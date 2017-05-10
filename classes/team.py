#!/usr/bin/python3

import classes.player as player
import random
import math
import json
from classes.helper import Helper

class Team:
    _db_connection = None
    count = 0

    def __init__(self, id, field, db_connection):
        self._db_connection = db_connection
        result = self._db_connection.query("SELECT `teams`.`name`, `teams`.`short_name`, `teams`.`formation`, `strategies`.`j01_start_x`, `strategies`.`j01_start_y`, `strategies`.`j01_end_x`, `strategies`.`j01_end_y`, `strategies`.`j02_start_x`, `strategies`.`j02_start_y`, `strategies`.`j02_end_x`, `strategies`.`j02_end_y`, `strategies`.`j03_start_x`, `strategies`.`j03_start_y`, `strategies`.`j03_end_x`, `strategies`.`j03_end_y`, `strategies`.`j04_start_x`, `strategies`.`j04_start_y`, `strategies`.`j04_end_x`, `strategies`.`j04_end_y`, `strategies`.`j05_start_x`, `strategies`.`j05_start_y`, `strategies`.`j05_end_x`, `strategies`.`j05_end_y`, `strategies`.`j06_start_x`, `strategies`.`j06_start_y`, `strategies`.`j06_end_x`, `strategies`.`j06_end_y`, `strategies`.`j07_start_x`, `strategies`.`j07_start_y`, `strategies`.`j07_end_x`, `strategies`.`j07_end_y`, `strategies`.`j08_start_x`, `strategies`.`j08_start_y`, `strategies`.`j08_end_x`, `strategies`.`j08_end_y`, `strategies`.`j09_start_x`, `strategies`.`j09_start_y`, `strategies`.`j09_end_x`, `strategies`.`j09_end_y`, `strategies`.`j10_start_x`, `strategies`.`j10_start_y`, `strategies`.`j10_end_x`, `strategies`.`j10_end_y`, `strategies`.`j11_start_x`, `strategies`.`j11_start_y`, `strategies`.`j11_end_x`, `strategies`.`j11_end_y` FROM `teams` INNER JOIN `strategies` ON `strategies`.`id` = `teams`.`strategy_id` WHERE `teams`.`id` = " + str(id) + " LIMIT 1", 1)

        self._id = id
        self._field = field
        self._index = Team.count
        self._name = result['name']
        self._short_name = result['short_name']
        self._players = []
        self._substitutes = []
        formation = json.loads(result['formation'])
        count = 0
        for pid in formation:
            position = [[], []]
            if (count < 11):
                if self._index == 0:
                    position[0].append(result["j%02d_start_x" % (count + 1)])
                    position[0].append(result["j%02d_start_y" % (count + 1)])
                    position[1].append(result["j%02d_end_x" % (count + 1)])
                    position[1].append(result["j%02d_end_y" % (count + 1)])
                else:
                    position[0].append(field[0] - result["j%02d_start_x" % (count + 1)])
                    position[0].append(field[1] - result["j%02d_start_y" % (count + 1)])
                    position[1].append(field[0] - result["j%02d_end_x" % (count + 1)])
                    position[1].append(field[1] - result["j%02d_end_y" % (count + 1)])

                self._players.append(player.Player(self._index, pid, count, [position[0][0], position[0][1]], [position[1][0], position[1][1]], db_connection))
            else:
                self._substitutes.append(player.Player(self._index, pid, count, [0,0], [0,0], db_connection))

            count += 1

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

    def getFormation(self):
        output = []
        for player in self._players:
            position = player.getPositionDefensive()

            if self._index == 0:
                top = min([44, int(position[1] * 100 / self._field[1])])
            else:
                top = max([56, int(position[1] * 100 / self._field[1])])

            output.append({
                'number' : player.getNumber(),
                'short_name' : player.getShortName(),
                'location' : position,
                'left' : int(position[0] * 100 / self._field[0]),
                'top' : top,
            })

        for player in self._substitutes:
            output.append({
                'number' : player.getNumber(),
                'short_name' : player.getShortName(),
                'location' : [0,0],
                'left' : 0,
                'top' : 0,
            })

        return output

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

    def getId(self):
        return self._id

    def getNextPlay(self, player, closest_friend, closest_rival, goal_distance):
        probs = [0, 0, 0, 0] # 0 = running, 1 = passing, 2 = shooting, 3 = dribbling
        plays = [2, 3, 4, 7] # 0 = running, 1 = passing, 2 = shooting, 3 = dribbling

        if goal_distance <= self._players[player].getMaxStrength():
            # In shooting range
            if (goal_distance < self._players[player].getShootingStrength()):
                probs[2] = self._players[player].getMaxStrength() - int(math.pow(goal_distance, 2)/self._players[player].getShootingStrength())
            else:
                probs[2] = int(math.pow(self._players[player].getMaxStrength() - goal_distance, 2)/(self._players[player].getMaxStrength() - self._players[player].getShootingStrength()))

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