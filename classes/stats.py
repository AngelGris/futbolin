#!/usr/bin/python3

import random
import math
import json
import time
import datetime
import os

class Stats:
    def __init__(self, local, visit, matchType, debugLevel = 0, outputFile = '', categoryId = 0):
        self._local = local
        self._visit = visit
        self._matchType = matchType
        self._debugLevel = debugLevel
        self._outputFile = outputFile
        self._categoryId = categoryId
        if outputFile != '':
            self._output = []
        self._goals = [0, 0]
        self._time = 0.0
        self._possesion = 0
        self._possesionLastChange = 0
        self._possesionTime = [0, 0]
        self._shots = [[0, 0], [0, 0]]
        self._scorers = []
        self._substitutions = [0, 0]
        self._injuries = [0, 0]

    def __str__ (self):
        self._possesionPerc = [0, 0]
        if (self._possesionTime[0] + self._possesionTime[1] > 0):
            self._possesionPerc = [self._possesionTime[0] * 100.0 / (self._possesionTime[0] + self._possesionTime[1]), self._possesionTime[1] * 100.0 / (self._possesionTime[0] + self._possesionTime[1])]

        if self._outputFile == '':
            cols = [15, 10, 10]
            total_width = cols[0] + cols[1] + cols[2] + 2
            output =  '{:*^{width}}'.format('ESTADISTICAS', width=total_width) + '\n'
            output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Goles:', *self._goals, width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
            output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Posesión:', Stats.formatTime(self._possesionTime[0]), Stats.formatTime(self._possesionTime[1]), width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
            output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Posesión %:', '{:05.2f}%'.format(self._possesionPerc[0]), '{:05.2f}%'.format(self._possesionPerc[1]), width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
            output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Disparos:', str(self._shots[0][0]) + ' (' + str(self._shots[0][1]) + ')', str(self._shots[1][0]) + ' (' + str(self._shots[1][1]) + ')', width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
            output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Cambios:', str(self._substitutions[0]), str(self._substitutions[1]), width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
            output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Lesiones:', str(self._injuries[0]), str(self._injuries[1]), width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
        else:
            output = ''
        return output

    def _printAction(self, level, team, action, description):
        # Levels
        # 0 = Show always
        # 1 = Show on log
        # 2 = Show on debug mode
        # 3 = Show debug and wait

        # Actions
        #  1 = Corner kick
        #  2 = Heading defence
        #  3 = Dribbling
        #  4 = Foul
        #  5 = Freekick on goal
        #  6 = Freekick goal scored
        #  7 = Goal keeper cuts the crossing
        #  8 = Goalkeeper defends
        #  9 = Goalkeeper to corner
        # 10 = Goalkick
        # 11 = Heading away
        # 12 = Heading on goal
        # 13 = Pass intercepted
        # 14 = Kick off
        # 15 = Passing
        # 16 = Run with the ball
        # 17 = Shoot away
        # 18 = Shoot on goal
        # 19 = Goal scored
        # 20 = Ball stolen
        # 21 = Match suspended
        # 22 = Substitution
        # 23 = Player injured
        if self._outputFile == '':
            if self._debugLevel == 3:
                input(self.getFormattedTime() + ' - ' + description)
            elif level <= self._debugLevel:
                print(self.getFormattedTime(), '-', description)
        else:
            self._output.append([self.getFormattedTime(), team, action, description])

    def _setPossesion(self, team):
        if team != self._possesion:
            self._possesionTime[self._possesion] += self._time - self._possesionLastChange
            self._possesion = team
            self._possesionLastChange = self._time

    def execCornerKick(self, team, player):
        player.increasePlay()
        self._printAction(0, team, 1, str(player) + ' va a ejecutar el tiro de esquina')

    def execDefendingHeader(self, team, player):
        player.increasePlay(2)
        self._setPossesion(team)
        self._printAction(0, team, 2, str(player) + ' rechaza de cabeza')

    def execDribbling(self, team, player1, player2):
        player1.increasePlay()
        player2.increasePlay()
        self._printAction(2, team, 3, str(player1) + ' escapa de la marca de ' + str(player2))

    def execFoul(self, team, player1, player2):
        player1.increasePlay()
        player2.increasePlay()
        self._printAction(1, team, 4, str(player2) + ' le hace falta a ' + str(player1))

    def execFreekickOnGoal(self, team, player):
        player.increasePlay()
        self._printAction(0, team, 5, str(player) + ' patea el tiro libre directo al arco...')

    def execFreekickScore(self, team, player):
        player.increasePlay()
        self._printAction(0, team, 6, 'GOOOOOOLLLL de ' + str(player) + ' de tiro libre!!!')
        self._scorers.append([self.getFormattedTime(), team, player.getShortName(), player.getId()])
        self._goals[team] += 1

    def execGoalkeeperCutsCrossing(self, team, player):
        player.increasePlay(10)
        self._setPossesion(team)
        self._printAction(1, team, 7, str(player) + ' sale y corta el centro')

    def execGoalkeeperDefence(self, team, player):
        player.increasePlay(50)
        self._setPossesion(team)
        self._printAction(0, team, 8, str(player) + ' ataja el remate')

    def execGoalkeeperDefenceToCorner(self, team, player):
        player.increasePlay(30)
        self._printAction(0, team, 9, str(player) + ' saca el tiro al corner')

    def execGoalKick(self, team, player):
        player.increasePlay(5)
        self._setPossesion(team)
        self._printAction(2, team, 10, str(player) + ' saca desde el arco')

    def execHeaderAway(self, team, player):
        player.increasePlay()
        self._shots[team][0] += 1
        self._printAction(0, team, 11, str(player) + ' cabecea fuera')

    def execHeaderOnTarget(self, team, player):
        player.increasePlay()
        self._shots[team][0] += 1
        self._shots[team][1] += 1
        self._printAction(0, team, 12, str(player) + ' cabecea al arco...')

    def execInjury(self, team, player):
        self._injuries[team] += 1
        self._printAction(0, team, 23, str(player) + ' se retira lesionado y no pueden hacer más cambios')

    def execInterception(self, team, player1, player2):
        player1.increasePlay()
        player2.increasePlay()
        self._setPossesion(team)
        self._printAction(2, team, 13, str(player2) + ' intercepta el pase de ' + str(player1))

    def execKickoff(self, team, player1, player2):
        player1.increasePlay()
        player2.increasePlay()
        self._setPossesion(team)
        self._printAction(1, team, 14, str(player1) + ' saca del medio para ' + str(player2))

    def execPassing(self, team, player1, player2):
        player1.increasePlay()
        player2.increasePlay()
        self._printAction(2, team, 15, str(player1) + ' pasa la pelota a ' + str(player2))

    def execRun(self, team, player):
        player.increasePlay()
        self._printAction(2, team, 16, str(player) + ' corre con la pelota')

    def execScore(self, team, player):
        player.increasePlay()
        self._printAction(0, team, 19, 'GOOOOOLLLL!!!!! de ' + str(player))
        self._scorers.append([self.getFormattedTime(), team, player.getShortName(), player.getId()])
        self._goals[team] += 1

    def execShootAway(self, team, player):
        player.increasePlay()
        self._shots[team][0] += 1
        self._printAction(0, team, 17, str(player) + ' dispara desviado, saque de arco')

    def execShootOnGoal(self, team, player):
        player.increasePlay()
        self._shots[team][0] += 1
        self._shots[team][1] += 1
        self._printAction(0, team, 18, str(player) + ' tira al arco...')

    def execSubstitution(self, team, player_out, player_in):
        self._substitutions[team] += 1
        self._printAction(0, team, 22, 'Sale ' + str(player_out) + ' y entra ' + str(player_in))

    def execSubstitutionInjury(self, team, player_out, player_in):
        self._substitutions[team] += 1
        self._injuries[team] += 1
        self._printAction(0, team, 23, str(player_out) + ' se retira lesionado y entra ' + str(player_in))

    def execSuspendMatch(self, team):
        if (team is not None):
            self._goals[team] = 2
        else:
            team = 1

        self._printAction(0, team, 21, 'Partido suspendido por equipo incompleto')

    def execTackling(self, team, player1, player2):
        player1.increasePlay()
        player2.increasePlay()
        self._setPossesion(team)
        self._printAction(2, team, 20, str(player2) + ' le quita la pelota a ' + str(player1))

    def formatTime(time):
        return "%02d:%02d" % (int(time / 60), int(time % 60))

    def getFormattedTime(self):
        return Stats.formatTime(self._time)

    def getGoals(self):
        return self._goals

    def getInjuries(self):
        return self._injuries

    def getShots(self):
        return self._shots

    def getSubstitutions(self):
        return self._substitutions

    def getTime(self):
        return self._time

    def increaseTime(self, seconds):
        step = math.fabs(random.gauss(seconds, seconds / 4) + (seconds / 2))
        self._time += step

        return step

    def saveScorers(self, db_connection):
        scorers = [{}, {}]
        for scorer in self._scorers:
            try:
                scorers[scorer[1]][scorer[3]] += 1
            except:
                scorers[scorer[1]][scorer[3]] = 1

        for player in scorers[0]:
            db_connection.query('INSERT INTO `scorers` (`team_id`, `player_id`, `category_id`, `goals`) VALUES (' + str(self._local.getId()) + ', ' + str(player) + ', ' + str(self._categoryId) + ', ' + str(scorers[0][player]) + ') ON DUPLICATE KEY UPDATE `goals` = `goals` + ' + str(scorers[0][player]), 0)

        for player in scorers[1]:
            db_connection.query('INSERT INTO `scorers` (`team_id`, `player_id`, `category_id`, `goals`) VALUES (' + str(self._visit.getId()) + ', ' + str(player) + ', ' + str(self._categoryId) + ', ' + str(scorers[1][player]) + ') ON DUPLICATE KEY UPDATE `goals` = `goals` + ' + str(scorers[1][player]), 0)

    def writeOutput(self, db_connection):
        matchTime = int(time.time())
        matchDateTime = datetime.datetime.fromtimestamp(matchTime).strftime('%Y-%m-%d %H:%M:%S')

        output = {
            'timestamp' : matchTime,
            'stadium' : self._local.getStadiumName(),
            'local' : {
                'id' : self._local.getId(),
                'goals' : self._goals[0],
                'posession' : Stats.formatTime(self._possesionTime[0]),
                'posessionPer' : '{:05.2f}%'.format(self._possesionPerc[0]),
                'shots' : self._shots[0][0],
                'shotsOnTarget' : self._shots[0][1],
                'formation' : self._local.getStartingFormation(),
                'substitutions' : self._substitutions[0],
            },
            'visit' : {
                'id' : self._visit.getId(),
                'goals' : self._goals[1],
                'posession' : Stats.formatTime(self._possesionTime[1]),
                'posessionPer' : '{:05.2f}%'.format(self._possesionPerc[1]),
                'shots' : self._shots[1][0],
                'shotsOnTarget' : self._shots[1][1],
                'formation' : self._visit.getStartingFormation(),
                'substitutions' : self._substitutions[1],
            },
            'plays' : self._output,
            'scorers' : self._scorers,
        }
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'logs/') + self._outputFile, 'a') as out:
            out.write(json.dumps(output) + '\n')

        winner = 0
        if self._goals[0] > self._goals[1]:
            winner = 1
        elif self._goals[0] < self._goals[1]:
            winner = 2

        db_connection.query('INSERT INTO `matches` (`stadium`, `type_id`, `local_id`, `local_goals`, `visit_id`, `visit_goals`, `winner`, `logfile`, `created_at`, `updated_at`) VALUES (\'' + self._local.getStadiumName() + '\', ' + str(self._matchType) + ', ' + str(self._local.getId()) + ', ' + str(self._goals[0]) + ', ' + str(self._visit.getId()) + ', ' + str(self._goals[1]) + ', ' + str(winner) + ', \'' + self._outputFile + '\', \'' + matchDateTime + '\', \'' + matchDateTime + '\')', 0)