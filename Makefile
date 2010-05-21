all:
	@echo "Targets available:"
	@echo "\tsetup\tsets up a blank database called ts.db"
	@echo "\ttest\truns doctests, redirects stderr to /dev/null"

setup:
	touch ts.db
	sqlite3 ts.db < setup.sql

test:
	python -m doctest -v tweetscrape.py 2> /dev/null
