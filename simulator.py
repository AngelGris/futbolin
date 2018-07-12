#!/usr/bin/python3

# Imports
import random
import sys
import classes.mysql as mysql
import classes.simulator as Simulator

# Arguments list:
# 0 = script name
# 1 = match type
# 2 = debug level
# 3 = output file name (optional)
# 4 = tournament category ID (optional)

if len(sys.argv) < 2:
    print('Missing arguments (Match type, Debug level, [Output file, Category ID])')
    exit()

args = []
for i in range(2):
    try:
        args.append(int(sys.argv[i + 1]))
    except ValueError:
        if (i == 0):
            print('Match type must be an integer')
        elif (i == 1):
            print('Debug level must be an integer')
        exit()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

try:
    output_file = sys.argv[3]
except:
    output_file = ''

try:
    category_id = sys.argv[4]
except:
    category_id = 0

games_count = 0
games_closed = 0
goals_total = [0, 0]
shots_total = [[0,0],[0,0]]
substitutions_total = 0
fouls_total = 0
cards_total = [0, 0]
goalkeepers_cards_total = [0, 0]
injuries_total = 0
goalkeepers_injuries_total = 0
penalties_total = [0, 0, 0]
results = [0, 0, 0]

db_connection = mysql.Mysql()
teams = db_connection.query('SELECT `id` FROM `teams` WHERE `user_id` > 1 AND `playable` = 1', 1000)

while True:
    local = random.choice(teams)
    visit = random.choice(teams)
    sim = Simulator.Simulator(local['id'], visit['id'], args[0], args[1], output_file, category_id)
    statistics = sim.simulate()

    goals = statistics.getGoals()
    if (goals[0] > goals[1]):
        results[0] += 1
    elif (goals[1] > goals[0]):
        results[2] += 1
    else:
        results[1] += 1

    penalties = statistics.getPenalties()
    penalties_total[0] += penalties[0]
    penalties_total[1] += penalties[1]
    penalties_total[2] += penalties[2]

    shots = statistics.getShots()
    shots_total[0][0] += shots[0][0]
    shots_total[0][1] += shots[0][1]
    shots_total[1][0] += shots[1][0]
    shots_total[1][1] += shots[1][1]
    total_shots = [shots_total[0][0] + shots_total[1][0], shots_total[0][1] + shots_total[1][1]]

    substitutions = statistics.getSubstitutions()
    substitutions_total += substitutions[0] + substitutions[1]

    fouls = statistics.getFouls()
    fouls_total += fouls[0] + fouls[1]

    cards = statistics.getCards()
    cards_total[0] += cards[0][0] + cards[1][0]
    cards_total[1] += cards[0][1] + cards[1][1]

    goalkeepers_cards = statistics.getGoalkeepersCards()
    goalkeepers_cards_total[0] += goalkeepers_cards[0]
    goalkeepers_cards_total[1] += goalkeepers_cards[1]

    injuries = statistics.getInjuries()
    injuries_total += injuries[0] + injuries[1]

    goalkeepers_injuries_total += statistics.getGoalkeepersInjuries()

    games_count += 1
    goals_total[0] += goals[0]
    goals_total[1] += goals[1]
    if goals[0] == 0 and goals[1] == 0:
        games_closed += 1

    print('Partidos:', games_count)
    print('Resultados:', results)
    print('Goles por equipo:', goals_total[0], '(', '{:05.2f}'.format(goals_total[0] / games_count), ') -', goals_total[1], '(', '{:05.2f}'.format(goals_total[1] / games_count), ')')
    print('Goles por partido:', '{:05.2f}'.format((goals_total[0] + goals_total[1]) / games_count))
    print('Penales por partido:', '{:05.2f}'.format(penalties_total[0] / games_count), '({:05.2f}%'.format(penalties_total[1] / penalties_total[0] * 100 if penalties_total[0] > 0 else 0), '-', '{:05.2f}%)'.format(penalties_total[2] / penalties_total[0] * 100 if penalties_total[0] else 0))
    print('Partidos sin goles:', games_closed)
    print('Disparos por equipo:', str(shots_total[0][0]), '(', str(shots_total[0][1]), ') -', str(shots_total[1][0]), '(', str(shots_total[1][1]), ')')
    print('Disparos total:', str(total_shots[0]), '(', str(total_shots[1]), ')')
    print('Disparos por partido:', '{:05.2f}'.format(total_shots[0] / games_count), '(', '{:05.2f}'.format(total_shots[1] / games_count), ')')
    print('Cambios por partido:', '{:05.2f}'.format(substitutions_total / games_count))
    print('Faltas por partido:', '{:05.2f}'.format(fouls_total / games_count))
    print('Tarjetas por partidos:', '{:05.2f}'.format(cards_total[0] / games_count) + ' / ' + '{:05.2f}'.format(cards_total[1] / games_count))
    print('Tarjetas a los arqueros:', '{:05.2f}'.format(goalkeepers_cards_total[0] / games_count), '/', '{:05.2f}'.format(goalkeepers_cards_total[1] / games_count))
    print('Lesiones por partido:', '{:05.2f}'.format(injuries_total / games_count))
    print('Arqueros lesionados por partido:', '{:05.2f}'.format(goalkeepers_injuries_total / games_count))