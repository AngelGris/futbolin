#!/usr/bin/python3

import math
from classes.helper import Helper

class Player:
    # Constants
    _MAX_PRECISION = 100.0
    _MAX_SPEED = 8.0 # Meters per second
    _MAX_STRENGTH = 50.0 # How long it can shoot (Meters)

    def __init__(self, team, id, index, pos_def, pos_att, match_type, db_connection):
        self._team = team
        self._id = id
        self._index = index
        self._pos_def = pos_def.copy()
        self._pos_att = pos_att.copy()
        self._pos_cur = pos_def.copy()
        self._hasBall = False

        if(int(id) > 0):
            response = db_connection.query("SELECT * FROM `players` WHERE `id` = " + str(id) + " LIMIT 1;", 1)
            self._number = response['number']
            self._name = response['first_name'] + " " + response['last_name']
            self._position = response['position']
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
            self._condition = response['condition'] # Physical condition to know how much stamina is affected
            if match_type < 3:
                self._stamina = 100
            else:
                self._stamina = response['stamina'] # Remaining stamina

            self._active = True
            self._present = True
        else:
            self._active = False
            self._present = False

        self._plays = 0 # Player's interventions in the match
        self._distance = 0 # Total distance run during the match

    def __str__(self):
        return self._short_name

    def _reduceStamina(self, value):
        if (self._stamina > value):
            self._stamina -= value
        else:
            self._stamina = 0

    def _staminaEffect(self, value):
        rate = 1
        break_point = 40
        inflexion = 28
        if self._stamina < break_point:
            if self._stamina < inflexion:
                rate = (math.pow(self._stamina, 2) / inflexion) / break_point
            else:
                rate = (break_point - (math.pow(break_point - self._stamina, 2) / (break_point - inflexion))) / break_point

        return max(1, int(value * rate))

    def deactivate(self):
        self._active = False

    def getCondition(self):
        return 0.6 / self._condition

    def getDefending(self):
        return self._staminaEffect(self._defending)

    def getDistance(self):
        return self._distance

    def getDribbling(self):
        return self._staminaEffect(self._dribbling)

    def getGoalKeeping(self):
        return self._staminaEffect(self._goalkeeping)

    def getHasBall(self):
        return self._hasBall

    def getHeading(self):
        return self._staminaEffect(self._heading)

    def getId(self):
        return self._id

    def getIndex(self):
        return self._index

    def getJumping(self):
        return self._staminaEffect(self._jumping)

    def getMaxStrength(self):
        return self._MAX_STRENGTH

    def getMaxSpeed(self):
        return Player._MAX_SPEED

    def getNumber(self):
        return self._number

    def getPassing(self):
        return self._staminaEffect(self._passing)

    def getPosition(self):
        return self._position

    def getPositioning(self):
        if (self.isActive()):
            return self._pos_cur
        else:
            return [1000, 1000]

    def getPositioningAtt(self):
        return self._pos_att

    def getPositioningDef(self):
        return self._pos_def

    def getPositioningDefensive(self):
        return self._pos_def

    def getPrecision(self, goal):
        return self.getProbsToShoot(Helper.calculateDistance(self._pos_cur, goal)) * self._precision

    def getProbsToRun(self):
        return Helper.calculateDistance(self._pos_cur, self._pos_att) / Helper.calculateDistance(self._pos_def, self._pos_att)

    def getProbsToShoot(self, distance):
        rate = 0
        correction_rate = 1.2
        if distance <= self._MAX_STRENGTH:
            if distance < (self.getShootingStrength() / correction_rate):
                rate = (self._MAX_STRENGTH - (math.pow(distance, 2) / (self.getShootingStrength() / correction_rate))) / self._MAX_STRENGTH
            else:
                rate = (math.pow(self._MAX_STRENGTH - distance, 2) / (self._MAX_STRENGTH - (self.getShootingStrength() / correction_rate))) / self._MAX_STRENGTH

        return rate

    def getShootingStrength(self):
        return self._staminaEffect(self._strength * Player._MAX_STRENGTH / 100)

    def getShortName(self):
        return self._short_name

    def getSpeed(self):
        speed = self._speed * Player._MAX_SPEED / 100
        if self.getHasBall():
                speed *= 0.75
        return self._staminaEffect(speed)

    def getStamina(self):
        return self._stamina

    def getTackling(self):
        return self._staminaEffect(self._tackling)

    def getTeam(self):
        return self._team

    def increasePlay(self, count = 1):
        self._plays += count
        self._reduceStamina(count * self.getCondition() * 5)

    def isActive(self):
        return (self._present and self._active)

    def isChangeable(self):
        return self._stamina < 40

    def isPresent(self):
        return self._present

    def resetPositioning(self, proportion = 0):
        self.setPositioning([(proportion * (self._pos_att[0] - self._pos_def[0])) + self._pos_def[0], (proportion * (self._pos_att[1] - self._pos_def[1])) + self._pos_def[1]])

    def saveStatus(self, db_connection):
        experience = min(27, 7 + int(self._plays / 6))
        db_connection.query("UPDATE `players` SET `experience` = `experience` + " + str(experience) + ", `stamina` = " + str(int(self._stamina)) + " WHERE `id` = " + str(self._id) + " LIMIT 1;", 0)

    def setHasBall(self, hasBall):
        self._hasBall = hasBall

    def setPositioning(self, positioning):
        self._pos_cur = positioning

    def substitution(self, pos_def, pos_att):
        self._pos_def = pos_def.copy()
        self._pos_att = pos_att.copy()
        self._pos_cur = pos_def.copy()

    def updatePositioning(self, portion, seconds, hasBall = False):
        if self.getHasBall() == hasBall and self.isActive():
            destination = [(portion * (self._pos_att[0] - self._pos_def[0])) + self._pos_def[0], (portion * (self._pos_att[1] - self._pos_def[1])) + self._pos_def[1]]
            distance = math.sqrt(math.pow(self._pos_cur[0] - destination[0], 2) + math.pow(self._pos_cur[1] - destination[1], 2))
            speed = self.getSpeed()

            if distance >= (speed * seconds * (self._speed / 100)):
                speed = (speed * seconds * (self._speed / 100))
                proportion = speed / distance
                speed_x = (destination[0] - self._pos_cur[0]) * proportion
                speed_y = (destination[1] - self._pos_cur[1]) * proportion
                self._pos_cur[0] += speed_x
                self._pos_cur[1] += speed_y

                self._reduceStamina(distance * self.getCondition())
                self._distance += distance
            else:
                distance = Helper.calculateDistance(self._pos_cur, destination)
                self._reduceStamina(distance * self.getCondition())
                self._distance += distance
                self._pos_cur = destination