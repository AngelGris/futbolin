#!/usr/bin/python3

# Imports
from classes.field import Field
import classes.ball as bal
import classes.mysql as mysql
import classes.stats as stats
import classes.team as team
import math
import random

class Simulator:
    def __init__(self, local_id, visit_id, match_type, debug_level, output_file = '', category_id = 0, assistance = 0, incomes = 0):
        # DB connection
        self._db_connection = mysql.Mysql()

        # Configuration
        self._time_step = 2.0

        # Initiate instance values
        self._ball = bal.Ball([45.0, 60.0])
        self._field_size = Field.getSize()
        self._play_type = 1
        self._local_id = local_id
        self._visit_id = visit_id
        self._match_type = match_type
        self._debug_level = debug_level
        self._output_file = output_file
        self._category_id = category_id
        self._assistance = assistance
        self._incomes = incomes

    def _execCornerKick(self, possesion_team):
        # Corner kick
        r = random.randint(0, 1)
        if (r == 0):
            # Left corner
            if (possesion_team == 0):
                self._ball.setPositioning([0, self._field_size[1]])
            else:
                self._ball.setPositioning([self._field_size[0], 0])
        else:
            # Right corner
            if (possesion_team == 0):
                self._ball.setPositioning([self._field_size[0], self._field_size[1]])
            else:
                self._ball.setPositioning([0, 0])

        # Get closest player to corner
        self._teams[possesion_team].resetPositionings(1)
        self._ball.setPlayer(self._teams[possesion_team].getPlayerCorner(self._ball.getPositioning()))

        self._statistics.execCornerKick(possesion_team, self._ball.getPlayer())
        time_update = self._statistics.increaseTime(self._time_step / 2)

        # Probs
        # 0 = Goalkeeper takes the ball
        # 1 = Defender heads away
        # 2 = Heading out
        # 3 = Heading on goal successfully defended by the goalkeeper
        # 4 = Heading on goal to the corner by the goalkeeper
        # 5 = Heading on goal poorly defended GOAL!
        # 6 = Heading on goal rejected by defender to corner
        # 7 = GOAL!
        base = 1000
        rival_team = (possesion_team + 1) % 2
        header_attacking = self._teams[possesion_team].getHeadingPlayer(self._ball)
        header_defending = self._teams[rival_team].getHeadingPlayer(self._ball)
        goalkeeper = self._teams[rival_team].getGoalkeeper()
        goalkeeper_rate = goalkeeper.getGoalKeeping() / 100
        probs = [0, 0, 0, 0, 0, 0, 0, 0]
        probs[0] = base * (goalkeeper.getJumping() / 200)
        probs[1] = base * (header_defending[1] / (header_defending[1] + header_attacking[1]))
        base *= (header_attacking[1] / (header_defending[1] + header_attacking[1]))
        probs[2] = base * (1 - header_attacking[2])
        probs[3] = base * header_attacking[2] * (1 - header_attacking[2]) * math.pow(goalkeeper_rate, 2)
        probs[4] = base * header_attacking[2] * (1 - header_attacking[2]) * goalkeeper_rate * (1 - goalkeeper_rate)
        probs[5] = base * header_attacking[2] * (1 - header_attacking[2]) * math.pow(1 - goalkeeper_rate, 2) * (1 - header_defending[2])
        probs[6] = base * header_attacking[2] * (1 - header_attacking[2]) * math.pow(1 - goalkeeper_rate, 2) * header_defending[2]
        probs[7] = base * math.pow(header_attacking[2], 2)

        prob = self._randomProbs(probs)
        if (prob == 0):
            # Goalkeeper takes the ball
            self._statistics.execGoalkeeperCutsCrossing(rival_team, goalkeeper)
            self._ball.setPlayer(goalkeeper)
            time_update += self._statistics.increaseTime(self._time_step * 2)
            self._play_type = 5
        elif (prob == 1):
            # Defender heads away
            self._statistics.execDefendingHeader(rival_team, self._teams[rival_team].getPlayer(header_defending[0]))
            self._ball.setPlayer(self._teams[rival_team].getPlayer(header_defending[0]))
            time_update += self._statistics.increaseTime(self._time_step)
            self._play_type = 3
        elif (prob == 2):
            # Heading out
            self._statistics.execHeaderAway(possesion_team, self._teams[possesion_team].getPlayer(header_attacking[0]))
            self._ball.setPlayer(goalkeeper)
            time_update += self._statistics.increaseTime(self._time_step * 2)
            self._play_type = 5
        else:
            # Heading on target
            self._statistics.execHeaderOnTarget(possesion_team, self._teams[possesion_team].getPlayer(header_attacking[0]))
            if (prob == 3):
                # Goalkeeper keeps the ball
                self._statistics.execGoalkeeperDefense(rival_team, goalkeeper)
                self._ball.setPlayer(goalkeeper)
                self._play_type = 0
            elif (prob == 4):
                # Corner kick
                self._statistics.execGoalkeeperDefenseToCorner(rival_team, goalkeeper)
                self._ball.setPlayer(self._teams[possesion_team].getPlayerCorner())
                self._play_type = 6
            elif (prob == 5):
                # Poor defense GOAL!
                self._statistics.execGoalkeeperPoorDefense(possesion_team, self._teams[possesion_team].getPlayer(header_attacking[0]), goalkeeper)
                self._ball.setPlayer(goalkeeper)
                time_update += self._statistics.increaseTime(self._time_step * 3)
                self._play_type = 1
            elif (prob == 6):
                # Cleared by defender
                self._statistics.execDefenseClear(rival_team, self._teams[rival_team].getPlayer(header_defending[0]))
                self._ball.setPlayer(self._teams[possesion_team].getPlayerCorner())
                time_update += self._statistics.increaseTime(self._time_step * 2)
                self._play_type = 6
            else:
                self._statistics.execScore(possesion_team, self._teams[possesion_team].getPlayer(header_attacking[0]))
                self._ball.setPlayer(goalkeeper)
                time_update += self._statistics.increaseTime(self._time_step * 3)
                self._play_type = 1

        return time_update + self._statistics.increaseTime(self._time_step)

    def _execDecision(self, possesion_team, possesion_player, last_kickoff):
        rival_team = (possesion_team + 1) % 2
        closest_friend = self._teams[possesion_team].getClosestPlayer(self._teams[possesion_team].getPlayer(possesion_player).getPositioning(), possesion_player)
        closest_rival = self._teams[rival_team].getClosestPlayer(self._teams[possesion_team].getPlayer(possesion_player).getPositioning())
        goal_distance = math.hypot(self._ball.getPositioning()[0] - Field.getGoalPositioning(rival_team)[0], self._ball.getPositioning()[1] - Field.getGoalPositioning(rival_team)[1])
        self._play_type = self._teams[possesion_team].getNextPlay(possesion_player, closest_friend, closest_rival, goal_distance, last_kickoff)
        return self._statistics.increaseTime(self._time_step / 2)

    def _execDribbling(self, possesion_team, possesion_player):
        # Dribbling
        time_update = self._statistics.increaseTime(self._time_step)
        rival_team = (possesion_team + 1) % 2
        closest_rival = self._teams[rival_team].getClosestPlayer(self._teams[possesion_team].getPlayer(possesion_player).getPositioning())

        # Probs
        #  0 = Successful dribbling
        #  1 = Successful tackling
        #  2 = Facing off (try to dribble again)
        #  3 = Foul, no injury, no card
        #  4 = Foul, no injury, yellow card
        #  5 = Foul, no injury, red card
        #  6 = Foul, injury, no card
        #  7 = Foul, injury, yellow card
        #  8 = Foul, injury, red card
        #  9 = Penalty, no injury, no card
        # 10 = Penalty, no injury, yellow card
        # 11 = Penalty, no injury, red card
        # 12 = Penalty, injury, no card
        # 13 = Penalty, injury, yellow card
        # 14 = Penalty, injury, red card
        dribbling = self._teams[possesion_team].getPlayer(possesion_player).getDribbling() / 100
        tackling = min(1, self._teams[rival_team].getPlayer(closest_rival[0]).getTackling() / 85)
        stamina = min(1, self._teams[possesion_team].getPlayer(possesion_player).getStamina() / 70)
        ball_position = self._ball.getPositioning()
        goal_position = Field.getGoalPositioning(rival_team)
        goal_distance = math.hypot(ball_position[0] - goal_position[0], ball_position[1] - goal_position[1])
        penalty = min(1, self._teams[possesion_team].getPlayer(possesion_player).getProbsToShoot(goal_distance) * 50)
        yellow_card = 0.25
        red_card = 0.01
        base = 1000
        probs = [0 for x in range(15)]
        probs[0] = base * dribbling
        probs[1] = base * (1 - dribbling) * math.pow(tackling, 2)
        probs[2] = base * (1 - dribbling) * (tackling * (1 - tackling) * 2)
        foul = base * (1 - dribbling) * math.pow(1 - tackling, 2) * (1 - penalty)
        probs[3] = foul * stamina * (1 - yellow_card - red_card)
        probs[4] = foul * stamina * yellow_card
        probs[5] = foul * stamina * red_card
        probs[6] = foul * (1 - stamina) * (1 - yellow_card - red_card)
        probs[7] = foul * (1 - stamina) * yellow_card
        probs[8] = foul * (1 - stamina) * red_card
        penalty = base * (1 - dribbling) * math.pow(1 - tackling, 2) * penalty
        probs[9] = penalty * stamina * (1 - yellow_card - red_card)
        probs[10] = penalty * stamina * yellow_card
        probs[11] = penalty * stamina * red_card
        probs[12] = penalty * (1 - stamina) * (1 - yellow_card - red_card)
        probs[13] = penalty * (1 - stamina) * yellow_card
        probs[14] = penalty * (1 - stamina) * red_card

        prob = self._randomProbs(probs)
        if (prob == 0):
            # Dribbling succeeded
            self._statistics.execDribbling(possesion_team, self._teams[possesion_team].getPlayer(possesion_player), self._teams[rival_team].getPlayer(closest_rival[0]))
            self._play_type = 0
        elif (prob == 1):
            # Tackling succeeded
            self._statistics.execTackling(rival_team, self._teams[possesion_team].getPlayer(possesion_player), self._teams[rival_team].getPlayer(closest_rival[0]))
            self._ball.setPlayer(self._teams[rival_team].getPlayer(closest_rival[0]))
            self._play_type = 0
        elif (prob == 2):
            # Face defender (try dribbling again)
            self._statistics.execFacingDefender(possesion_team, self._teams[possesion_team].getPlayer(possesion_player), self._teams[rival_team].getPlayer(closest_rival[0]))
        else:
            # Foul
            if (prob <= 8):
                self._statistics.execFoul(possesion_team, self._teams[possesion_team].getPlayer(possesion_player), self._teams[rival_team].getPlayer(closest_rival[0]))
                time_update = self._statistics.increaseTime(self._time_step * 2)
                self._play_type = 8
            else:
                self._statistics.execPenalty(possesion_team, self._teams[possesion_team].getPlayer(possesion_player), self._teams[rival_team].getPlayer(closest_rival[0]))
                time_update = self._statistics.increaseTime(self._time_step * 5)
                self._play_type = 9

            if (prob in [4, 7, 10, 13]):
                # Yellow card
                self._teams[rival_team].yellowCard(self._statistics, closest_rival[0])
            elif (prob in [5, 8, 11, 14]):
                # Red card
                self._teams[rival_team].redCard(self._statistics, closest_rival[0])

            if (prob in [6, 7, 8, 12, 13, 14]):
                # injury
                time_update += self._statistics.increaseTime(self._time_step / 2)
                self._teams[possesion_team].playerInjured(self._statistics, possesion_player)

        return time_update

    def _execFreeKick(self, possesion_team):
        rival_team = (possesion_team + 1) % 2
        self._teams[possesion_team].resetPositionings(1)
        self._teams[rival_team].resetPositionings(0)
        shooter = self._teams[possesion_team].getClosestPlayer(self._ball.getPositioning())
        self._ball.setPlayer(self._teams[possesion_team].getPlayer(shooter[0]))
        ball_position = self._ball.getPlayer().getPositioning()
        goal_position = Field.getGoalPositioning(rival_team)
        goal_distance = math.hypot(ball_position[0] - goal_position[0], ball_position[1] - goal_position[1])

        # Probs
        # 0 = Passing
        # 1 = Centering, goalkeeper takes the ball
        # 2 = Centering, defender heads away
        # 3 = Centering, heading out
        # 4 = Centering, heading on goal successfully defended by the goalkeeper
        # 5 = Centering, heading on goal to the corner by the goalkeeper
        # 6 = Centering, heading on goal poorly defended GOAL!
        # 7 = Centering, heading on goal rejected by defender
        # 8 = Centering, headed and scored GOAL!
        # 9 = Shoot on goal, away
        # 10 = Shoot on goal, successfuly defended by goalkeeper
        # 11 = Shoot on goal, to the corner by the goalkeeper
        # 12 = Shoot on goal, GOAL!
        base = 1000
        passing = self._teams[possesion_team].getPlayer(shooter[0]).getPassing() / 100
        shooting = self._teams[possesion_team].getPlayer(shooter[0]).getProbsToShoot(goal_distance)
        centering = base * (1 - shooting) * (1 - passing)
        precision = self._teams[possesion_team].getPlayer(shooter[0]).getPrecision(goal_position) / 100
        header_attacking = self._teams[possesion_team].getHeadingPlayer(self._ball)
        header_defending = self._teams[rival_team].getHeadingPlayer(self._ball)
        goalkeeper = self._teams[rival_team].getGoalkeeper()
        goalkeeper_rate = goalkeeper.getGoalKeeping() / 100
        probs = [0 for x in range(13)]
        probs[0] = base * (1 - shooting)
        probs[1] = centering * (goalkeeper.getJumping() / 20)
        probs[2] = centering * (header_defending[1] / (header_defending[1] + header_attacking[1]))
        centering *= (header_attacking[1] / (header_defending[1] + header_attacking[1]))
        probs[3] = centering * (1 - header_attacking[2])
        probs[4] = centering * header_attacking[2] * (1 - header_attacking[2]) * math.pow(goalkeeper_rate, 2)
        probs[5] = centering * header_attacking[2] * (1 - header_attacking[2]) * goalkeeper_rate * (1 - goalkeeper_rate)
        probs[6] = centering * header_attacking[2] * (1 - header_attacking[2]) * math.pow(1 - goalkeeper_rate, 2) * (1 - header_defending[2])
        probs[7] = centering * header_attacking[2] * (1 - header_attacking[2]) * math.pow(1 - goalkeeper_rate, 2) * header_defending[2]
        probs[8] = centering * math.pow(header_attacking[2], 2)
        shooting = base * shooting * (1 - passing)
        probs[9] = shooting * (1 - precision)
        probs[10] = shooting * precision * math.pow(goalkeeper_rate, 2)
        probs[11] = shooting * precision * goalkeeper_rate * (1 - goalkeeper_rate)
        probs[12] = shooting * precision * (1 - goalkeeper_rate)

        prob = self._randomProbs(probs)
        time_update = self._statistics.increaseTime(self._time_step)
        if (prob == 0):
            # Passing
            self._statistics.execFreekick(possesion_team, self._teams[possesion_team].getPlayer(shooter[0]))
            time_update += self._statistics.increaseTime(self._time_step)
            self._play_type = 3
        elif (prob <= 8):
            # Centering
            self._statistics.execFreekickCentering(possesion_team, self._teams[possesion_team].getPlayer(shooter[0]))
            time_update += self._statistics.increaseTime(self._time_step * 2)

            if (prob == 1):
                # Centering, goalkeeper takes the ball
                self._statistics.execGoalkeeperCutsCrossing(rival_team, goalkeeper)
                self._ball.setPlayer(self._teams[rival_team].getGoalkeeper())
                time_update += self._statistics.increaseTime(self._time_step * 2)
                self._play_type = 5
            elif (prob == 2):
                # Centering, defender heads away
                self._statistics.execDefendingHeader(rival_team, self._teams[rival_team].getPlayer(header_defending[0]))
                self._ball.setPlayer(self._teams[rival_team].getPlayer(header_defending[0]))
                time_update += self._statistics.increaseTime(self._time_step)
                self._play_type = 3
            elif (prob == 3):
                # Centering, heading out
                self._statistics.execHeaderAway(possesion_team, self._teams[possesion_team].getPlayer(header_attacking[0]))
                self._ball.setPlayer(goalkeeper)
                time_update += self._statistics.increaseTime(self._time_step)
                self._play_type = 5
            elif (prob <= 8):
                self._statistics.execHeaderOnTarget(possesion_team, self._teams[possesion_team].getPlayer(header_attacking[0]))

                if (prob == 4):
                    # Centering, heading on goal successfully defended by the goalkeeper
                    self._statistics.execGoalkeeperDefense(rival_team, goalkeeper)
                    self._ball.setPlayer(goalkeeper)
                    time_update += self._statistics.increaseTime(self._time_step)
                    self._play_type = 0
                elif (prob == 5):
                    # Centering, heading on goal to the corner by the goalkeeper
                    self._statistics.execGoalkeeperDefenseToCorner(rival_team, goalkeeper)
                    self._ball.setPlayer(self._teams[possesion_team].getPlayerCorner())
                    time_update += self._statistics.increaseTime(self._time_step)
                    self._play_type = 6
                elif (prob == 6):
                    # Centering, heading on goal poorly defended GOAL!
                    self._statistics.execGoalkeeperPoorDefense(possesion_team, self._teams[possesion_team].getPlayer(header_attacking[0]), goalkeeper)
                    self._ball.setPlayer(self._teams[rival_team].getGoalkeeper())
                    time_update += self._statistics.increaseTime(self._time_step * 5)
                    self._play_type = 1
                elif (prob == 7):
                    # Centering, heading on goal rejected by defender
                    self._statistics.execDefenseClear(rival_team, self._teams[rival_team].getPlayer(header_defending[0]))
                    self._ball.setPlayer(self._teams[possesion_team].getPlayerCorner())
                    time_update += self._statistics.increaseTime(self._time_step * 2)
                    self._play_type = 6
                elif (prob == 8):
                    # Centering, headed and scored GOAL!
                    self._statistics.execScore(possesion_team, self._teams[possesion_team].getPlayer(header_attacking[0]))
                    self._ball.setPlayer(goalkeeper)
                    time_update += self._statistics.increaseTime(self._time_step * 3)
                    self._play_type = 1
        else:
            # Shoot on goal
            self._statistics.execFreekickOnGoal(possesion_team, self._teams[possesion_team].getPlayer(shooter[0]))
            time_update += self._statistics.increaseTime(self._time_step)

            if (prob == 9):
                # Shoot on goal, away
                self._statistics.execShootAway(possesion_team, self._teams[possesion_team].getPlayer(shooter[0]))
                self._ball.setPlayer(goalkeeper)
                time_update += self._statistics.increaseTime(self._time_step)
                self._play_type = 5
            elif (prob == 10):
                # Shoot on goal, successfuly defended by goalkeeper
                self._statistics.execGoalkeeperDefense(rival_team, goalkeeper)
                self._ball.setPlayer(goalkeeper)
                time_update += self._statistics.increaseTime(self._time_step)
                self._play_type = 0
            elif (prob == 11):
                # Shoot on goal, to the corner by the goalkeeper
                self._statistics.execGoalkeeperDefenseToCorner(rival_team, goalkeeper)
                self._ball.setPlayer(self._teams[possesion_team].getPlayerCorner())
                time_update += self._statistics.increaseTime(self._time_step)
                self._play_type = 6
            elif (prob == 12):
                # Shoot on goal, GOAL!
                self._statistics.execFreekickScore(possesion_team, self._teams[possesion_team].getPlayer(shooter[0]))
                self._ball.setPlayer(goalkeeper)
                time_update += self._statistics.increaseTime(self._time_step * 3)
                self._play_type = 1

        return time_update

    def _execGoalKick(self, possesion_team, time_half):
        self._teams[0].resetPositionings(0.5)
        self._teams[1].resetPositionings(0.5)
        goalkeeper = self._teams[self._ball.getTeam()].getGoalkeeper()

        if self._ball.getTeam() == 0:
            self._ball.setPositioning([self._field_size[0] / 2, 5.5])
        else:
            self._ball.setPositioning([self._field_size[0] / 2, self._field_size[1] - 5.5])

        time_update = self._statistics.increaseTime(self._time_step * 2)
        self._statistics.execGoalKick(self._ball.getTeam(), goalkeeper)
        self._play_type = 3

        # After minute 60 winning goalkeeper starts loosing time and can take a yellow card
        goals = self._statistics.getGoals()
        rival_team = (possesion_team + 1) % 2
        if (self._statistics.getTime() > 3600 and not goalkeeper.hasYellowCard() and goals[possesion_team] > goals[rival_team]):
            time_update += self._statistics.increaseTime(self._time_step * 3)
            if (random.randint(0,10) == 0):
                self._teams[possesion_team].goalkeeperYellowCard(self._statistics, goalkeeper.getIndex())

        return time_update

    def _execKickoff(self, possesion_team):
        self._teams[0].resetPositionings()
        self._teams[1].resetPositionings()
        self._ball.setPlayer(None)
        self._ball.setPositioning([45.0, 60.0])
        kickoff_player = self._teams[possesion_team].getClosestPlayer(self._ball.getPositioning())
        possesion_player = kickoff_player[0]
        self._ball.setPlayer(self._teams[possesion_team].getPlayer(kickoff_player[0]), False);
        self._teams[possesion_team].setPlayerPositioning(self._ball.getPlayer().getIndex(), self._ball.getPositioning())

        pass_to = self._teams[possesion_team].getPass(possesion_player)
        self._ball.setPlayer(self._teams[possesion_team].getPlayer(pass_to))

        self._statistics.execKickoff(possesion_team, self._teams[possesion_team].getPlayer(possesion_player), self._teams[possesion_team].getPlayer(pass_to))
        self._play_type = 0

        return self._statistics.increaseTime(self._time_step / 2)

    def _execPassing(self, possesion_team, possesion_player):
        rival_team = (possesion_team + 1) % 2
        pass_to = self._teams[possesion_team].getPass(possesion_player, True)
        closest_rival = self._teams[rival_team].getClosestPlayer(self._teams[possesion_team].getPlayer(possesion_player).getPositioning())
        probs = [self._teams[possesion_team].getPlayer(possesion_player).getPassing(), 0] # 0 = passing, 1 = interecption
        if closest_rival[1] > (closest_rival[2] * 2):
            # Rival too far
            probs[1] = 0
        elif closest_rival[1] > closest_rival[2]:
            # Rival closer
            probs[1] = int(self._teams[rival_team].getPlayer(closest_rival[0]).getDefending() * 0.5)
        else:
            # Rival is here
            probs[1] = self._teams[rival_team].getPlayer(closest_rival[0]).getDefending()

        total = probs[0] + probs[1]
        probs[0] = int(probs[0] * 100 / total)
        probs[1] = 100

        r = random.randint(0, 100)
        s = 0
        while(probs[s] < r):
            s += 1

        if s == 0:
            # Passing successfull
            self._statistics.execPassing(possesion_team, self._teams[possesion_team].getPlayer(possesion_player), self._teams[possesion_team].getPlayer(pass_to))
            self._ball.setPlayer(self._teams[possesion_team].getPlayer(pass_to))
        else:
            # Pass intercepted
            self._statistics.execInterception(rival_team, self._teams[possesion_team].getPlayer(possesion_player), self._teams[rival_team].getPlayer(closest_rival[0]))
            self._ball.setPlayer(self._teams[rival_team].getPlayer(closest_rival[0]))

        self._play_type = 0
        return self._statistics.increaseTime(self._time_step)

    def _execPenalty(self, possesion_team):
        rival_team = (possesion_team + 1) % 2
        self._teams[possesion_team].resetPositionings(1)
        self._teams[rival_team].resetPositionings(0)
        goal_position = Field.getGoalPositioning(rival_team)
        if (possesion_team == 0):
            self._ball.setPositioning([goal_position[0], goal_position[1] - 12])
        else:
            self._ball.setPositioning([goal_position[0], goal_position[1] + 12])
        shooter = self._teams[possesion_team].getPenaltyShooter(self._ball)
        self._ball.setPlayer(self._teams[possesion_team].getPlayer(shooter[0]))

        # Probs
        # 0 = Shoot away
        # 1 = Shoot on goal succesfully defending
        # 2 = Shoot on goal sent to the corner
        # 3 = Shoot on goal poorly defended GOAL!!!!
        # 4 = Shoot on goal not defended GOAL!!!
        base = 100
        precision = shooter[1] / 120
        goalkeeping = self._teams[rival_team].getGoalkeeper().getGoalKeeping() / 100
        probs = [0, 0, 0, 0, 0]
        probs[0] = base * (1 - precision)
        probs[1] = base * precision * math.pow(goalkeeping, 2)
        probs[2] = base * precision * math.pow(goalkeeping, 2) * (1 - goalkeeping)
        probs[3] = base * precision * goalkeeping * math.pow(1 - goalkeeping, 2)
        probs[4] = base * precision * (1 - goalkeeping)

        prob = self._randomProbs(probs)
        if (prob == 0):
            # Shoot away
            time_update = self._statistics.increaseTime(self._time_step * 3)
            self._statistics.execShootPenaltyAway(possesion_team, self._teams[possesion_team].getPlayer(shooter[0]))
            self._ball.setPlayer(self._teams[rival_team].getGoalkeeper())
            self._play_type = 5
        else:
            # Shoot on goal
            self._statistics.execShootPenaltyOnGoal(possesion_team, self._teams[possesion_team].getPlayer(shooter[0]))
            time_update = self._statistics.increaseTime(self._time_step)

            if (prob == 1):
                # Shoot on goal succesfully defending
                self._statistics.execGoalkeeperDefense(rival_team, self._teams[rival_team].getGoalkeeper())
                self._ball.setPlayer(self._teams[rival_team].getGoalkeeper())
                self._play_type = 0
            elif (prob == 2):
                # Shoot on goal sent to the corner
                self._statistics.execGoalkeeperDefenseToCorner(rival_team, self._teams[rival_team].getGoalkeeper())
                self._ball.setPlayer(self._teams[possesion_team].getPlayerCorner())
                time_update += self._statistics.increaseTime(self._time_step)
                self._play_type = 6
            elif (prob == 3):
                # Shoot on goal poorly defended GOAL!!!!
                self._statistics.execGoalkeeperPoorDefense(possesion_team, self._teams[possesion_team].getPlayer(shooter[0]), self._teams[rival_team].getGoalkeeper())
                self._ball.setPlayer(self._teams[rival_team].getGoalkeeper())
                time_update += self._statistics.increaseTime(self._time_step * 5)
                self._play_type = 1
            else:
                # Shoot on goal not defended GOAL!!!
                self._statistics.execScore(possesion_team, self._teams[possesion_team].getPlayer(shooter[0]))
                self._ball.setPlayer(self._teams[rival_team].getGoalkeeper())
                time_update += self._statistics.increaseTime(self._time_step * 5)
                self._play_type = 1

        return time_update

    def _execRun(self, possesion_team, possesion_player):
        self._teams[possesion_team].getPlayer(possesion_player).updatePositioning(1, self._time_step, True)

        self._statistics.execRun(possesion_team, self._teams[possesion_team].getPlayer(possesion_player))

        self._play_type = 0
        return self._statistics.increaseTime(self._time_step)

    def _execSubstitutions(self):
        self._teams[0].checkSubstitutions(self._statistics)
        self._teams[1].checkSubstitutions(self._statistics)

    def _execShooting(self, possesion_team, possesion_player):
        rival_team = (possesion_team + 1) % 2
        # Probs
        # 0 = Shoot away
        # 1 = Shoot on goal succesfully defending
        # 2 = Shoot on goal sent to the corner
        # 3 = Shoot on goal poorly defended GOAL!!!!
        # 4 = Shoot on goal not defended GOAL!!!
        base = 100
        precision = self._teams[possesion_team].getPlayer(possesion_player).getPrecision(Field.getGoalPositioning(rival_team)) / 130
        goalkeeping = self._teams[rival_team].getGoalkeeper().getGoalKeeping() / 150
        probs = [0, 0, 0, 0, 0]
        probs[0] = base * (1 - precision)
        probs[1] = base * precision * math.pow(goalkeeping, 2)
        probs[2] = base * precision * math.pow(goalkeeping, 2) * (1 - goalkeeping)
        probs[3] = base * precision * goalkeeping * math.pow(1 - goalkeeping, 2)
        probs[4] = base * precision * (1 - goalkeeping)

        prob = self._randomProbs(probs)
        if (prob == 0):
            # Shoot away
            self._statistics.execShootAway(possesion_team, self._teams[possesion_team].getPlayer(possesion_player))
            self._ball.setPlayer(self._teams[rival_team].getGoalkeeper())
            time_update = self._statistics.increaseTime(self._time_step)
            self._play_type = 5
        else:
            # Shoot on goal
            self._statistics.execShootOnGoal(possesion_team, self._teams[possesion_team].getPlayer(possesion_player))
            time_update = self._statistics.increaseTime(self._time_step)

            if (prob == 1):
                # Shoot on goal succesfully defending
                self._statistics.execGoalkeeperDefense(rival_team, self._teams[rival_team].getGoalkeeper())
                self._ball.setPlayer(self._teams[rival_team].getGoalkeeper())
                self._play_type = 0
            elif (prob == 2):
                # Shoot on goal sent to the corner
                self._statistics.execGoalkeeperDefenseToCorner(rival_team, self._teams[rival_team].getGoalkeeper())
                self._ball.setPlayer(self._teams[possesion_team].getPlayerCorner())
                time_update += self._statistics.increaseTime(self._time_step)
                self._play_type = 6
            elif (prob == 3):
                # Shoot on goal poorly defended GOAL!!!!
                self._statistics.execGoalkeeperPoorDefense(possesion_team, self._teams[possesion_team].getPlayer(possesion_player), self._teams[rival_team].getGoalkeeper())
                self._ball.setPlayer(self._teams[rival_team].getGoalkeeper())
                time_update += self._statistics.increaseTime(self._time_step * 5)
                self._play_type = 1
            else:
                # Shoot on goal not defended GOAL!!!
                self._statistics.execScore(possesion_team, self._teams[possesion_team].getPlayer(possesion_player))
                self._ball.setPlayer(self._teams[rival_team].getGoalkeeper())
                time_update += self._statistics.increaseTime(self._time_step * 5)
                self._play_type = 1

        return time_update

    def _randomProbs(self, probs):
        probs[0] = round(probs[0])
        # Round numbers and relative probs
        for p in range(1, len(probs)):
            probs[p] = round(probs[p]) + probs[p - 1]

        # Random number
        r = random.randint(1, probs[-1])

        prob = 0
        while (prob < len(probs) and r > probs[prob]):
            prob += 1

        return min(prob, len(probs) - 1)

    def simulate(self):
        # Initiate method values
        local_max_stamina = 1
        visit_max_stamina = 1
        time_total = 2700
        time_half = 1

        # Calculate max stamina for official matches
        if (self._match_type == 3):
            if (self._local_id > 26):
                local_stamina = self._db_connection.query('SELECT AVG(`stamina`) AS `stamina` FROM `players` WHERE `team_id` = ' + str(self._local_id) + ' AND `deleted_at` IS NULL', 1)
            else:
                local_stamina = {'stamina' : 100}

            if (self._visit_id > 26):
                visit_stamina = self._db_connection.query('SELECT AVG(`stamina`) AS `stamina` FROM `players` WHERE `team_id` = ' + str(self._visit_id) + ' AND `deleted_at` IS NULL', 1)
            else:
                visit_stamina = {'stamina' : 100}

            if local_stamina['stamina'] > visit_stamina['stamina']:
                visit_max_stamina = visit_stamina['stamina'] / local_stamina['stamina']
            elif visit_stamina['stamina'] > local_stamina['stamina']:
                local_max_stamina = local_stamina['stamina'] / visit_stamina['stamina']
            del local_stamina
            del visit_stamina

        # Load teams
        self._teams = [team.Team(self._local_id, self._field_size, self._match_type, local_max_stamina, self._category_id, self._db_connection, True), team.Team(self._visit_id, self._field_size, self._match_type, visit_max_stamina, self._category_id, self._db_connection, False)]

        # Instantiate statistics object
        self._statistics = stats.Stats(self._teams[0], self._teams[1], self._match_type, self._debug_level, self._output_file, self._category_id)

        # Suspend Match if one of the teams in not enabled to play
        if (not self._teams[0].getEnabled() or not self._teams[1].getEnabled()):
            if (self._teams[0].getEnabled()):
                self._statistics.execSuspendMatch(0)
            elif (self._teams[1].getEnabled()):
                self._statistics.execSuspendMatch(1)
            else:
                self._statistics.execSuspendMatch(None)

            if (self._output_file != ''):
                self._statistics.writeOutput(db_connection)

            exit()

        # Play the game!
        kickoff_team = random.randint(0,1)

        while(time_half <= 2):
            print('*** COMIENZO ' + ('PRIMER' if time_half == 1 else 'SEGUNDO') + ' TIEMPO ***')
            # Substitutions
            if time_half == 2:
                self._teams[0].checkSubstitutions(self._statistics)
                self._teams[1].checkSubstitutions(self._statistics)

            self._teams[0].resetPositionings()
            self._teams[1].resetPositionings()
            self._ball.setPositioning([45.0, 60.0])
            kickoff_player = self._teams[kickoff_team].getClosestPlayer(self._ball.getPositioning())
            last_kickoff = 0
            self._ball.setPlayer(self._teams[kickoff_team].getPlayer(kickoff_player[0]), False);
            self._teams[kickoff_team].setPlayerPositioning(self._ball.getPlayer().getIndex(), self._ball.getPositioning())

            while(self._statistics.getTime() <= time_total):
                time_update = 0
                possesion_team = self._ball.getTeam()
                possesion_player = self._ball.getPlayer().getIndex()
                #  0 = Make a decision
                #  1 = Kick off
                #  2 = Run with the ball
                #  3 = Pass the ball
                #  4 = Shoot to the goal
                #  5 = Goal kick
                #  6 = Corner kick
                #  7 = Dribbling
                #  8 = Free kick
                #  9 = Penalty kick
                if self._play_type == 1:
                    # Kick off
                    last_kickoff = 0
                    time_update += self._execKickoff(possesion_team)
                elif self._play_type == 2:
                    # Run with the ball
                    time_update += self._execRun(possesion_team, possesion_player)
                elif self._play_type == 3:
                    # Pass the ball
                    time_update += self._execPassing(possesion_team, possesion_player)
                elif self._play_type == 4:
                    # Shoot to the goal
                    time_update += self._execShooting(possesion_team, possesion_player)
                elif self._play_type == 5:
                    # Substitutions
                    if time_half == 2:
                        self._execSubstitutions()

                        # Set player again in case the goalkeepers was replaced
                        self._ball.setPlayer(self._teams[possesion_team].getGoalkeeper())

                    # Goal kick
                    time_update += self._execGoalKick(possesion_team, time_half)
                elif self._play_type == 6:
                    # Substitutions
                    if time_half == 2:
                        self._execSubstitutions()

                    # Corner kick
                    time_update += self._execCornerKick(possesion_team)
                elif self._play_type == 7:
                    # Dribbling
                    time_update += self._execDribbling(possesion_team, possesion_player)
                elif self._play_type == 8:
                    # Substitutions
                    if time_half == 2:
                        self._execSubstitutions()

                    # Free kick
                    time_update += self._execFreeKick(possesion_team)
                elif self._play_type == 9:
                    # Substitutions
                    if time_half == 2:
                        self._execSubstitutions()

                    # Penalty kick
                    time_update += self._execPenalty(possesion_team)
                else:
                    if (self._play_type > 0):
                        print('Play', self._play_type)
                        exit()
                    # Make a decision
                    time_update += self._execDecision(possesion_team, possesion_player, last_kickoff)

                self._teams[0].updatePositionings(self._field_size, self._ball, time_update)
                self._teams[1].updatePositionings(self._field_size, self._ball, time_update)
                last_kickoff += time_update

            print('*** FINAL ' + ('PRIMER' if time_half == 1 else 'SEGUNDO') + ' TIEMPO ***')

            time_half += 1
            time_total *= 2
            kickoff_team = (kickoff_team + 1) % 2
            play_type = 1

        print('')
        print(self._statistics)
        print('')

        if (self._output_file != ''):
            self._statistics.writeOutput(self._db_connection, {
                'assistance': self._assistance,
                'incomes': self._incomes
            })

        # If tournament match
        if (self._match_type == 3):
            # Increase player's experience
            if self._teams[0].getId() > 26:
                for player in self._teams[0].getPlayersList():
                    player.saveStatus(self._db_connection, self._category_id)

            if self._teams[1].getId() > 26:
                for player in self._teams[1].getPlayersList():
                    player.saveStatus(self._db_connection, self._category_id)

            # Update scorers
            self._statistics.saveScorers(self._db_connection)


        return self._statistics