from database.container import Channel
from database.client import DbClient
from manager.error import SignUpError,SignUpErrType
import bcrypt


SIGNUP_KEY = [
    "fname",
    "mname",
    "lname",
    "username",
    "month",
    "day",
    "year",
    "email",
    "password"
]


class SignUpManager:

    def __validateJsonBody(self,data:dict,expect_key:list):
        
        for key in expect_key:

            found = False
        
            if key in data.keys():
                found = True

            if not found: 
                raise SignUpReqError(SignUpErrType.MissingField,key) 

    
    def handle(self,data:dict,client:DbClient):
        
        self.__validateJsonBody(data,SIGNUP_KEY)

        row = client.query(f"""
        SELECT Username 
        FROM Channels
        WHERE Username = '{data["username"]}';""",
        1)
    
        if row == 1: 
            raise SignUpError(SignUpErrType.UsernameExist)

        row = client.query(f"""

            SELECT Email
            FROM ChannelDetails
            WHERE Email = '{data["email"]}';""",
            1)

        if row == 1: 
            raise SignUpError(SignUpErrType.EmailExist)

        middle_name =  data["mname"] if  data["mname"] else None
        birthday = f"{data['year']}-{data['month']}-{data['day']}"

        # generate salt
        salt = bcrypt.gensalt(rounds=14)
        passwd = bcrypt.hashpw(data["password"].encode('utf-8'), salt)

        _id = client.queryForValue("""SELECT COUNT(CHANNELID) FROM Channels""")[0][0] + 1
        channel = Channel(
            _id,
            data["username"],
            passwd.decode('utf-8'),
            data["fname"],
            middle_name,
            data["lname"],
            data["email"], 
            birthday
            )

        client.insert(channel.insert_to_channels())        
        client.insert(channel.insert_to_channeslDetails())
