import mariadb
import configparser

from typing import List
from src.manager.error import VireoError, ErrorType


class DbClient:
    """ interact with database  """

    def __init__(self, config: dict):
        """ Initializes the DbClient class """

        self.__connection = None
        self.__cursor = None
        self.__info = config

    def initiate_connection(self):
        """
        Make a connection with the database.
        @raise VireoError: When the connection fail with the credential of the config.ini file
        """

        try:
            self.__connection = mariadb.connect(

                user=self.__info['username'],
                password=self.__info['password'],
                host=self.__info['address'],
                port=int(self.__info['port']),
                database=self.__info['name']
            )

        except mariadb.Error as e:
            raise VireoError(ErrorType.DbConnection, e.args[0])

        # this will serve to execute query and inset
        self.__cursor = self.__connection.cursor()

    def is_connected(self) -> bool:
        """
        check if a current connection is still connected.
        @return: whether it can ping the database
        """
        try:
            self.__connection.ping()
        except mariadb.Error:
            return False

        return True

    def query(self, query: str) -> List:
        """
        Execute a query to the database if connected to database.
        @param query: the query to be executed
        @return: the rows found that match the query
        """

        # check if a connection have been made
        if self.__connection is None:
            raise VireoError(ErrorType.DbNotConnected)

        if not self.is_connected():
            self.initiate_connection()

        try:
            self.__cursor.execute(query)

        except mariadb.Error as e:
            raise VireoError(ErrorType.DbExecution, e.args[0])

        return self.__cursor.fetchall()

    def insert(self, query):
        """
        Execute query that need to be committed.
        @param query: the query to be executed
        """

        # check if a connection have been made
        if self.__connection is None:
            raise VireoError(ErrorType.DbNotConnected)

        if not self.is_connected():
            self.initiate_connection()

        try:
            self.__cursor.execute(query)
            self.__connection.commit()
        except mariadb.Error as e:
            raise VireoError(ErrorType.DbInsertion, e.args[0])
