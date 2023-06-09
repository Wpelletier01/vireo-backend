
from src.database.client import DbClient

import bcrypt

BODY_KEY = [
    "username",
    "password",

]


def __validateJsonBody(data:dict, expect_key:list):

    for key in expect_key:
        found = False

        if key in data.keys():
            found = True

        if not found:
            raise SignInError(SignInErrType.MissingField, key)

    if data["utype"] not in ["email", "username"]:
        raise SignInError(SignInErrType.BadUtype)


class SignInManager:

    def handle(self,data:dict,db_client:DbClient):
        
        __validateJsonBody(data,BODY_KEY)

        _id = 0

        if data["utype"] == "email":

            row = db_client.query(f"""
                SELECT Email
                FROM ChannelDetails
                WHERE Email = {data["username"]};""",
                1)

            if row == 0:
                raise SignInError(SignInErrType.EmailNotFound)

            _id = db_client.queryForValue(f"""
                SELECT CHANNELID
                FROM ChannelDetails
                WHERE EMAIL = {data["username"]};""")[0][0]

        else:
           
            row = db_client.query(f"""
                SELECT Username
                FROM Channels
                WHERE Username = '{data['username']}';""",
                1)
         

            if row == 0:
                raise SignInError(SignInErrType.UsernameNotFound)

            _id = db_client.queryForValue(f"""
                SELECT CHANNELID
                FROM Channels
                WHERE Username = '{data["username"]}';
                """)[0][0]

        password = data["password"].encode('utf-8')
        hpassword = db_client.queryForValue(
            f"""SELECT Password FROM Channels WHERE ChannelID = {_id};"""
            )[0][0]

        if not bcrypt.checkpw(password.encode('utf-8'),hpassword):
            raise SignInError(SignInErrType.WrongPassword)



