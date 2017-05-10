#!/usr/bin/python3

class Ball:
    def __init__(self, position):
        self._position = position.copy()
        self._player = None

    def __str__(self):
        return 'Ball: %d, %d; X: %f - Y: %f' % (self._team, self._player, self._position[0], self._position[1])

    def getPlayer(self):
        return self._player

    def getPosition(self):
        return self._position

    def getTeam(self):
        return self._player.getTeam()

    def setPlayer(self, player, updatePosition = True):
        if self._player:
            self._player.setHasBall(False)

        self._player = player

        if player:
            player.setHasBall(True)

            if updatePosition:
                self._position = player.getPosition().copy()
            else:
                self._player.setPosition(self._position.copy())

    def setPosition(self, position):
        self._position = position.copy()
        if self._player:
            self._player.setPosition(position.copy())