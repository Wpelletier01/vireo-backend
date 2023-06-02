
import mariadb


# for connection outside the nat network
PORT_FOWARDING = 5533
HOST_OUTSIDE = "127.0.0.1"


DB_USER = "admin"
PASSWORD = "vireo"
DB_NAME = "vireodb"



class DbClient:

    def __init__(self,dev_mode:bool):
        

        if dev_mode:
            self._connection = mariadb.connect(
    
                user=DB_USER,
                password=PASSWORD,
                host=HOST_OUTSIDE,
                port=PORT_FOWARDING,
                database=DB_NAME     
            )

            self._cursor = self._connection.cursor()


    def validate_logging(self,uname:str,password:str) -> bool:

        query = f"""
            
            SELECT username,password 
            from accountIds 
            WHERE USERNAME = '{uname}'
            AND PASSWORD = '{password}';
        """
        
        self._cursor.execute(query) 
        

        if self._cursor.rowcount == 0:

            return False

        return True


if __name__ == "__main__":

    client = DbClient(True)

    if client.validate_logging("test1", "1234"):
        print("login")
    else:
        print("not loggin")