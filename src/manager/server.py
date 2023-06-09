import os.path

from src.database.client import DbClient
from src.database.container import Channel

# from src.manager.upload import UploadManager
from src.manager.error import VireoError, ErrorType
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import jwt
import bcrypt
import configparser

SUCCESS = 200
BAD_REQUEST = 400
UNAUTHORIZED = 401
FORBIDDEN = 403
INTERNAL_ERROR = 500

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


# TODO: use join table query for getting username of the channel with videos

class Server:

    def __init__(self):

        # TODO: make sure all important key are there
        self.__config = configparser.ConfigParser()
        self.__config.read("config.ini")

        # TODO: implement when not in development
        logfile = os.path.join(self.__config['DEVELOPMENT']['db-dir'], "app.log")

        self.db_client = DbClient(dict(self.__config["DATABASE"]))
        self.db_client.initiate_connection()

        self.__secret = self.__config["TOKEN"]["secret"]
        self.__alg = self.__config["TOKEN"]["algorithm"]
        print(self.__alg)

    def process_token(self, header: dict, ipaddr: str) -> (dict, int):

        try:
            auth = header["Authorization"]

        except KeyError:
            logging.debug(f"{ipaddr} - request missing authorization header field")
            return {}, BAD_REQUEST

        # eg. authorization: Basic Tokekkekdkskakakdfkaskdfkkas
        auth = auth.split(" ")

        if len(auth) != 2:
            logging.debug(f"{ipaddr} - malformed authorization header field")
            return {}, BAD_REQUEST

        token = auth[1]

        try:
            payload = jwt.decode(token, key=self.__secret, algorithms=self.__alg)

        except jwt.ExpiredSignatureError as e:
            logging.debug(f"{ipaddr} - session expire")
            return {"response": "token expire"}, UNAUTHORIZED

        username = payload["username"]
        password = payload["password"]

        try:
            hpassword = self.db_client.query(f"""
            SELECT Password FROM Channels WHERE USERNAME = '{username}';""")[0][0]

        except VireoError as e:
            logging.error(f"{ipaddr} - {e}")
            return {}, INTERNAL_ERROR

        return SUCCESS

    def handle_signin(self, data, ipaddr: str) -> (dict, int):

        # validate body
        for key in ["username", "password"]:
            found = False

            if key in data.keys():
                found = True

            if not found:
                logging.debug(f"{ipaddr} - malformed body field")
                return {}, BAD_REQUEST

        try:
            username, hpassword = self.db_client.query(f"""
                SELECT Username,Password 
                FROM Channels
                WHERE Username = '{data['username']}';""")[0]

        except VireoError as e:
            logging.error(e)
            return {}, INTERNAL_ERROR
        except IndexError as e:
            return {"response": "username"}, UNAUTHORIZED

        if not bcrypt.checkpw(data["password"].encode('utf-8'), hpassword.encode('utf-8')):
            return {"response": "password"}, UNAUTHORIZED

        expire = (datetime.now() + timedelta(hours=3)).timestamp()

        payload = {
            "username": username,
            "password": hpassword,
            "exp": expire
        }

        token = jwt.encode(payload, self.__secret, algorithm=self.__alg)

        return {"token": token}, 200

    def handle_sign_up(self, data: dict, ipaddr: str) -> (dict, int):

        for key in SIGNUP_KEY:
            found = False

            if key in data.keys():
                found = True

            if not found:
                return {"response": ""}, BAD_REQUEST

        valid_username = False
        try:

            user = self.db_client.query(f"""
                SELECT Username
                FROM Channels
                WHERE Username = '{data["username"]}';""")[0][0]

        except VireoError as e:
            logging.error(f"{ipaddr} - {e}")
            return {}, 500
        except IndexError:
            valid_username = True

        if not valid_username:
            return {"response": "username"}, BAD_REQUEST

        valid_email = False
        try:
            self.db_client.query(f"""
                SELECT Email
                FROM ChannelDetails
                WHERE Email = '{data["email"]}';""")[0][0]

        except VireoError as e:
            logging.error(f"{ipaddr} - {e}")
            return {}, 500
        except IndexError:
            valid_email = True

        if not valid_username:
            return {"response": "password"}, BAD_REQUEST

        middle_name = f"'{data['mname']}'" if data["mname"] else "NULL"

        birthday = datetime(data["year"], data["month"], data["day"])

        salt = bcrypt.gensalt(rounds=14)
        passwd = bcrypt.hashpw(data["password"].encode('utf-8'), salt)

        try:
            _id = self.db_client.query("""SELECT COUNT(ChannelID) FROM Channels;""")[0][0] + 1

        except VireoError as e:
            logging.error(f"{ipaddr} - {e}")
            return {}, INTERNAL_ERROR

        insert1 = f"""
            INSERT INTO Channels (
                ChannelID,
	            Username,
                Password
            )
            VALUES 
            ( '{_id}','{data["username"]}','{passwd}');"""

        try:
            self.db_client.insert(insert1)

        except VireoError as e:
            logging.error(f"{ipaddr} - {e}")
            return {}, INTERNAL_ERROR

        insert2 = f"""
            INSERT INTO ChannelDetails (
                ChannelId,
	            Fname,
                Mname,
                Lname,
                Email,
                Birth
            )   
            VALUES
            (
                {_id},
                '{data["name"]}',
                {middle_name},
                '{data["lname"]}',
                '{data["email"]}',
                Date('{birthday.isoformat()}'));"""

        return {}, 200
