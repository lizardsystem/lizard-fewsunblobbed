Usage of lizard-fewsunblobbed
=============================


Making a sqlite database with data
----------------------------------

How to make a sqlite fews-unblobbed database::

    # sqlite3 filename.db
    SQLite version 3.6.16
    Enter ".help" for instructions
    Enter SQL statements terminated with a ";"
    sqlite> .read import.sql
    SQL error near line 11: no such table: filter
    SQL error near line 12: no such table: location
    SQL error near line 13: no such table: parameter
    SQL error near line 14: no such table: timeserie
    SQL error near line 15: no such table: timeseriedata
    sqlite>

(Finished! - it gives the errors because if you have existing tables,
the script will remove the tables first)


Deploying lizard-fewsunblobbed
------------------------------

Add crontab job to your deploy.cfg to run "bin/django
fews_unblobbed_cache" every 8 hours. This way visitors of the page
will always get its filters from the cache (= huge user experience
boost).

deploy.cfg::

    [fews-unblobbed-cronjob]
    recipe = z3c.recipe.usercrontab
    times = * */8 * * *
    command = ${buildout:bin-directory}/django fews_unblobbed_cache
