#!/usr/bin/python3

# Imports
import classes.mysql as mysql
import time
import datetime
import os

startTime = int(time.time())

print('Starting Cron')

# DB connection
db_connection = mysql.Mysql()

start = startTime - (startTime % 86400)
end = start + 86399
rounds_count = 0
matches_count = 0

rounds = db_connection.query("SELECT `id` FROM `tournament_rounds` WHERE `datetime` BETWEEN " + str(start) + " AND " + str(end), 1000)

for round in rounds:
    rounds_count += 1
    matches = db_connection.query('SELECT `id`, `local_id`, `visit_id` FROM `matches_rounds` WHERE `round_id` = ' + str(round['id']) + ' AND `match_id` IS NULL', 10)
    for match in matches:
        matches_count += 1
        file_name = str(startTime) + '-' + str(match['local_id']) + '-' + str(match['visit_id']) + '.log';
        os.system(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'play.py') + ' ' + str(match['local_id']) + ' ' + str(match['visit_id']) + ' 3 -1 ' + file_name)
        db_connection.query('UPDATE `matches_rounds` SET match_id = (SELECT `id` FROM `matches` WHERE `logfile` = \'' + file_name + '\' LIMIT 1) WHERE `id` = ' + str(match['id']))

    # UPDATE POSITIONS

print()
print(str(matches_count) + ' matches played in ' + str(rounds_count) + ' rounds')
print('Total time: ' + str(int(time.time()) - startTime) + 's')