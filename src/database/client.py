import mariadb
import logging

from typing import List
from src.manager.error import VireoError, ErrorType


class DbClient:
    """ interact with a database  """

    def __init__(self, config: dict, log_file: str):
        """ Initializes the DbClient class """

        self.__connection = None
        self.__cursor = None
        self.__info = config

        # TODO: change log format
        logging.basicConfig(filename=log_file, filemode='a')

    def initiate_connection(self):
        """
        Make a connection with the database.
        @raise VireoError: When the connection fails with the credential of the good_config.ini file
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

        # this will serve to execute a query and inset
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

    def query(self, query: str) -> List | None:
        """
        Execute a query to the database if connected to a database.
        @param query: The query to be executed
        @return: the rows found that match the query
        """

        # check if a connection has been made
        if self.__connection is None:
            raise VireoError(ErrorType.DbNotConnected)

        if not self.is_connected():
            self.initiate_connection()

        try:
            self.__cursor.execute(query)

        except mariadb.Error as e:
            logging.error(f"Query execution: {e}")
            return None

        return self.__cursor.fetchall()

    def insert(self, query) -> List | None:
        """
        Execute a query that needs to be committed.
        @param query: The query to be executed
        """

        # check if a connection has been made
        if self.__connection is None:
            raise VireoError(ErrorType.DbNotConnected)

        if not self.is_connected():
            logging.error("try to execute query to database but no connection is made")
            return None

        try:
            self.__cursor.execute(query)
            self.__connection.commit()

        except mariadb.Error as e:
            logging.error(f"Query execution: {e}")
            return None
