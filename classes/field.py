#!/usr/bin/python3

class Field:
    _height = 120.0
    _width = 90.0

    def getGoalPositioning(index):
        if index == 0:
            return [Field._width / 2, 0]
        else:
            return [Field._width / 2, Field._height]

    def getHeight():
        return Field._height

    def getSize():
        return [Field._width, Field._height]

    def getWidth():
        return Field._width
