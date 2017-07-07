#!/usr/bin/python3

class Ball:
    def __init__(self, positioning):
        self._positioning = positioning.copy()
        self._player = None

    def __str__(self):
        return 'Ball: %d, %d; X: %f - Y: %f' % (self._player.getTeam(), self._player.getIndex(), self._positioning[0], self._positioning[1])

    def getPlayer(self):
        return self._player

    def getPositioning(self):
        return self._positioning

    def getTeam(self):
        return self._player.getTeam()

    def setPlayer(self, player, updatePositioning = True):
        if self._player:
            self._player.setHasBall(False)

        self._player = player

        if player:
            player.setHasBall(True)

            if updatePositioning:
                self._positioning = player.getPositioning().copy()
            else:
                self._player.setPositioning(self._positioning.copy())

    def setPositioning(self, positioning):
        self._positioning = positioning.copy()
        if self._player:
            self._player.setPositioning(positioning.copy())