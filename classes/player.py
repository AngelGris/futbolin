#!/usr/bin/python3

import random
import math
from classes.helper import Helper

class Player:
    # Constants
    _MAX_PRECISION = 100.0
    _MAX_SPEED = 8.0 # Meters per second
    _MAX_STRENGTH = 50.0 # How long it can shoot (Meters)

    def __init__(self, team, id, index, pos_def, pos_att, max_stamina, match_type, category_id, db_connection):
        self._team = team
        self._id = id
        self._index = index
        self._pos_def = pos_def.copy()
        self._pos_att = pos_att.copy()
        self._pos_cur = pos_def.copy()
        self._max_stamina = float(max_stamina)
        self._hasBall = False

        if(int(id) > 0):
            if (match_type < 3):
                response = db_connection.query("SELECT * FROM `players` WHERE `id` = " + str(id) + " AND `recovery` = 0 LIMIT 1;", 1)
            else:
                response = db_connection.query("SELECT * FROM `players` WHERE `id` = " + str(id) + " AND `id` NOT IN (SELECT `player_id` FROM `player_cards` WHERE `category_id` = " + str(category_id) + " AND `suspension` > 0) AND `recovery` = 0 LIMIT 1;", 1)

            if (response):
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
                self._stamina = 0
                if match_type < 3:
                    self._stamina = 100
                else:
                    self._stamina = response['stamina'] # Remaining stamina

                self._injured = False
                self._cards = [0, 0]
                self._active = True
                self._present = True
            else:
                self._active = False
                self._present = False
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
        rate = self._max_stamina
        break_point = 40
        if self._stamina < break_point:
            rate = self._max_stamina / (1 + math.pow(math.exp(1) / 2.2, (break_point / 2) - self._stamina))

        return max(1, int(value * rate))

    def deactivate(self, injured = False):
        self._injured = injured
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

    def redCard(self):
        self._cards[1] = 1
        self._active = False
        return False

    def resetPositioning(self, proportion = 0):
        self.setPositioning([(proportion * (self._pos_att[0] - self._pos_def[0])) + self._pos_def[0], (proportion * (self._pos_att[1] - self._pos_def[1])) + self._pos_def[1]])

    def saveStatus(self, db_connection, category_id):
        if (self._present):
            experience = min(27, 7 + int(self._plays / 6))
            injury = 0
            recovery = 0
            if (self._injured):
                # Select type of injury
                print('lesionado')
                injuries = db_connection.query("SELECT `id`, `recovery`, `chance` FROM `injuries` ORDER BY `chance`;", 100)

                probs = {}
                total = 0
                for inj in injuries:
                    total += int(inj['chance'] * 100)
                    probs[inj['id']] = {'prob' : total, 'recovery' : inj['recovery']}

                r = random.randint(0, total)
                s = 1
                while(probs[s]['prob'] < r):
                    s += 1

                injury = s
                recovery = probs[s]['recovery']

                db_connection.query("UPDATE `players` SET `injury_id` = " + str(injury) + ", `recovery` = " + str(recovery + 1) + ", `experience` = `experience` + " + str(experience) + ", `stamina` = `stamina` - FLOOR((`stamina` - " + str(int(self._stamina)) + ") * 0.75) WHERE `id` = " + str(self._id) + " LIMIT 1;", 0)
            else:
                db_connection.query("UPDATE `players` SET `experience` = `experience` + " + str(experience) + ", `stamina` = `stamina` - FLOOR((`stamina` - " + str(int(self._stamina)) + ") * 0.75) WHERE `id` = " + str(self._id) + " LIMIT 1;", 0)

            cards = 0
            suspension = 0
            if (self._cards[1] == 1):
                suspension = 3
                cards = self._cards[0]
            elif (self._cards[0] == 2):
                suspension = 2
            elif (self._cards[0] == 1):
                cards = 1

            if (suspension > 0):
                db_connection.query('INSERT INTO `player_cards` (`player_id`, `category_id`, `cards`, `suspension_id`, `suspension`) VALUES (' + str(self._id) + ', ' + str(category_id) + ', ' + str(cards) + ', 2, ' + str(suspension) + ') ON DUPLICATE KEY UPDATE `cards` = `cards` + ' + str(cards) + ', `suspension_id` = 2, `suspension` = ' + str(suspension), 0)
            elif (cards > 0):
                db_connection.query('INSERT INTO `player_cards` (`player_id`, `category_id`, `cards`) VALUES (' + str(self._id) + ', ' + str(category_id) + ', ' + str(cards) + ') ON DUPLICATE KEY UPDATE `cards` = `cards` + ' + str(cards), 0)

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

    def yellowCard(self):
        self._cards[0] += 1
        if (self._cards[0] == 2):
            self._active = False
        return self._active