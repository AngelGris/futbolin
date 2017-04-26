#!/usr/bin/python3

import random
import math

class Stats:
    def __init__(self, debugLevel = 0):
        self._debugLevel = debugLevel
        self._goals = [0, 0]
        self._time = 0.0
        self._possesion = 0
        self._possesionLastChange = 0
        self._possesionTime = [0, 0]
        self._shots = [[0, 0], [0, 0]]

    def __str__ (self):
        possesionPerc = [self._possesionTime[0] * 100.0 / (self._possesionTime[0] + self._possesionTime[1]), self._possesionTime[1] * 100.0 / (self._possesionTime[0] + self._possesionTime[1])]


        cols = [15, 10, 10]
        total_width = cols[0] + cols[1] + cols[2] + 2
        output =  '{:*^{width}}'.format('ESTADISTICAS', width=total_width) + '\n'
        output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Goles:', *self._goals, width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
        output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Posesión:', Stats.formatTime(self._possesionTime[0]), Stats.formatTime(self._possesionTime[1]), width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
        output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Posesión %:', '{:05.2f}%'.format(possesionPerc[0]), '{:05.2f}%'.format(possesionPerc[1]), width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
        output += '{:<{width1}} {:>{width2}} {:>{width3}}'.format('Disparos:', str(self._shots[0][0]) + ' (' + str(self._shots[0][1]) + ')', str(self._shots[1][0]) + ' (' + str(self._shots[1][1]) + ')', width1=cols[0], width2=cols[1], width3=cols[2]) + '\n'
        return output

    def _printAction(self, level, action):
        # Levels
        # 0 = Show always
        # 1 = Show on log
        # 2 = Show on debug mode
        # 3 = Show debug and wait
        if self._debugLevel == 3:
            input(self.getFormattedTime() + ' - ' + action)
        elif level <= self._debugLevel:
            print(self.getFormattedTime(), '-', action)

    def _setPossesion(self, team):
        if team != self._possesion:
            self._possesionTime[self._possesion] += self._time - self._possesionLastChange
            self._possesion = team
            self._possesionLastChange = self._time

    def execCornerKick(self, team, player):
        self._printAction(0, str(player) + ' va a ejecutar el tiro de esquina')

    def execDefendingHeader(self, team, player):
        self._printAction(0, str(player) + ' rechaza de cabeza')

    def execDribbling(self, team, player1, player2):
        self._printAction(2, str(player1) + ' escapa de la marca de ' + str(player2))

    def execFoul(self, team, player1, player2):
        self._printAction(1, str(player2) + ' le hace falta a ' + str(player1))

    def execFreekickOnGoal(self, team, player):
        self._printAction(0, str(player) + ' patea el tiro libre directo al arco...')

    def execFreekickScore(self, team, player):
        self._printAction(0, 'GOOOOOOLLLL de ' + str(player) + ' de tiro libre!!!')
        self._goals[team] += 1

    def execGoalkeeperCutsCrossing(self, team, player):
        self._setPossesion(team)
        self._printAction(1, str(player) + ' sale y corta el centro')

    def execGoalkeeperDefence(self, team, player):
        self._setPossesion(team)
        self._printAction(0, str(player) + ' ataja el remate')

    def execGoalkeeperDefenceToCorner(self, team, player):
        self._printAction(0, str(player) + ' saca el tiro al corner')

    def execGoalKick(self, team, player):
        self._printAction(2, str(player) + ' saca desde el arco')

    def execHeaderAway(self, team, player):
        self._shots[team][0] += 1
        self._printAction(0, str(player) + ' cabecea fuera')

    def execHeaderOnTarget(self, team, player):
        self._shots[team][0] += 1
        self._shots[team][1] += 1
        self._printAction(0, str(player) + ' cabecea al arco...')

    def execInterception(self, team, player1, player2):
        self._setPossesion(team)
        self._printAction(2, str(player2) + ' intercepta el pase de ' + str(player1))

    def execKickoff(self, team, player1, player2):
        self._setPossesion(team)
        self._printAction(1, str(player1) + ' saca del medio para ' + str(player2))

    def execPassing(self, player1, player2):
        self._printAction(2, str(player1) + ' pasa la pelota a ' + str(player2))

    def execRun(self, team, player):
        self._printAction(2, str(player) + ' corre con la pelota')

    def execShootAway(self, team, player):
        self._shots[team][0] += 1
        self._printAction(0, str(player) + ' dispara desviado, saque de arco')

    def execShootOnGoal(self, team, player):
        self._shots[team][0] += 1
        self._shots[team][1] += 1
        self._printAction(0, str(player) + ' tira al arco...')

    def execScore(self, team, player):
        self._printAction(0, 'GOOOOOLLLL!!!!! de ' + str(player))
        self._goals[team] += 1

    def execTackling(self, team, player1, player2):
        self._setPossesion(team)
        self._printAction(2, str(player2) + ' le quita la pelota a ' + str(player1))

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