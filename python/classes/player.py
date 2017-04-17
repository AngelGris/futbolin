#!/usr/bin/python3

import math
from classes.helper import Helper

class Player:
    # Constants
    _MAX_PRECISION = 100.0
    _MAX_SPEED = 8.0 # Meters per second
    _MAX_STRENGTH = 65.0 # How long it can shoot (Meters)

    def __init__(self, team, id, index, pos_def, pos_att, db_connection):
        self._team = team
        self._id = id
        self._index = index
        self._pos_def = pos_def.copy()
        self._pos_att = pos_att.copy()
        self._pos_cur = pos_def.copy()
        self._hasBall = False

        response = db_connection.query("SELECT * FROM `players` WHERE `id` = " + str(id) + " LIMIT 1;", 1)
        self._number = response['number']
        self._name = response['first_name'] + " " + response['last_name']
        names = response['first_name'].split();
        initials = '';
        for name in names:
            initials += name[0] + '. '
        self._short_name = initials + response['last_name']
        self._defending = response['defending'] # Chances to intercept a pass
        self._dribbling = response['dribbling'] # Ability to avoid a rival
        self._goalkeeping = response['goalkeeping'] # Ability while goalkeeping
        self._heading = response['heading'] # Heading on goal ability
        self._jumping = response['jumping'] # Ability to jump looking to head the ball
        self._passing = response['passing'] # Ability to make good passes
        self._precision = response['precision'] # Precision when shooting on goal
        self._speed = response['speed'] # Speed
        self._strength = response['strength'] # Strength to shoot on goal from far
        self._tackling = response['tackling'] # Chances to get the ball when tackling

    def __str__(self):
        return '(%d) %d - %s: %f, %f' % (self._team, self._number, self._short_name, self._pos_cur[0], self._pos_cur[1])

    def getDefending(self):
        return self._defending

    def getDribbling(self):
        return self._dribbling

    def getGoalKeeping(self):
        return self._goalkeeping

    def getHasBall(self):
        return self._hasBall

    def getHeading(self):
        return self._heading

    def getIndex(self):
        return self._index

    def getJumping(self):
        return self._jumping

    def getMaxSpeed(self):
        return Player._MAX_SPEED

    def getNumber(self):
        return self._number

    def getPassing(self):
        return self._passing

    def getPosition(self):
        return self._pos_cur

    def getPrecision(self, goal):
        distance = Helper.calculateDistance(self._pos_cur, goal)
        if distance >= self._MAX_STRENGTH:
            return 0
        else:
            return int(math.log(self._MAX_STRENGTH - distance, self._MAX_STRENGTH) * (self._MAX_PRECISION * self._precision / 100))

    def getProbsToRun(self):
        return Helper.calculateDistance(self._pos_cur, self._pos_att) / Helper.calculateDistance(self._pos_def, self._pos_att)

    def getShootingStrength(self):
        return self._strength * Player._MAX_STRENGTH / 100

    def getSpeed(self):
        return self._speed * Player._MAX_SPEED / 100

    def getTackling(self):
        return self._tackling

    def getTeam(self):
        return self._team

    def resetPosition(self, proportion = 0):
        self.setPosition([(proportion * (self._pos_att[0] - self._pos_def[0])) + self._pos_def[0], (proportion * (self._pos_att[1] - self._pos_def[1])) + self._pos_def[1]])

    def setHasBall(self, hasBall):
        self._hasBall = hasBall

    def setPosition(self, position):
        self._pos_cur = position

    def updatePosition(self, portion, seconds, hasBall = False):
        if self.getHasBall() == hasBall:
            destination = [(portion * (self._pos_att[0] - self._pos_def[0])) + self._pos_def[0], (portion * (self._pos_att[1] - self._pos_def[1])) + self._pos_def[1]]
            distance = math.sqrt(math.pow(self._pos_cur[0] - destination[0], 2) + math.pow(self._pos_cur[1] - destination[1], 2))
            speed = self.getSpeed()
            if self.getHasBall():
                speed *= 0.75

            if distance >= (speed * seconds * (self._speed / 100)):
                speed = (speed * seconds * (self._speed / 100))
                proportion = speed / distance
                speed_x = (destination[0] - self._pos_cur[0]) * proportion
                speed_y = (destination[1] - self._pos_cur[1]) * proportion
                self._pos_cur[0] += speed_x
                self._pos_cur[1] += speed_y
            else:
                self._pos_cur = destination