#!/usr/bin/python3

import random
import math
import json
import time
import os

class Stats:
    def __init__(self, local, visit, debugLevel = 0, outputFile = ''):
        self._local = local
        self._visit = visit
        self._debugLevel = debugLevel
        self._outputFile = outputFile
        if outputFile != '':
            self._output = []
        self._goals = [0, 0]
        self._time = 0.0
        self._possesion = 0
        self._possesionLastChange = 0
        self._possesionTime = [0, 0]
        self._shots = [[0, 0], [0, 0]]
        self._scorers = []

    def __str__ (self):
        self._possesionPerc = [self._possesionTime[0] * 100.0 / (self._possesionTime[0] + self._possesionTime[1]), self._possesionTime[1] * 100.0 / (self._possesionTime[0] + self._possesionTime[1])]

        cols = [15, 10, 10]
        total_width = cols[0] + cols[1] + cols[2] + 2
        output =  '{:*^{width}}'.format('ESTADISTICAS', width=total_width) + '\n'
        output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Goles:', *self._goals, width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
        output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Posesión:', Stats.formatTime(self._possesionTime[0]), Stats.formatTime(self._possesionTime[1]), width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
        output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Posesión %:', '{:05.2f}%'.format(self._possesionPerc[0]), '{:05.2f}%'.format(self._possesionPerc[1]), width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
        output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Disparos:', str(self._shots[0][0]) + ' (' + str(self._shots[0][1]) + ')', str(self._shots[1][0]) + ' (' + str(self._shots[1][1]) + ')', width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
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
        self._printAction(0, team, 1, str(player) + ' va a ejecutar el tiro de esquina')

    def execDefendingHeader(self, team, player):
        self._printAction(0, team, 2, str(player) + ' rechaza de cabeza')

    def execDribbling(self, team, player1, player2):
        self._printAction(2, team, 3, str(player1) + ' escapa de la marca de ' + str(player2))

    def execFoul(self, team, player1, player2):
        self._printAction(1, team, 4, str(player2) + ' le hace falta a ' + str(player1))

    def execFreekickOnGoal(self, team, player):
        self._printAction(0, team, 5, str(player) + ' patea el tiro libre directo al arco...')

    def execFreekickScore(self, team, player):
        self._printAction(0, team, 6, 'GOOOOOOLLLL de ' + str(player) + ' de tiro libre!!!')
        self._scorers.append([self.getFormattedTime(), team, player])
        self._goals[team] += 1

    def execGoalkeeperCutsCrossing(self, team, player):
        self._setPossesion(team)
        self._printAction(1, team, 7, str(player) + ' sale y corta el centro')

    def execGoalkeeperDefence(self, team, player):
        self._setPossesion(team)
        self._printAction(0, team, 8, str(player) + ' ataja el remate')

    def execGoalkeeperDefenceToCorner(self, team, player):
        self._printAction(0, (team + 1) % 2, 9, str(player) + ' saca el tiro al corner')

    def execGoalKick(self, team, player):
        self._printAction(2, team, 10, str(player) + ' saca desde el arco')

    def execHeaderAway(self, team, player):
        self._shots[team][0] += 1
        self._printAction(0, team, 11, str(player) + ' cabecea fuera')

    def execHeaderOnTarget(self, team, player):
        self._shots[team][0] += 1
        self._shots[team][1] += 1
        self._printAction(0, team, 12, str(player) + ' cabecea al arco...')

    def execInterception(self, team, player1, player2):
        self._setPossesion(team)
        self._printAction(2, team, 13, str(player2) + ' intercepta el pase de ' + str(player1))

    def execKickoff(self, team, player1, player2):
        self._setPossesion(team)
        self._printAction(1, team, 14, str(player1) + ' saca del medio para ' + str(player2))

    def execPassing(self, team, player1, player2):
        self._printAction(2, team, 15, str(player1) + ' pasa la pelota a ' + str(player2))

    def execRun(self, team, player):
        self._printAction(2, team, 16, str(player) + ' corre con la pelota')

    def execShootAway(self, team, player):
        self._shots[team][0] += 1
        self._printAction(0, team, 17, str(player) + ' dispara desviado, saque de arco')

    def execShootOnGoal(self, team, player):
        self._shots[team][0] += 1
        self._shots[team][1] += 1
        self._printAction(0, team, 18, str(player) + ' tira al arco...')

    def execScore(self, team, player):
        self._printAction(0, team, 19, 'GOOOOOLLLL!!!!! de ' + str(player))
        self._scorers.append([self.getFormattedTime(), team, player])
        self._goals[team] += 1

    def execTackling(self, team, player1, player2):
        self._setPossesion(team)
        self._printAction(2, team, 20, str(player2) + ' le quita la pelota a ' + str(player1))

    def formatTime(time):
        return "%02d:%02d" % (int(time / 60), int(time % 60))

    def getFormattedTime(self):
        return Stats.formatTime(self._time)

    def getGoals(self):
        return self._goals

    def getShots(self):
        return self._shots

    def getTime(self):
        return self._time

    def increaseTime(self, seconds):
        step = math.fabs(random.gauss(seconds, seconds / 4) + (seconds / 2))
        self._time += step

        return step

    def writeOutput(self):
        output = {
            'timestamp' : int(time.time()),
            'local' : {
                'id' : self._local.getId(),
                'goals' : self._goals[0],
                'posession' : Stats.formatTime(self._possesionTime[0]),
                'posessionPer' : '{:05.2f}%'.format(self._possesionPerc[0]),
                'shots' : self._shots[0][0],
                'shotsOnTarget' : self._shots[0][1],
                'formation' : self._local.getFormation(),
            },
            'visit' : {
                'id' : self._visit.getId(),
                'goals' : self._goals[1],
                'posession' : Stats.formatTime(self._possesionTime[1]),
                'posessionPer' : '{:05.2f}%'.format(self._possesionPerc[1]),
                'shots' : self._shots[1][0],
                'shotsOnTarget' : self._shots[1][1],
                'formation' : self._visit.getFormation(),
            },
            'plays' : self._output,
            'scorers' : self._scorers,
        }
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'logs/') + self._outputFile, 'a') as out:
            out.write(json.dumps(output) + '\n')