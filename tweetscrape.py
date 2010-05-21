from datetime import datetime
import sys, getopt
import tweepy, sqlite3

help_message = """
Usage: python movietwitter.py [OPTION]... COMMAND [ARGUMENTS]...

Standalone options:
  -h, --help               Print this help information

Other options:
  -d, --database=FILE      Use Sqlite3 database FILE

Commands:
  list                     List current topics and queries (with id numbers)
  add TOPIC QUERY          Add a new topic and query (checks for duplicates)
  remove ID | all          Removes query by its database id or all queries
  activate ID              Activates topic by its id
  deactivate ID            Deactivates topic by its id

  Commands that take an id number may also take a comma-delimited list of id numbers.
"""

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

class DBConnection:
    """
    Connects to the sqlite3 database file in name.
    """
    def __init__(self, name):
        self.connection = sqlite3.connect(name)
        self.cursor = self.connection.cursor()

def main(argv=None):
    """
    Main program. Can be run independently if given an argv-style list.
    
    >>> main(['', 'remove', 'all'])
    0
    >>> main(['', 'add', 'A Topic', 'a query'])
    0
    >>> main(['', 'add', 'A Topic'])
    1
    >>> main(['', 'list'])
       ID                          Topic                          Query    Active?
        1                        A Topic                        a query          1
    0
    """
    if argv is None:
        argv = sys.argv
    # Configure arguments and possible commands
    largs = [
        'help',
        'database=',
    ]
    sargs = 'hd:'
    commands = [
        'list',
        'add',
        'remove',
        'activate',
        'deactivate',
    ]
    # Parsing command line options
    try:
        try:
            opts, args = getopt.getopt(argv[1:], sargs, largs)
        except getopt.error, msg:
             raise Usage(msg)
        # setup default settings
        database = None
        # process options
        for o, a in opts:
            if o in ('--help', '-h'):
                print >>sys.stderr, help_message
                return 0
            elif o in ('--database', '-d'):
                if a:
                    database = a
                else:
                    raise Usage('Missing database name.')
            else:
                raise Usage('Invalid option: %s.' % o)
        # process arguments (commands)
        command_name = None
        command_args = None
        if args:
            if args[0] in commands:
                # Got a valid command
                command_name = args[0]
                command_args = args[1:]
                # Check syntax
                if command_name == 'list':
                    if command_args:
                        raise Usage('Command takes no arguments.')
                elif command_name == 'add':
                    if len(command_args) != 2:
                        raise Usage('Command requires two arguments.')
                elif command_name == 'remove':
                    if len(command_args) != 1:
                        raise Usage('Command requires one argument.')
                elif command_name in ('activate', 'deactivate'):
                    if len(command_args) != 1:
                        raise Usage('Command requires one argument.')
            else:
                raise Usage('Invalid command.')
    except Usage, err:
        print >>sys.stderr, 'Error:', err.msg
        print >>sys.stderr, "For help use --help."
        return 1

    # Get the database filename from the config file
    #TODO: config file interface
    if database is None:
        database = 'ts.db'

    # Establish database connection
    db = DBConnection(database)
    
    # Load list of searches... (id, title, query, isactive)
    db.cursor.execute("""SELECT id,topic,query,isactive FROM topics;""")
    searches = [(str(r[0]), r[1], r[2], r[3]) for r in db.cursor.fetchall()]
    
    # Process commands
    if command_name == 'list':
        print '%5s %30s %30s %10s' % ('ID', 'Topic', 'Query', 'Active?')
        if searches:
            for s in searches:
                print '%5s %30s %30s %10s' % s
        else:
            print 'No results to display.'
    elif command_name == 'add':
        for s in searches:
            if s[1] == command_args[0] and s[2] == command_args[1]:
                print >>sys.stderr, 'Topic/Query already exists, ID=%s' % s[0]
                return 1
        # Fell through, means we didn't find it already so we add it
        db.cursor.execute("""INSERT INTO topics (
            topic,
            query,
            isactive
        ) VALUES (?, ?, ?);""", (
            command_args[0],
            command_args[1],
            '1'
        ))
    elif command_name == 'remove':
        num = command_args[0]
        if num == 'all':
            db.cursor.execute("""DELETE FROM topics;""")
            print >>sys.stderr, 'Removed all topics/queries.'
        else:
            # Drop by ID number now
            ids = num.split(',')
            for i in ids:
                found = False
                for s in searches:
                    if s[0] == i:
                        found = True
                        db.cursor.execute("""DELETE FROM topics WHERE id=?""",
                            (i,)
                        )
                        print >>sys.stderr, 'Remove successful, ID=%s' % i
                        break
                if not found:
                    print >>sys.stderr, 'Remove failed, not found, ID=%s' % i
    elif command_name == 'activate':
        pass
    elif command_name == 'deactivate':
        pass
    elif command_name is None:
        # No command was given, run normal twitter grab
        # Get date to use for this run
        current_date = datetime.now()
        # Iterate queries and run
        for s in searches:
            topic = s[1]
            query = s[2]
            # Get largest id for this search, start new search from there
            db.cursor.execute("""SELECT max(tweetid) FROM tweets WHERE search=?;""",
                (query,)
            )
            max_id = db.cursor.fetchone()[0]
            # Submit query to twitter api
            results = tweepy.api.search(q=query, rpp=100, since_id=max_id, result_type='recent')
            # Add results to the database
            for result in results:
                # Output message for logging
                print >>sys.stderr, 'Inserting row: %s %s' % (query, result.id)
                # Query to insert tweet into DB
                db.cursor.execute("""INSERT INTO tweets (
                    tweetid, 
                    tweetdate, 
                    user, 
                    text, 
                    topic, 
                    query, 
                    fetchdate
                ) VALUES (?, ?, ?, ?, ?, ?, ?);""", (
                    result.id,
                    str(result.created_at),
                    result.from_user,
                    result.text,
                    topic,
                    query,
                    str(current_date),
                ))
    # Commit changes to the database
    db.connection.commit()
    # Close database connection
    db.cursor.close()
    # All done!
    return 0

if __name__ == "__main__":
    sys.exit(main())
