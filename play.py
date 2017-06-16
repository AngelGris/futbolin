#!/usr/bin/python3

# Imports
import random
import math
import classes.team as team
import classes.ball as bal
import classes.stats as stats
import classes.mysql as mysql
import sys
from classes.field import Field
from classes.helper import Helper

# Arguments list:
# 0 = script name
# 1 = home team ID
# 2 = visit team ID
# 3 = debug level
# 4 = output file name (optional)

if len(sys.argv) < 4:
    print('Missing arguments (Home team ID, Visit team ID, Match type, Debug level)')
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

# DB connection
db_connection = mysql.Mysql()

games_count = 0
games_closed = 0
goals_total = [0, 0]
shots_total = [[0,0],[0,0]]
results = [0, 0, 0]
time_step = 2.0
ball = bal.Ball([45.0, 60.0])
field_size = Field.getSize()
teams = [team.Team(args[0], field_size, db_connection), team.Team(args[1], field_size, db_connection)]

for i in range(1):
#while True:
    time_total = 2700
    time_half = 1
    play_type = 1
    statistics = stats.Stats(teams[0], teams[1], args[2], args[3], output_file)

    if (not teams[0].getEnabled() or not teams[1].getEnabled()):
        if (teams[0].getEnabled()):
            statistics.execSuspendMatch(0)
        elif (teams[1].getEnabled()):
            statistics.execSuspendMatch(1)
        else:
            statistics.execSuspendMatch(None)

        print('')
        print(statistics)
        print('')
        statistics.writeOutput(db_connection)
        exit()

    kickoff_team = random.randint(0,1)
    kickoff_team = 1
    while(time_half <= 2):
        print('*** COMIENZO ' + ('PRIMER' if time_half == 1 else 'SEGUNDO') + ' TIEMPO ***')
        teams[0].resetPositions()
        teams[1].resetPositions()
        ball.setPosition([45.0, 60.0])
        kickoff_player = teams[kickoff_team].getClosestPlayer(ball.getPosition())
        ball.setPlayer(teams[kickoff_team].getPlayer(kickoff_player[0]), False);
        teams[kickoff_team].setPlayerPosition(ball.getPlayer().getIndex(), ball.getPosition())
        while(statistics.getTime() <= time_total):
            time_update = 0
            possesion_team = ball.getTeam()
            possesion_player = ball.getPlayer().getIndex()
            rival_team = (possesion_team + 1) % 2
            #  0 = Regular play
            #  1 = Kick off
            #  2 = Run with the ball
            #  3 = Pass the ball
            #  4 = Shoot to the goal
            #  5 = Goal kick
            #  6 = Corner kick
            #  7 = Dribbling
            #  8 = Free kick
            if play_type == 1:
                # Kick off
                teams[0].resetPositions()
                teams[1].resetPositions()
                ball.setPlayer(None)
                ball.setPosition([45.0, 60.0])
                kickoff_player = teams[possesion_team].getClosestPlayer(ball.getPosition())
                possesion_player = kickoff_player[0]
                ball.setPlayer(teams[possesion_team].getPlayer(kickoff_player[0]), False);
                teams[possesion_team].setPlayerPosition(ball.getPlayer().getIndex(), ball.getPosition())

                pass_to = teams[possesion_team].getPass(possesion_player)
                ball.setPlayer(teams[possesion_team].getPlayer(pass_to))

                statistics.execKickoff(possesion_team, teams[possesion_team].getPlayer(possesion_player), teams[possesion_team].getPlayer(pass_to))
                play_type = 0
                time_update += statistics.increaseTime(time_step / 2)
            elif play_type == 2:
                # Run with the ball
                teams[possesion_team].getPlayer(possesion_player).updatePosition(1, time_step, True)

                statistics.execRun(possesion_team, teams[possesion_team].getPlayer(possesion_player))

                play_type = 0
                time_update += statistics.increaseTime(time_step)
            elif play_type == 3:
                # Pass the ball
                pass_to = teams[possesion_team].getPass(possesion_player, True)
                closest_rival = teams[rival_team].getClosestPlayer(teams[possesion_team].getPlayer(possesion_player).getPosition())
                probs = [teams[possesion_team].getPlayer(possesion_player).getPassing(), 0] # 0 = passing, 1 = interecption
                if closest_rival[1] > (closest_rival[2] * 2):
                    # Rival too far
                    probs[1] = 0
                elif closest_rival[1] > closest_rival[2]:
                    # Rival closer
                    probs[1] = int(teams[rival_team].getPlayer(closest_rival[0]).getDefending() * 0.5)
                else:
                    # Rival is here
                    probs[1] = teams[rival_team].getPlayer(closest_rival[0]).getDefending()

                total = probs[0] + probs[1]
                probs[0] = int(probs[0] * 100 / total)
                probs[1] = 100

                r = random.randint(0, 100)
                s = 0
                while(probs[s] < r):
                    s += 1

                if s == 0:
                    # Passing successfull
                    statistics.execPassing(possesion_team, teams[possesion_team].getPlayer(possesion_player), teams[possesion_team].getPlayer(pass_to))
                    ball.setPlayer(teams[possesion_team].getPlayer(pass_to))
                else:
                    # Pass intercepted
                    statistics.execInterception(rival_team, teams[possesion_team].getPlayer(possesion_player), teams[rival_team].getPlayer(closest_rival[0]))
                    ball.setPlayer(teams[rival_team].getPlayer(closest_rival[0]))

                play_type = 0
                time_update += statistics.increaseTime(time_step)
            elif play_type == 4:
                # Shoot to the goal
                r = random.randint(0, 100)
                if (r < teams[possesion_team].getPlayer(possesion_player).getPrecision(Field.getGoalPosition(rival_team))):
                    # Shoot on goal
                    statistics.execShootOnGoal(possesion_team, teams[possesion_team].getPlayer(possesion_player))
                    time_update += statistics.increaseTime(time_step)
                    probs = [teams[possesion_team].getPlayer(possesion_player).getPrecision(Field.getGoalPosition(rival_team)), teams[rival_team].getPlayer(0).getGoalKeeping()]
                    total = probs[0] + probs[1]
                    probs[0] = int(probs[0] * 100 / total)
                    probs[1] = 100

                    r = random.randint(0, 100)
                    if r < probs[0]:
                        # GOAL
                        statistics.execScore(possesion_team, teams[possesion_team].getPlayer(possesion_player))
                        ball.setPlayer(teams[rival_team].getPlayer(0))
                        time_update += statistics.increaseTime(time_step * 3)
                        play_type = 1
                    else:
                        # Goalkeeper defends
                        r = random.randint(0, 100)
                        if (r < teams[rival_team].getPlayer(0).getGoalKeeping()):
                            # Goalkeeper keeps the ball
                            statistics.execGoalkeeperDefence(rival_team, teams[rival_team].getPlayer(0))
                            ball.setPlayer(teams[rival_team].getPlayer(0))
                            play_type = 0
                        else:
                            # Corner kick
                            statistics.execGoalkeeperDefenceToCorner(rival_team, teams[rival_team].getPlayer(0))
                            ball.setPlayer(teams[possesion_team].getPlayerCorner())
                            play_type = 6
                        time_update += statistics.increaseTime(time_step)
                else:
                    # Shoot away
                    statistics.execShootAway(possesion_team, teams[possesion_team].getPlayer(possesion_player))
                    ball.setPlayer(teams[rival_team].getPlayer(0))
                    time_update += statistics.increaseTime(time_step)
                    play_type = 5
            elif play_type == 5:
                # Goal kick
                teams[0].resetPositions(0.5)
                teams[1].resetPositions(0.5)

                if ball.getTeam() == 0:
                    ball.setPosition([field_size[0] / 2, 5.5])
                else:
                    ball.setPosition([field_size[0] / 2, field_size[1] - 5.5])

                time_update += statistics.increaseTime(time_step)
                statistics.execGoalKick(ball.getTeam(), teams[ball.getTeam()].getPlayer(0))
                time_update += statistics.increaseTime(time_step)
                play_type = 3
                time_update = time_step / 2
            elif play_type == 6:
                # Corner kick
                time_update += statistics.increaseTime(time_step * 2)
                statistics.execCornerKick(possesion_team, teams[possesion_team].getPlayer(possesion_player))
                time_update += statistics.increaseTime(time_step / 2)
                r = random.randint(0, 100)
                if (r < 50):
                    # Left corner
                    if (possesion_team == 1):
                        ball.setPosition([0, field_size[1]])
                    else:
                        ball.setPosition([field_size[0], 0])
                else:
                    # Right corner
                    if (possesion_team == 1):
                        ball.setPosition([field_size[0], field_size[1]])
                    else:
                        ball.setPosition([0, 0])

                header_attacking = teams[possesion_team].getHeadingPlayer(ball)
                header_defending = teams[rival_team].getHeadingPlayer(ball, False)
                r = random.randint(0, header_attacking[1] + header_defending[1])
                if (r < header_attacking[1]):
                    # Attacking header
                    r = random.randint(0, 100)
                    if (r < header_attacking[2]):
                        # Heading on target
                        statistics.execHeaderOnTarget(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                        r = random.randint(0, header_attacking[2] + teams[rival_team].getPlayer(0).getGoalKeeping())

                        if r < header_attacking[2]:
                            # GOAL
                            statistics.execScore(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                            ball.setPlayer(teams[rival_team].getPlayer(0))
                            time_update += statistics.increaseTime(time_step * 3)
                            play_type = 1
                        else:
                            # Goalkeeper defends
                            r = random.randint(0, 100)
                            if (r < teams[rival_team].getPlayer(0).getGoalKeeping()):
                                # Goalkeeper keeps the ball
                                statistics.execGoalkeeperDefence(rival_team, teams[rival_team].getPlayer(0))
                                ball.setPlayer(teams[rival_team].getPlayer(0))
                                play_type = 0
                            else:
                                # Corner kick
                                statistics.execGoalkeeperDefenceToCorner(rival_team, teams[rival_team].getPlayer(0))
                                ball.setPlayer(teams[possesion_team].getPlayerCorner())
                                play_type = 6

                            time_update += statistics.increaseTime(time_step)
                    else:
                        # Heading out
                        statistics.execHeaderAway(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                        ball.setPlayer(teams[rival_team].getPlayer(0))
                        time_update += statistics.increaseTime(time_step)
                        play_type = 5
                else:
                    # Defending header
                    if (header_defending[0] == 0):
                        # Goalkeeper takes the ball
                        statistics.execGoalkeeperCutsCrossing(rival_team, teams[rival_team].getPlayer(0))
                        ball.setPlayer(teams[rival_team].getPlayer(0))
                        time_update += statistics.increaseTime(time_step * 2)
                        play_type = 5
                    else:
                        # Defender heads away
                        statistics.execDefendingHeader(rival_team, teams[rival_team].getPlayer(header_defending[0]))
                        ball.setPlayer(teams[rival_team].getPlayer(header_defending[0]))
                        time_update += statistics.increaseTime(time_step)
                        play_type = 3
            elif play_type == 7:
                # Dribbling
                closest_rival = teams[rival_team].getClosestPlayer(teams[possesion_team].getPlayer(possesion_player).getPosition())
                probs = [0, 0, 0] # 0 = dribbling, 1 = tackling, 2 = foul
                probs[0] = teams[possesion_team].getPlayer(possesion_player).getDribbling()
                probs[1] = int(math.fabs(math.pow(teams[rival_team].getPlayer(closest_rival[0]).getTackling(), 2) / 100))
                probs[2] = teams[rival_team].getPlayer(closest_rival[0]).getTackling() - probs[1]

                probs[1] += probs[0]
                probs[2] += probs[1]

                r = random.randint(0, probs[2])

                if r < probs[0]:
                    # Dribbling successed
                    statistics.execDribbling(possesion_team, teams[possesion_team].getPlayer(possesion_player), teams[rival_team].getPlayer(closest_rival[0]))
                    play_type = 0
                elif r < probs[1]:
                    # Tackling successed
                    statistics.execTackling(rival_team, teams[possesion_team].getPlayer(possesion_player), teams[rival_team].getPlayer(closest_rival[0]))
                    ball.setPlayer(teams[rival_team].getPlayer(closest_rival[0]))
                    play_type = 0
                else:
                    # Foul
                    statistics.execFoul(possesion_team, teams[possesion_team].getPlayer(possesion_player), teams[rival_team].getPlayer(closest_rival[0]))
                    play_type = 8

                time_update += statistics.increaseTime(time_step)
            elif play_type == 8:
                # Free kick
                teams[possesion_team].resetPositions(1)
                teams[rival_team].resetPositions(0)
                shooter = teams[possesion_team].getClosestPlayer(ball.getPosition())
                ball.setPlayer(teams[possesion_team].getPlayer(shooter[0]))
                goal_distance = Helper.calculateDistance(ball.getPlayer().getPosition(), Field.getGoalPosition(rival_team))

                probs = [0, 0, 0] # 0 = passing, 1 = centering, 2 = shoot on goal
                probs[0] = teams[possesion_team].getPlayer(shooter[0]).getPassing()

                centering = int(teams[possesion_team].getPlayer(shooter[0]).getPassing() * teams[possesion_team].getPlayer(shooter[0]).getPrecision(Field.getGoalPosition(rival_team)) / 100)
                if centering > goal_distance:
                    probs[1] = int(math.pow((centering - goal_distance) / centering, 2) * 100)

                shooting = int(teams[possesion_team].getPlayer(shooter[0]).getShootingStrength() * teams[possesion_team].getPlayer(shooter[0]).getPrecision(Field.getGoalPosition(rival_team)) / 100)
                if shooting > goal_distance:
                    probs[2] = int(math.pow((shooting - goal_distance) / shooting, 2) * 100)

                probs[1] += probs[0]
                probs[2] += probs[1]

                r = random.randint(0, probs[2])
                if r <= probs[0]:
                    # Passing
                    play_type = 3
                elif r <= probs[1]:
                    # Centering
                    header_attacking = teams[possesion_team].getHeadingPlayer(ball)
                    header_defending = teams[possesion_team].getHeadingPlayer(ball, False)
                    r = random.randint(0, header_attacking[1] + header_defending[1])
                    if (r < header_attacking[1]):
                        # Attacking header
                        r = random.randint(0, 100)
                        if (r < header_attacking[2]):
                            # Heading on target
                            statistics.execHeaderOnTarget(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                            r = random.randint(0, header_attacking[2] + teams[rival_team].getPlayer(0).getGoalKeeping())

                            if r < header_attacking[2]:
                                # GOAL
                                statistics.execScore(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                                ball.setPlayer(teams[rival_team].getPlayer(0))
                                time_update += statistics.increaseTime(time_step * 3)
                                play_type = 1
                            else:
                                # Goalkeeper defends
                                r = random.randint(0, 100)
                                if (r < teams[rival_team].getPlayer(0).getGoalKeeping()):
                                    # Goalkeeper keeps the ball
                                    statistics.execGoalkeeperDefence(rival_team, teams[rival_team].getPlayer(0))
                                    ball.setPlayer(teams[rival_team].getPlayer(0))
                                    play_type = 0
                                else:
                                    # Corner kick
                                    statistics.execGoalkeeperDefenceToCorner(rival_team, teams[rival_team].getPlayer(0))
                                    ball.setPlayer(teams[possesion_team].getPlayerCorner())
                                    play_type = 6

                                time_update += statistics.increaseTime(time_step)
                        else:
                            # Heading out
                            statistics.execHeaderAway(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                            ball.setPlayer(teams[rival_team].getPlayer(0))
                            time_update += statistics.increaseTime(time_step)
                            play_type = 5
                    else:
                        # Defending header
                        if (header_defending[0] == 0):
                            # Goalkeeper takes the ball
                            statistics.execGoalkeeperCutsCrossing(rival_team, teams[rival_team].getPlayer(0))
                            ball.setPlayer(teams[rival_team].getPlayer(0))
                            time_update += statistics.increaseTime(time_step * 2)
                            play_type = 5
                        else:
                            # Defender heads away
                            statistics.execDefendingHeader(rival_team, teams[rival_team].getPlayer(header_defending[0]))
                            ball.setPlayer(teams[rival_team].getPlayer(header_defending[0]))
                            time_update += statistics.increaseTime(time_step)
                            play_type = 3
                else:
                    # Shoot on goal
                    r = random.randint(0, 100)
                    if (r <= shooting):
                        # Shoot on goal
                        statistics.execFreekickOnGoal(possesion_team, teams[possesion_team].getPlayer(shooter[0]))
                        time_update += statistics.increaseTime(time_step)
                        probs = [teams[possesion_team].getPlayer(shooter[0]).getPrecision(Field.getGoalPosition(rival_team)), teams[rival_team].getPlayer(0).getGoalKeeping()]
                        total = probs[0] + probs[1]
                        probs[0] = int(probs[0] * 100 / total)
                        probs[1] = 100

                        r = random.randint(0, 100)
                        if r < probs[0]:
                            # GOAL
                            statistics.execFreekickScore(possesion_team, teams[possesion_team].getPlayer(possesion_player))
                            ball.setPlayer(teams[rival_team].getPlayer(0))
                            time_update += statistics.increaseTime(time_step * 3)
                            play_type = 1
                        else:
                            # Goalkeeper defends
                            r = random.randint(0, 100)
                            if (r < teams[rival_team].getPlayer(0).getGoalKeeping()):
                                # Goalkeeper keeps the ball
                                statistics.execGoalkeeperDefence(rival_team, teams[rival_team].getPlayer(0))
                                ball.setPlayer(teams[rival_team].getPlayer(0))
                                play_type = 0
                            else:
                                # Corner kick
                                statistics.execGoalkeeperDefenceToCorner(rival_team, teams[rival_team].getPlayer(0))
                                ball.setPlayer(teams[possesion_team].getPlayerCorner())
                                play_type = 6
                            time_update += statistics.increaseTime(time_step)
                    else:
                        # Shoot away
                        statistics.execShootAway(possesion_team, teams[possesion_team].getPlayer(possesion_player))
                        ball.setPlayer(teams[rival_team].getPlayer(0))
                        time_update += statistics.increaseTime(time_step)
                        play_type = 5

                time_update += statistics.increaseTime(time_step)
            else:
                # Regular play
                closest_friend = teams[possesion_team].getClosestPlayer(teams[possesion_team].getPlayer(possesion_player).getPosition(), possesion_player)
                closest_rival = teams[rival_team].getClosestPlayer(teams[possesion_team].getPlayer(possesion_player).getPosition())
                goal_distance = Helper.calculateDistance(ball.getPlayer().getPosition(), Field.getGoalPosition(rival_team))
                play_type = teams[possesion_team].getNextPlay(possesion_player, closest_friend, closest_rival, goal_distance)
                time_update += statistics.increaseTime(time_step / 2)

            teams[0].updatePositions(field_size, ball, time_update)
            teams[1].updatePositions(field_size, ball, time_update)
        print('*** FINAL ' + ('PRIMER' if time_half == 1 else 'SEGUNDO') + ' TIEMPO ***')
        time_half += 1
        time_total *= 2
        kickoff_team = (kickoff_team + 1) % 2
        play_type = 1

    print('')
    print(statistics)
    print('')

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

    if (output_file != ''):
        statistics.writeOutput(db_connection)

    # If tournament match
    if (args[2] == 3):
        # Increase player's experience
        if teams[0].getId() > 26:
            for player in teams[0].getPlayersList():
                player.saveExperience(db_connection)

        if teams[1].getId() > 26:
            for player in teams[1].getPlayersList():
                player.saveExperience(db_connection)