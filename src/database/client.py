
import mariadb
from .container import UserInfo
from enum import Enum

# for connection outside the nat network
PORT_FOWARDING = 5533
HOST_OUTSIDE = "127.0.0.1"


DB_USER = "admin"
PASSWORD = "vireo"
DB_NAME = "vireodb"


class DatabaseError(Exception):

    def __init__(self, message):
        self.msg = message
    
    def __str__(self):

        return self.msg
    
class QueryError(DatabaseError):

    def __init__(self,message):

        super().__init__(f"Query Error: {message}")

class UnexpectedReturnError(QueryError):

    def __init__(self,expected,found):

        super().__init__(f"Unexpected Return Error: Expected {expected} but found {found}")

class InsertQuerryError(QueryError):
    def __init__(self, message):
        super().__init__("Insert Call failed because {message}")

class InsertAccountErrorType(Enum):

    EmailAlreadyUsed = 1
    UsernameAlreadyUsed = 2

class InsertAccountErr(DatabaseError):

    def __init__(self, message:str,error_type:InsertAccountErrorType):

        self.error_type = error_type

        super().__init__(message)


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
                raise DatabaseError(e.args)
        
        
        self.__cursor = self.__connection.cursor()


    def __query(self,query:str,expect:int) -> bool:

        try:
            self.__cursor.execute(query)

            nb_row = self.__cursor.rowcount

            if nb_row == expect:
                return True 
            elif nb_row == 0:
                return False
            else:
                raise UnexpectedReturnError(expect, nb_row)

        except mariadb.Error as e:
            raise DatabaseError(e.args)


    def __insert(self,query):

        try:
            self.__cursor.execute(query)
            self.__connection.commit()

        except mariadb.Error as e:
            raise InsertQuerryError(e.args)
        
    def validate_logging(self,uname:str,password:str) -> bool:

        query = f"""
            
            SELECT username,password 
            from accountIds 
            WHERE USERNAME = '{uname}'
            AND PASSWORD = '{password}';
        """
        
        return self.__query(query,1)

       
    def __email_exist(self,email) -> bool:

        query = f"""
        
            SELECT email
            FROM accountInfo
            WHERE email = '{email}';
        """

        return self.__query(query, 1)

    def __username_exist(self,username:str) -> bool:
        
        query = f"""
        
            SELECT username
            FROM accountIds
            WHERE username = '{username}';
        """

        return self.__query(query,1)


    def insertNewAccount(self,userinfo:UserInfo):
        
        if self.__email_exist(userinfo.email):
            raise InsertAccountErr("Email exist", InsertAccountErrorType.EmailAlreadyUsed)
        
        if self.__username_exist(userinfo.username):
            raise InsertAccountErr("Username exist", InsertAccountErrorType.UsernameAlreadyUsed)


    
    
    
    