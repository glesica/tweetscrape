create table tweets (id INTEGER PRIMARY KEY, tweetid TEXT, tweetdate TEXT, user TEXT, text TEXT, topic TEXT, query TEXT, fetchdate TEXT);
create table topics (id INTEGER PRIMARY KEY, topic TEXT, query TEXT, isactive BOOLEAN);
create table config (id INTEGER PRIMARY KEY, key TEXT, value TEXT);
