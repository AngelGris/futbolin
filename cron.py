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

rounds = db_connection.query("SELECT `id`, `category_id` FROM `tournament_rounds` WHERE `datetime` BETWEEN " + str(start) + " AND " + str(end), 1000)

for round in rounds:
    # Play matches
    rounds_count += 1
    matches = db_connection.query('SELECT `id`, `local_id`, `visit_id` FROM `matches_rounds` WHERE `round_id` = ' + str(round['id']) + ' AND `match_id` IS NULL', 10)
    logfiles =  []
    for match in matches:
        matches_count += 1
        file_name = str(startTime) + '-' + str(match['local_id']) + '-' + str(match['visit_id']) + '.log';
        os.system(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'play.py') + ' ' + str(match['local_id']) + ' ' + str(match['visit_id']) + ' 3 -1 ' + file_name + ' ' + str(round['category_id']))
        db_connection.query('UPDATE `matches_rounds` SET match_id = (SELECT `id` FROM `matches` WHERE `logfile` = \'' + file_name + '\' LIMIT 1) WHERE `id` = ' + str(match['id']))
        logfiles.append(file_name)

    # Update points and goals
    matches = db_connection.query('SELECT `local_id`, `local_goals`, `visit_id`, `visit_goals` FROM `matches` WHERE `logfile` IN (\'' + '\', \''.join(logfiles) + '\') LIMIT 10', 10)
    for match in matches:
        results = [[0, 0, 0], [0, 0, 0]]
        if (match['local_goals'] > match['visit_goals']):
            results[0][0] = 1
            results[1][2] = 1
        elif (match['local_goals'] < match['visit_goals']):
            results[0][2] = 1
            results[1][0] = 1
        else:
            results[0][1] = 1
            results[1][1] = 1

        db_connection.query('UPDATE `tournament_positions` SET `points` = `points` + ' + str((results[0][0] * 3) + results[0][1]) + ', `played` = `played` + 1, `won` = `won` + ' + str(results[0][0]) + ', `tied` = `tied` + ' + str(results[0][1]) + ', `lost` = `lost` + ' + str(results[0][2]) + ', `goals_favor` = `goals_favor` + ' + str(match['local_goals']) + ', `goals_against` = `goals_against` + ' + str(match['visit_goals']) + ', `goals_difference` = `goals_difference` + ' + str(match['local_goals'] - match['visit_goals']) + ' WHERE `category_id` = ' + str(round['category_id']) + ' AND `team_id` = ' + str(match['local_id']) + ' LIMIT 1')
        db_connection.query('UPDATE `tournament_positions` SET `points` = `points` + ' + str((results[1][0] * 3) + results[1][1]) + ', `played` = `played` + 1, `won` = `won` + ' + str(results[1][0]) + ', `tied` = `tied` + ' + str(results[1][1]) + ', `lost` = `lost` + ' + str(results[1][2]) + ', `goals_favor` = `goals_favor` + ' + str(match['visit_goals']) + ', `goals_against` = `goals_against` + ' + str(match['local_goals']) + ', `goals_difference` = `goals_difference` + ' + str(match['visit_goals'] - match['local_goals']) + ' WHERE `category_id` = ' + str(round['category_id']) + ' AND `team_id` = ' + str(match['visit_id']) + ' LIMIT 1')

    # Update positions
    teams = db_connection.query('SELECT `team_id` FROM `tournament_positions` WHERE `category_id` = ' + str(round['category_id']) + ' ORDER BY `points` DESC, `goals_difference` DESC, `goals_favor` DESC LIMIT 20;', 20);
    position = 0
    for team in teams:
        position += 1
        db_connection.query('UPDATE `tournament_positions` SET `position` = ' + str(position) + ' WHERE `category_id` = ' + str(round['category_id']) + ' AND `team_id` = ' + str(team['team_id']) + ' LIMIT 1;')

print()
print(str(matches_count) + ' matches played in ' + str(rounds_count) + ' rounds')
print('Total time: ' + str(int(time.time()) - startTime) + 's')