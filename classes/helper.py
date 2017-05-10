#!/usr/bin/python3

import math

class Helper:
    def calculateDistance(pos1, pos2):
        return math.sqrt(pow(pos1[0] - pos2[0], 2) + pow(pos1[1] - pos2[1], 2))