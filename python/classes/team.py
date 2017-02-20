#!/usr/bin/python3

import classes.player as player
import random
import math
from classes.helper import Helper

class Team:
    count = 0
    formation_4_4_2 = [
        [[45.0, 0.5], [45.0, 25.0]],
        [[35.0, 10.5], [35.0, 45.0]],
        [[15.0, 25.0], [15.0, 55.0]],
        [[75.0, 25.0], [75.0, 55.0]],
        [[35.0, 35.0], [35.0, 75.0]],
        [[55.0, 10.5], [55.0, 45.0]],
        [[15.0, 45.0], [15.0, 95.0]],
        [[75.0, 45.0], [75.0, 95.0]],
        [[35.0, 55.0], [35.0, 105.0]],
        [[55.0, 35.0], [55.0, 75.0]],
        [[55.0, 55.0], [55.0, 105.0]]
    ]

    def __init__(self, name, field):
        self._index = Team.count
        self._name = name
        self._players = []
        for x in range(11):
            position = Team.formation_4_4_2[x]
            if self._index == 1:
                position[0][0] = field[0] - position[0][0]
                position[0][1] = field[1] - position[0][1]
                position[1][0] = field[0] - position[1][0]
                position[1][1] = field[1] - position[1][1]

            self._players.append(player.Player(self._index, x, x + 1, self._name + '_' + str(x + 1), [position[0][0], position[0][1]], [position[1][0], position[1][1]]))

        Team.count += 1

    def __str__(self):
        output = ''
        for player in self._players:
            output += str(player) + '\n'
        return output

    def getClosestPlayer(self, position, exclude = -1):
        distance_min = 120
        player = 0
        for x in range(11):
            if (exclude != x):
                distance = Helper.calculateDistance(position, self._players[x].getPosition())
                if (distance < distance_min):
                    distance_min = distance
                    player = x

        return [player, distance_min, self._players[player].getSpeed()]

    def getHeadingPlayer(self, ball, goalkeeper = True):
        probs = [0 for x in range(11)]
        if goalkeeper:
            probs[0] = self._players[0].getJumping()

        for x in range(1,11):
            probs[x] = self._players[0].getJumping()

        total = 0
        for x in range(11):
            total += probs[x]
            probs[x] = total

        r = random.randint(0, total)
        s = 0
        while(probs[s] < r):
            s += 1

        return [s, self._players[s].getJumping(), self._players[s].getHeading()]

    def getNextPlay(self, player, closest_friend, closest_rival, goal_distance):
        probs = [0, 0, 0, 0] # 0 = running, 1 = passing, 2 = shooting, 3 = dribbling
        plays = [2, 3, 4, 7] # 0 = running, 1 = passing, 2 = shooting, 3 = dribbling

        if goal_distance <= self._players[player].getShootingStrength():
            # In shooting range
            probs[2] = int(math.pow((self._players[player].getShootingStrength() - goal_distance) / self._players[player].getShootingStrength(),2) * 100)

        if closest_rival[1] > (closest_rival[2] * 2):
            # No near rival
            probs[0] = int((100 - probs[2]) * 0.6)
        elif closest_rival[1] > closest_rival[2]:
            # Rival getting closer
            probs[0] = int((100 - probs[2]) * 0.4)
        else:
            # Rival is here
            probs[0] = int((100 - probs[2]) * 0.2)
            probs[3] = self._players[player].getDribbling() / 100.0

        probs[0] = int(probs[0] * self._players[player].getProbsToRun())
        probs[3] = int((100 - probs[0] - probs[2]) * probs[3])
        probs[1] = 100 - probs[0] - probs[2] - probs[3]

        total = []
        total.append(probs[0])
        total.append(total[0] + probs[1])
        total.append(total[1] + probs[2])
        total.append(total[2] + probs[3])

        r = random.randint(0, 100)
        s = 0
        while(total[s] < r):
            s += 1

        return plays[s]

    def getPass(self, pos, forward = False):
        distances = [0 for x in range(11)]
        distance_max = 0
        location = self._players[pos].getPosition()
        for x in range(11):
            if(x != pos):
                destination = self._players[x].getPosition()
                distance = int(Helper.calculateDistance(location, destination))
                if (forward and ((self._index == 0 and location[1] < destination[1]) or (self._index == 1 and location[1] > destination[1]))):
                    distance = int(distance / 2)

                distances[x] = distance
                if(distance > distance_max):
                    distance_max = distance

        distances[pos] = distance_max
        probs = [0 for x in range(11)]
        prob_total = 0
        for x in range(11):
            prob_total += distance_max - distances[x]
            probs[x] = prob_total

        r = random.randint(0, prob_total)
        s = 0
        while(probs[s] < r):
            s += 1

        return s

    def getPlayer(self, pos):
        return self._players[pos]

    def getPlayerCorner(self):
        return self._players[6]

    def playerString(self, pos):
        return str(self._players[pos])

    def resetPositions(self, proportion = 0):
        for x in range(11):
            self._players[x].resetPosition(proportion)

    def setPlayerPosition(self, player, position):
        self._players[player].setPosition(position)

    def showField(self):
        field = [[0 for x in range(9)] for y in range(12)]

        for player in self._players:
            position = player.getPosition()
            pos_x = int((position[1]) // 10)
            pos_y = int((position[0]) // 10)
            field[pos_x][pos_y] = player.getNumber()

        for r in field:
            row = ''
            for f in r:
                if f == 0:
                    row += '..'
                elif f < 10:
                    row += '0' + str(f)
                else:
                    row += str(f)

            print(row)

    def updatePositions(self, field, ball, seconds):
        if self._index == 0:
            position = ball.getPosition()
        else:
            ball_position = ball.getPosition()
            position = [field[0] - ball_position[0], field[1] - ball_position[1]]

        portion = position[1] / field[1]
        for player in self._players:
            player.updatePosition(portion, seconds)