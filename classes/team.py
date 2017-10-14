#!/usr/bin/python3

import classes.player as Player
import random
import math
import json
from classes.helper import Helper

class Team:
    _db_connection = None
    count = 0
    _enabled = False

    def __init__(self, id, field, match_type, max_stamina, category_id, db_connection, reset_counter = False):
        self._db_connection = db_connection
        result = self._db_connection.query("SELECT `teams`.`name`, `teams`.`short_name`, `teams`.`stadium_name`, `teams`.`formation`, `strategies`.`j01_start_x`, `strategies`.`j01_start_y`, `strategies`.`j01_end_x`, `strategies`.`j01_end_y`, `strategies`.`j02_start_x`, `strategies`.`j02_start_y`, `strategies`.`j02_end_x`, `strategies`.`j02_end_y`, `strategies`.`j03_start_x`, `strategies`.`j03_start_y`, `strategies`.`j03_end_x`, `strategies`.`j03_end_y`, `strategies`.`j04_start_x`, `strategies`.`j04_start_y`, `strategies`.`j04_end_x`, `strategies`.`j04_end_y`, `strategies`.`j05_start_x`, `strategies`.`j05_start_y`, `strategies`.`j05_end_x`, `strategies`.`j05_end_y`, `strategies`.`j06_start_x`, `strategies`.`j06_start_y`, `strategies`.`j06_end_x`, `strategies`.`j06_end_y`, `strategies`.`j07_start_x`, `strategies`.`j07_start_y`, `strategies`.`j07_end_x`, `strategies`.`j07_end_y`, `strategies`.`j08_start_x`, `strategies`.`j08_start_y`, `strategies`.`j08_end_x`, `strategies`.`j08_end_y`, `strategies`.`j09_start_x`, `strategies`.`j09_start_y`, `strategies`.`j09_end_x`, `strategies`.`j09_end_y`, `strategies`.`j10_start_x`, `strategies`.`j10_start_y`, `strategies`.`j10_end_x`, `strategies`.`j10_end_y`, `strategies`.`j11_start_x`, `strategies`.`j11_start_y`, `strategies`.`j11_end_x`, `strategies`.`j11_end_y` FROM `teams` INNER JOIN `strategies` ON `strategies`.`id` = `teams`.`strategy_id` WHERE `teams`.`id` = " + str(id) + " LIMIT 1", 1)
        self._id = id
        self._field = field
        if (reset_counter):
            Team.count = 0
        self._index = Team.count
        self._name = result['name']
        self._short_name = result['short_name']
        self._stadium_name = result['stadium_name']
        self._players_in_field = []
        self._players = []
        self._substitutions_count = 3
        if (result['formation'] != ''):
            # Load players
            formation = json.loads(result['formation'])
            count = 0
            players_added = 0
            for pid in formation:
                if (count < 11):
                    positioning = [[], []]
                    if self._index == 0:
                        positioning[0].append(result["j%02d_start_x" % (count + 1)])
                        positioning[0].append(result["j%02d_start_y" % (count + 1)])
                        positioning[1].append(result["j%02d_end_x" % (count + 1)])
                        positioning[1].append(result["j%02d_end_y" % (count + 1)])
                    else:
                        positioning[0].append(field[0] - result["j%02d_start_x" % (count + 1)])
                        positioning[0].append(field[1] - result["j%02d_start_y" % (count + 1)])
                        positioning[1].append(field[0] - result["j%02d_end_x" % (count + 1)])
                        positioning[1].append(field[1] - result["j%02d_end_y" % (count + 1)])
                else:
                    positioning = [[0,0], [0,0]]

                self._players.append(Player.Player(self._index, pid, count, [positioning[0][0], positioning[0][1]], [positioning[1][0], positioning[1][1]], max_stamina, match_type, category_id, db_connection))

                if count < 11:
                    self._players_in_field.append(count)
                    if int(pid) > 0:
                        players_added += 1

                count += 1

            # Check for missing players
            for index in range(len(self._players_in_field)):
                if not self._players[self._players_in_field[index]].isActive():
                    substitute = -1
                    for i in range(11, len(self._players)):
                        if i not in self._players_in_field and self._players[i].isActive():
                            substitute = i
                            break

                    if substitute >= 0:
                        self.substitution(index, substitute)
                        players_added += 1

            if (players_added >= 7):
                self._enabled = True

        self._startingFormation = []
        for index in self._players_in_field:
            if self._players[index].isPresent():
                self._startingFormation.append(self._players[index])
        for player in self._players:
            if player.getIndex() and player.isPresent() not in self._players_in_field:
                self._startingFormation.append(player)

        Team.count += 1

    def __str__(self):
        output = ''
        for player in self._players:
            output += str(player) + '\n'
        return output

    def checkSubstitutions(self, stats, player_out = False, Injured = False):
        players_out = []
        output = []
        if self._substitutions_count > 0:
            if (player_out):
                players_out = [player_out]
            else:
                for i in self._players_in_field:
                    player = self._players[i]
                    if (player.isActive() and player.isChangeable()):
                        players_out.append(player)

            for player_out in players_out:
                pos = self.getPlayerPosition(player_out.getIndex())

                player_in = False
                for player in self._players:
                    if player.isActive() and player.getIndex() not in self._players_in_field:
                        player_in = player
                        if player_out.getPosition() == player_in.getPosition():
                            break

                if (player_in):
                    output.append(player_in)
                    self.substitution(pos, player_in.getIndex(), stats, Injured)

        return output

    def getClosestPlayer(self, positioning, exclude = -1):
        distance_min = 200
        player = -1
        for x in self._players_in_field:
            if (exclude != x and self._players[x].isActive()):
                distance = Helper.calculateDistance(positioning, self._players[x].getPositioning())
                if (distance < distance_min):
                    distance_min = distance
                    player = x

        return [player, distance_min, self._players[player].getSpeed()]

    def getEnabled(self):
        return self._enabled

    def getFormation(self):
        output = []
        for player in self._players:
            positioning = player.getPositioningDefensive()

            if self._index == 0:
                top = min([44, int(positioning[1] * 100 / self._field[1])])
            else:
                top = max([56, int(positioning[1] * 100 / self._field[1])])

            if (player.isActive()):
                output.append({
                    'number' : player.getNumber(),
                    'short_name' : player.getShortName(),
                    'location' : positioning,
                    'left' : int(positioning[0] * 100 / self._field[0]),
                    'top' : top,
                })
            else:
                output.append({
                    'number' : '',
                    'short_name' : '',
                    'location' : positioning,
                    'left' : int(positioning[0] * 100 / self._field[0]),
                    'top' : top,
                })

        return output

    def getGoalkeeper(self):
        pos = 0
        while (not self._players[self._players_in_field[pos]].isActive()):
            pos += 1

        return self.getPlayerAtPos(pos)

    def getHeadingPlayer(self, ball, goalkeeper = True):
        probs = [0 for x in range(len(self._players_in_field))]
        if goalkeeper:
            if (self._players[self._players_in_field[0]].isActive()):
                probs[0] = self._players[self._players_in_field[0]].getJumping()
            else:
                probs[0] = 0

        for x in range(1,len(self._players_in_field)):
            player = self._players[x]
            if player.isActive():
                probs[x] = player.getJumping()
            else:
                probs[x] = 0

        # Centering player can't head
        if ball.getTeam() == self._index:
            probs[self._players_in_field.index(ball.getPlayer().getIndex())] = 0

        total = 0
        for x in range(len(probs)):
            total += probs[x]
            probs[x] = total

        r = random.randint(1, total)
        s = 0
        while(probs[s] < r):
            s += 1

        s = self._players_in_field[s]

        return [s, self._players[s].getJumping(), self._players[s].getHeading()]

    def getId(self):
        return self._id

    def getNextPlay(self, player, closest_friend, closest_rival, goal_distance):
        probs = [0, 0, 0, 0] # 0 = running, 1 = passing, 2 = shooting, 3 = dribbling
        plays = [2, 3, 4, 7] # 0 = running, 1 = passing, 2 = shooting, 3 = dribbling
        player = self._players[player]

        probs[2] = int(player.getProbsToShoot(goal_distance) * 50) # 50% is the highest chance to shoot on goal

        if closest_rival[1] > (closest_rival[2] * 2):
            # No near rival
            probs[0] = int((100 - probs[2]) * 0.6)
        elif closest_rival[1] > closest_rival[2]:
            # Rival getting closer
            probs[0] = int((100 - probs[2]) * 0.4)
        else:
            # Rival is here
            probs[0] = int((100 - probs[2]) * 0.2)
            probs[3] = player.getDribbling() / 100.0

        probs[0] = int(probs[0] * player.getProbsToRun())
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
        total = len(self._players_in_field)
        distances = [0 for x in range(total)]
        distance_max = 200
        location = self._players[pos].getPositioning()

        distances = [200 for x in range(total)]
        for x in range(total):
            if(self._players[self._players_in_field[x]].isActive() and self._players_in_field[x] != pos):
                destination = self._players[self._players_in_field[x]].getPositioning()
                distance = int(Helper.calculateDistance(location, destination))
                if (forward and ((self._index == 0 and location[1] < destination[1]) or (self._index == 1 and location[1] > destination[1]))):
                    distance = int(distance / 2)

                distances[x] =  distance

        probs = [0 for x in range(total)]
        prob_total = 0
        for x in range(total):
            prob_total += distance_max - distances[x]
            probs[x] = prob_total

        r = random.randint(1, prob_total)
        s = 0
        while(probs[s] < r):
            s += 1

        return self._players_in_field[s]

    def getPlayer(self, pos):
        return self._players[pos]

    def getPlayerAtPos(self, pos):
        return self.getPlayer(self._players_in_field[pos])

    def getPlayerCorner(self, positioning = False):
        if positioning:
            player = self.getClosestPlayer(positioning)
            index = player[0]
        else:
            index = self._players_in_field[0]

        return self._players[index]

    def getPlayerPosition(self, player):
        position = 0
        while (not self._players[self._players_in_field[position]].isActive() or player != self._players[self._players_in_field[position]].getIndex()):
            position += 1

        return position

    def getPlayersList(self):
        return self._players

    def getStadiumName(self):
        return self._stadium_name

    def getStartingFormation(self):
        output = []
        for player in self._startingFormation:
            positioning = player.getPositioningDefensive()

            if self._index == 0:
                top = min([44, int(positioning[1] * 100 / self._field[1])])
            else:
                top = max([56, int(positioning[1] * 100 / self._field[1])])

            if (player.isPresent()):
                output.append({
                    'number' : player.getNumber(),
                    'short_name' : player.getShortName(),
                    'location' : positioning,
                    'left' : int(positioning[0] * 100 / self._field[0]),
                    'top' : top,
                })
            else:
                output.append({
                    'number' : '',
                    'short_name' : '',
                    'location' : positioning,
                    'left' : int(positioning[0] * 100 / self._field[0]),
                    'top' : top,
                })

        return output

    def playerInjured(self, stats, index):
        player_in = self.checkSubstitutions(stats, self._players[index], True)
        if (len(player_in) == 0):
            player = self._players[index]
            stats.execInjury(self._index, player)
            player.deactivate(True)

    def playerString(self, pos):
        return str(self._players[pos])

    def redCard(self, stats, index):
        player = self._players[index]
        player.redCard()
        stats.execRedCard(self._index, player)

    def reset(self):
        self._substitutions_count = 3

    def resetPositionings(self, proportion = 0):
        for x in self._players_in_field:
            self._players[x].resetPositioning(proportion)

    def setPlayerPositioning(self, player, positioning):
        self._players[player].setPositioning(positioning)

    def showField(self):
        field = [[0 for x in range(9)] for y in range(12)]

        for x in self._players_in_field:
            player = self._players[x]
            positioning = player.getPositioning()
            pos_x = int((positioning[1]) // 10)
            pos_y = int((positioning[0]) // 10)
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

    def substitution(self, position, index_in, stats = False, Injured = False):
        if self._substitutions_count > 0:
            player_out =  self._players[self._players_in_field[position]]
            self._players[index_in].substitution(player_out.getPositioningDef(), player_out.getPositioningAtt())
            self._players_in_field[position] = index_in
            player_out.deactivate()

            if stats:
                self._substitutions_count -= 1
                if Injured:
                    stats.execSubstitutionInjury(self._index, player_out, self._players[index_in])
                else:
                    stats.execSubstitution(self._index, player_out, self._players[index_in])


    def updatePositionings(self, field, ball, seconds):
        if self._index == 0:
            positioning = ball.getPositioning()
        else:
            ball_positioning = ball.getPositioning()
            positioning = [field[0] - ball_positioning[0], field[1] - ball_positioning[1]]

        portion = positioning[1] / field[1]
        for x in self._players_in_field:
            self._players[x].updatePositioning(portion, seconds)

    def yellowCard(self, stats, index):
        player = self._players[index]

        if (player.yellowCard()):
            stats.execFirstYellowCard(self._index, player)
        else:
            stats.execSecondYellowCard(self._index, player)