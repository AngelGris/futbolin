#!/usr/bin/python3

# Imports
import sys
from classes.handler import Handler

# Arguments list:
# 0 = script name
# 1 = home team ID
# 2 = visit team ID
# 3 = debug level
# 4 = output file name (optional)
# 5 = tournament category ID (optional)

if len(sys.argv) < 4:
    print('Missing arguments (Home team ID, Visit team ID, Match type, Debug level, [Output file, Category ID])')
    exit()

args = []
for i in range(4):
    try:
        args.append(int(sys.argv[i + 1]))
    except ValueError:
        if (i == 0):
            print('Home team ID must be an integer')
        elif (i == 1):
            print('Visit team ID must be an integer')
        elif (i == 2):
            print('Match type must be an integer')
        elif (i == 3):
            print('Debug level must be an integer')
        exit()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

try:
    output_file = sys.argv[5]
except:
    output_file = ''

try:
    category_id = sys.argv[6]
except:
    category_id = 0

games_count = 0
games_closed = 0
goals_total = [0, 0]
shots_total = [[0,0],[0,0]]
substitutions_total = 0
fouls_total = 0
cards_total = [0, 0]
injuries_total = 0
results = [0, 0, 0]

while True:
    statistics = Handler.execute(args[0], args[1], args[2], args[3], output_file, category_id)

    goals = statistics.getGoals()
    if (goals[0] > goals[1]):
        results[0] += 1
    elif (goals[1] > goals[0]):
        results[2] += 1
    else:
        results[1] += 1

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

    injuries = statistics.getInjuries()
    injuries_total += injuries[0] + injuries[1]

    games_count += 1
    goals_total[0] += goals[0]
    goals_total[1] += goals[1]
    if goals[0] == 0 and goals[1] == 0:
        games_closed += 1

    print('Partidos:', games_count)
    print('Resultados:', results)
    print('Goles por equipo:', goals_total[0], '(', '{:05.2f}'.format(goals_total[0] / games_count), ') -', goals_total[1], '(', '{:05.2f}'.format(goals_total[1] / games_count), ')')
    print('Goles por partido:', '{:05.2f}'.format((goals_total[0] + goals_total[1]) / games_count))
    print('Partidos sin goles:', games_closed)
    print('Disparos por equipo:', str(shots_total[0][0]), '(', str(shots_total[0][1]), ') -', str(shots_total[1][0]), '(', str(shots_total[1][1]), ')')
    print('Disparos total:', str(total_shots[0]), '(', str(total_shots[1]), ')')
    print('Disparos por partido:', '{:05.2f}'.format(total_shots[0] / games_count), '(', '{:05.2f}'.format(total_shots[1] / games_count), ')')
    print('Cambios por partido:', '{:05.2f}'.format(substitutions_total / games_count))
    print('Faltas por partido:', '{:05.2f}'.format(fouls_total / games_count))
    print('Tarjetas por partidos', '{:05.2f}'.format(cards_total[0] / games_count) + ' / ' + '{:05.2f}'.format(cards_total[1] / games_count))
    print('Lesiones por partido:', '{:05.2f}'.format(injuries_total / games_count))