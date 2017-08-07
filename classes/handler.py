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

class Handler:
    def execute(local_id, visit_id, match_type, debug_level, output_file = '', categoryId = 0):
        # DB connection
        db_connection = mysql.Mysql()

        time_step = 2.0
        ball = bal.Ball([45.0, 60.0])
        field_size = Field.getSize()
        local_max_stamina = 1
        visit_max_stamina = 1
        if (match_type == 3):
            local_stamina = db_connection.query('SELECT AVG(`stamina`) AS `stamina` FROM `players` WHERE `team_id` = ' + str(local_id), 1)
            visit_stamina = db_connection.query('SELECT AVG(`stamina`) AS `stamina` FROM `players` WHERE `team_id` = ' + str(visit_id), 1)
            if local_stamina['stamina'] > visit_stamina['stamina']:
                visit_max_stamina = visit_stamina['stamina'] / local_stamina['stamina']
            elif visit_stamina['stamina'] > local_stamina['stamina']:
                local_max_stamina = local_stamina['stamina'] / visit_stamina['stamina']
            del local_stamina
            del visit_stamina

        teams = [team.Team(local_id, field_size, match_type, local_max_stamina, db_connection, True), team.Team(visit_id, field_size, match_type, visit_max_stamina, db_connection)]

        time_total = 2700
        time_half = 1
        play_type = 1
        statistics = stats.Stats(teams[0], teams[1], match_type, debug_level, output_file, categoryId)

        # Suspend Match if one of the teams in not enabled to play
        if (not teams[0].getEnabled() or not teams[1].getEnabled()):
            if (teams[0].getEnabled()):
                statistics.execSuspendMatch(0)
            elif (teams[1].getEnabled()):
                statistics.execSuspendMatch(1)
            else:
                statistics.execSuspendMatch(None)

            if (output_file != ''):
                statistics.writeOutput(db_connection)

            exit()

        # Play the game!
        kickoff_team = random.randint(0,1)
        while(time_half <= 2):
            print('*** COMIENZO ' + ('PRIMER' if time_half == 1 else 'SEGUNDO') + ' TIEMPO ***')
            # Substitutions
            if time_half == 2:
                teams[0].checkSubstitutions(statistics)
                teams[1].checkSubstitutions(statistics)

            teams[0].resetPositionings()
            teams[1].resetPositionings()
            ball.setPositioning([45.0, 60.0])
            kickoff_player = teams[kickoff_team].getClosestPlayer(ball.getPositioning())
            ball.setPlayer(teams[kickoff_team].getPlayer(kickoff_player[0]), False);
            teams[kickoff_team].setPlayerPositioning(ball.getPlayer().getIndex(), ball.getPositioning())

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
                    teams[0].resetPositionings()
                    teams[1].resetPositionings()
                    ball.setPlayer(None)
                    ball.setPositioning([45.0, 60.0])
                    kickoff_player = teams[possesion_team].getClosestPlayer(ball.getPositioning())
                    possesion_player = kickoff_player[0]
                    ball.setPlayer(teams[possesion_team].getPlayer(kickoff_player[0]), False);
                    teams[possesion_team].setPlayerPositioning(ball.getPlayer().getIndex(), ball.getPositioning())

                    pass_to = teams[possesion_team].getPass(possesion_player)
                    ball.setPlayer(teams[possesion_team].getPlayer(pass_to))

                    statistics.execKickoff(possesion_team, teams[possesion_team].getPlayer(possesion_player), teams[possesion_team].getPlayer(pass_to))
                    play_type = 0
                    time_update += statistics.increaseTime(time_step / 2)
                elif play_type == 2:
                    # Run with the ball
                    teams[possesion_team].getPlayer(possesion_player).updatePositioning(1, time_step, True)

                    statistics.execRun(possesion_team, teams[possesion_team].getPlayer(possesion_player))

                    play_type = 0
                    time_update += statistics.increaseTime(time_step)
                elif play_type == 3:
                    # Pass the ball
                    pass_to = teams[possesion_team].getPass(possesion_player, True)
                    closest_rival = teams[rival_team].getClosestPlayer(teams[possesion_team].getPlayer(possesion_player).getPositioning())
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
                    if (r < teams[possesion_team].getPlayer(possesion_player).getPrecision(Field.getGoalPositioning(rival_team))):
                        # Shoot on goal
                        statistics.execShootOnGoal(possesion_team, teams[possesion_team].getPlayer(possesion_player))
                        time_update += statistics.increaseTime(time_step)
                        probs = [teams[possesion_team].getPlayer(possesion_player).getPrecision(Field.getGoalPositioning(rival_team)), teams[rival_team].getPlayerAtPos(0).getGoalKeeping()]
                        total = probs[0] + probs[1]
                        probs[0] = int(probs[0] * 100 / total)
                        probs[1] = 100

                        r = random.randint(0, 100)
                        if r < probs[0]:
                            # GOAL
                            statistics.execScore(possesion_team, teams[possesion_team].getPlayer(possesion_player))
                            ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                            time_update += statistics.increaseTime(time_step * 3)
                            play_type = 1
                        else:
                            # Goalkeeper defends
                            r = random.randint(0, 100)
                            if (r < teams[rival_team].getPlayerAtPos(0).getGoalKeeping()):
                                # Goalkeeper keeps the ball
                                statistics.execGoalkeeperDefence(rival_team, teams[rival_team].getPlayerAtPos(0))
                                ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                                play_type = 0
                            else:
                                # Corner kick
                                statistics.execGoalkeeperDefenceToCorner(rival_team, teams[rival_team].getPlayerAtPos(0))
                                ball.setPlayer(teams[possesion_team].getPlayerCorner())
                                play_type = 6
                            time_update += statistics.increaseTime(time_step)
                    else:
                        # Shoot away
                        statistics.execShootAway(possesion_team, teams[possesion_team].getPlayer(possesion_player))
                        ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                        time_update += statistics.increaseTime(time_step)
                        play_type = 5
                elif play_type == 5:
                    # Substitutions
                    if time_half == 2:
                        teams[0].checkSubstitutions(statistics)
                        teams[1].checkSubstitutions(statistics)

                        ball.setPlayer(teams[rival_team].getPlayerAtPos(0))

                    # Goal kick
                    teams[0].resetPositionings(0.5)
                    teams[1].resetPositionings(0.5)

                    if ball.getTeam() == 0:
                        ball.setPositioning([field_size[0] / 2, 5.5])
                    else:
                        ball.setPositioning([field_size[0] / 2, field_size[1] - 5.5])

                    time_update += statistics.increaseTime(time_step)
                    statistics.execGoalKick(ball.getTeam(), teams[ball.getTeam()].getPlayerAtPos(0))
                    time_update += statistics.increaseTime(time_step)
                    play_type = 3
                    time_update = time_step / 2
                elif play_type == 6:
                    # Substitutions
                    if time_half == 2:
                        teams[0].checkSubstitutions(statistics)
                        teams[1].checkSubstitutions(statistics)

                    # Corner kick
                    time_update += statistics.increaseTime(time_step * 2)
                    r = random.randint(0, 100)
                    if (r < 50):
                        # Left corner
                        if (possesion_team == 0):
                            ball.setPositioning([0, field_size[1]])
                        else:
                            ball.setPositioning([field_size[0], 0])
                    else:
                        # Right corner
                        if (possesion_team == 0):
                            ball.setPositioning([field_size[0], field_size[1]])
                        else:
                            ball.setPositioning([0, 0])

                    # Get closest player to corner
                    teams[possesion_team].resetPositionings(1)
                    ball.setPlayer(teams[possesion_team].getPlayerCorner(ball.getPositioning()))

                    statistics.execCornerKick(possesion_team, ball.getPlayer())
                    time_update += statistics.increaseTime(time_step / 2)

                    header_attacking = teams[possesion_team].getHeadingPlayer(ball)
                    header_defending = teams[rival_team].getHeadingPlayer(ball, False)
                    r = random.randint(0, header_attacking[1] + header_defending[1])
                    if (r < header_attacking[1]):
                        # Attacking header
                        r = random.randint(0, 100)
                        if (r < header_attacking[2]):
                            # Heading on target
                            statistics.execHeaderOnTarget(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                            r = random.randint(0, header_attacking[2] + teams[rival_team].getPlayerAtPos(0).getGoalKeeping())

                            if r < header_attacking[2]:
                                # GOAL
                                statistics.execScore(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                                ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                                time_update += statistics.increaseTime(time_step * 3)
                                play_type = 1
                            else:
                                # Goalkeeper defends
                                r = random.randint(0, 100)
                                if (r < teams[rival_team].getPlayerAtPos(0).getGoalKeeping()):
                                    # Goalkeeper keeps the ball
                                    statistics.execGoalkeeperDefence(rival_team, teams[rival_team].getPlayerAtPos(0))
                                    ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                                    play_type = 0
                                else:
                                    # Corner kick
                                    statistics.execGoalkeeperDefenceToCorner(rival_team, teams[rival_team].getPlayerAtPos(0))
                                    ball.setPlayer(teams[possesion_team].getPlayerCorner())
                                    play_type = 6

                                time_update += statistics.increaseTime(time_step)
                        else:
                            # Heading out
                            statistics.execHeaderAway(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                            ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                            time_update += statistics.increaseTime(time_step)
                            play_type = 5
                    else:
                        # Defending header
                        if (header_defending[0] == 0):
                            # Goalkeeper takes the ball
                            statistics.execGoalkeeperCutsCrossing(rival_team, teams[rival_team].getPlayerAtPos(0))
                            ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
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
                    closest_rival = teams[rival_team].getClosestPlayer(teams[possesion_team].getPlayer(possesion_player).getPositioning())
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
                    # Substitutions
                    if time_half == 2:
                        teams[0].checkSubstitutions(statistics)
                        teams[1].checkSubstitutions(statistics)

                    # Free kick
                    teams[possesion_team].resetPositionings(1)
                    teams[rival_team].resetPositionings(0)
                    shooter = teams[possesion_team].getClosestPlayer(ball.getPositioning())
                    ball.setPlayer(teams[possesion_team].getPlayer(shooter[0]))
                    goal_distance = Helper.calculateDistance(ball.getPlayer().getPositioning(), Field.getGoalPositioning(rival_team))

                    probs = [0, 0, 0] # 0 = passing, 1 = centering, 2 = shoot on goal
                    probs[0] = teams[possesion_team].getPlayer(shooter[0]).getPassing()

                    centering = int(teams[possesion_team].getPlayer(shooter[0]).getPassing() * teams[possesion_team].getPlayer(shooter[0]).getPrecision(Field.getGoalPositioning(rival_team)) / 100)
                    if centering > goal_distance:
                        probs[1] = int(math.pow((centering - goal_distance) / centering, 2) * 100)

                    shooting = int(teams[possesion_team].getPlayer(shooter[0]).getShootingStrength() * teams[possesion_team].getPlayer(shooter[0]).getPrecision(Field.getGoalPositioning(rival_team)) / 100)
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
                        header_defending = teams[rival_team].getHeadingPlayer(ball, False)
                        r = random.randint(0, header_attacking[1] + header_defending[1])
                        if (r < header_attacking[1]):
                            # Attacking header
                            r = random.randint(0, 100)
                            if (r < header_attacking[2]):
                                # Heading on target
                                statistics.execHeaderOnTarget(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                                r = random.randint(0, header_attacking[2] + teams[rival_team].getPlayerAtPos(0).getGoalKeeping())

                                if r < header_attacking[2]:
                                    # GOAL
                                    statistics.execScore(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                                    ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                                    time_update += statistics.increaseTime(time_step * 3)
                                    play_type = 1
                                else:
                                    # Goalkeeper defends
                                    r = random.randint(0, 100)
                                    if (r < teams[rival_team].getPlayerAtPos(0).getGoalKeeping()):
                                        # Goalkeeper keeps the ball
                                        statistics.execGoalkeeperDefence(rival_team, teams[rival_team].getPlayerAtPos(0))
                                        ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                                        play_type = 0
                                    else:
                                        # Corner kick
                                        statistics.execGoalkeeperDefenceToCorner(rival_team, teams[rival_team].getPlayerAtPos(0))
                                        ball.setPlayer(teams[possesion_team].getPlayerCorner())
                                        play_type = 6

                                    time_update += statistics.increaseTime(time_step)
                            else:
                                # Heading out
                                statistics.execHeaderAway(possesion_team, teams[possesion_team].getPlayer(header_attacking[0]))
                                ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                                time_update += statistics.increaseTime(time_step)
                                play_type = 5
                        else:
                            # Defending header
                            if (header_defending[0] == 0):
                                # Goalkeeper takes the ball
                                statistics.execGoalkeeperCutsCrossing(rival_team, teams[rival_team].getPlayerAtPos(0))
                                ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
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
                            probs = [teams[possesion_team].getPlayer(shooter[0]).getPrecision(Field.getGoalPositioning(rival_team)), teams[rival_team].getPlayerAtPos(0).getGoalKeeping()]
                            total = probs[0] + probs[1]
                            probs[0] = int(probs[0] * 100 / total)
                            probs[1] = 100

                            r = random.randint(0, 100)
                            if r < probs[0]:
                                # GOAL
                                statistics.execFreekickScore(possesion_team, teams[possesion_team].getPlayer(possesion_player))
                                ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                                time_update += statistics.increaseTime(time_step * 3)
                                play_type = 1
                            else:
                                # Goalkeeper defends
                                r = random.randint(0, 100)
                                if (r < teams[rival_team].getPlayerAtPos(0).getGoalKeeping()):
                                    # Goalkeeper keeps the ball
                                    statistics.execGoalkeeperDefence(rival_team, teams[rival_team].getPlayerAtPos(0))
                                    ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                                    play_type = 0
                                else:
                                    # Corner kick
                                    statistics.execGoalkeeperDefenceToCorner(rival_team, teams[rival_team].getPlayerAtPos(0))
                                    ball.setPlayer(teams[possesion_team].getPlayerCorner())
                                    play_type = 6
                                time_update += statistics.increaseTime(time_step)
                        else:
                            # Shoot away
                            statistics.execShootAway(possesion_team, teams[possesion_team].getPlayer(possesion_player))
                            ball.setPlayer(teams[rival_team].getPlayerAtPos(0))
                            time_update += statistics.increaseTime(time_step)
                            play_type = 5

                    time_update += statistics.increaseTime(time_step)
                else:
                    # Regular play
                    closest_friend = teams[possesion_team].getClosestPlayer(teams[possesion_team].getPlayer(possesion_player).getPositioning(), possesion_player)
                    closest_rival = teams[rival_team].getClosestPlayer(teams[possesion_team].getPlayer(possesion_player).getPositioning())
                    goal_distance = Helper.calculateDistance(ball.getPlayer().getPositioning(), Field.getGoalPositioning(rival_team))
                    play_type = teams[possesion_team].getNextPlay(possesion_player, closest_friend, closest_rival, goal_distance)
                    time_update += statistics.increaseTime(time_step / 2)

                teams[0].updatePositionings(field_size, ball, time_update)
                teams[1].updatePositionings(field_size, ball, time_update)
            print('*** FINAL ' + ('PRIMER' if time_half == 1 else 'SEGUNDO') + ' TIEMPO ***')

            time_half += 1
            time_total *= 2
            kickoff_team = (kickoff_team + 1) % 2
            play_type = 1

        print('')
        print(statistics)
        print('')

        if (output_file != ''):
            statistics.writeOutput(db_connection)

        # If tournament match
        if (match_type == 3):
            # Increase player's experience
            if teams[0].getId() > 26:
                for player in teams[0].getPlayersList():
                    player.saveStatus(db_connection)

            if teams[1].getId() > 26:
                for player in teams[1].getPlayersList():
                    player.saveStatus(db_connection)

            # Update scorers
            statistics.saveScorers(db_connection)

        return statistics