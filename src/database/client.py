import mariadb
import bcrypt
from enum import Enum
from typing import List

# for connection outside the nat network
PORT_FOWARDING = 5533
HOST_OUTSIDE = "127.0.0.1"
DB_USER = "admin"
PASSWORD = "vireo"
DB_NAME = "vireodb"


class DatabaseErrorType(Enum):
    
    UnexpectedQueryReturn = 1
    TableInsertion = 2
    Connection = 3
    BadQuery = 4
    


class DatabaseError(Exception):

    def __init__(self, message,etype:DatabaseErrorType):
        self.msg = message
        self.__etype = etype
    
    def __str__(self):
        return self.msg

    def getType(self):
        return self.__etype


class DbClient:

    def __init__(self):
        self.__connection = None
        self.__cursor = None 

    def initiate_connection(self,dev_mode:bool):

        if dev_mode:

            try: 

                self.__connection = mariadb.connect(
    
                    user=DB_USER,
                    password=PASSWORD,
                    host=HOST_OUTSIDE,
                    port=PORT_FOWARDING,
                    database=DB_NAME     
                    )

            except mariadb.Error as e:
                raise DatabaseError(e.args[0],DatabaseErrorType.Connection)
        
        
        self.__cursor = self.__connection.cursor()


    def query(self,query:str,atMost:int) -> int:

        try:
            self.__cursor.execute(query)
            nbRow = self.__cursor.rowcount

            if nbRow > atMost:
            
                raise DatabaseError(
                    "Unexpected Number of return value have been found",
                    DatabaseErrorType.UnexpectedQueryReturn
                    )
            
            return nbRow


        except mariadb.Error as e:
            raise DatabaseError(e.args[0],DatabaseErrorType.BadQuery)

    def queryForValue(self,query) -> List:

        try:
            self.__cursor.execute(query)

            return self.__cursor.fetchall()

        except mariadb.Error as e:
            raise DatabaseError(
                    f"Unable to execute query reason: {e.args[0]}",
                    DatabaseErrorType.BadQuery
                )


    def insert(self,query):

        try:
            self.__cursor.execute(query)
            self.__connection.commit()
        except mariadb.Error as e:
            raise DatabaseError(
                f"Unable to execute insert query because of: {e.args[0]}",
                DatabaseErrorType.TableInsertion
                )
        
    def alter(self,query):
        try:
            self.__cursor.execute(query)
        
        except mariadb.Error as e:
            raise DatabaseError(
                f"Unable to execute alter table query because of: {e.args[0]}",
                DatabaseErrorType.TableInsertion
                )
