#!/usr/bin/python3

# Imports
import configparser
import MySQLdb
import os

class Mysql:
    _mysql_connection = None

    def __init__(self):
        # Load configuration
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'conf.ini'))

        # MySQL connection
        self._mysql_connection = MySQLdb.connect(config['MYSQL']['Host'], config['MYSQL']['User'], config['MYSQL']['Pass'], config['MYSQL']['Database'])

    def __del__(self):
        self._mysql_connection.close()

    def query(self, query, results = 0):
        self._mysql_connection.query(query)
        r = self._mysql_connection.store_result()

        if results == 1:
            r = r.fetch_row(1, 1)
            return r[0]
        else:
            return r.fetch_row(results, 1)