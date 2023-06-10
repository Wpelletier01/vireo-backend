from src.database.client import DbClient
from src.manager.error import VireoError
from src.manager.vconf import validate_config_file
from datetime import datetime, timedelta
from deffcode import FFdecoder
from dataclasses import dataclass

import logging
import jwt
import bcrypt
import configparser
import os
import random
import string
import cv2
import shutil

# TODO: when vireo exception is raised, make them log automatically

# http error code
SUCCESS = 200
BAD_REQUEST = 400
UNAUTHORIZED = 401
FORBIDDEN = 403
INTERNAL_ERROR = 500

# sign up field that needs to be found in the post-body
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


def _validate_body(body: dict, keys: list) -> bool:
    """
    Make sure that all the filed needed are there to be found

    @param body: The request body that needs to be validated
    @param keys: the keys that need to be found in the body
    @return: true if the request body is valid
    """
    for key in keys:
        found = False

        if key in body.keys():
            found = True

        if not found:
            return False

    return True


@dataclass
class ResponseBody:
    stype: str
    channel: str
    title: str | None
    thumbnail: str
    upload: str | None
    nb_video: int | None

    def asDict(self) -> dict:
        return {
            "type": self.stype,
            "channel": self.channel,
            "title": self.title if self.title else "",
            "thumbnail": self.thumbnail,
            "nb_count": self.nb_video if self.nb_video else "",
            "upload": self.upload if self.upload else ""
        }


class VResponse:
    def __init__(self, status: int, response: str | dict | list = "", headers: dict | None = None):
        self.status = status
        self.response = {"response": response}
        self.headers = headers

    def send(self) -> tuple:
        if self.headers is not None:
            return self.response, self.status, self.headers.items()
        return self.response, self.status


class Server:

    def __init__(self):
        """ initialize the Server class"""

        # gather all important config value
        self.__config = configparser.ConfigParser()
        self.__config.read("good_config.ini")
        # validate his content
        validate_config_file(self.__config)

        # Where we should found all the data (thumbnails, videos, channel picture, etc.)
        self.__data_dir = self.__config['DEVELOPMENT']['db-dir']

        # Where the server log would be
        slogfile = os.path.join(self.__data_dir, "server.log")
        logging.basicConfig(filename=slogfile, filemode="w")

        # Create and start a connection with the database
        dlogfile = os.path.join(self.__data_dir, "log/db.log")
        self.db_client = DbClient(dict(self.__config["DATABASE"]), dlogfile)
        self.db_client.initiate_connection()

        # secret and algorithm used for encode and decode jwt token
        self.__secret = self.__config["TOKEN"]["secret"]
        self.__alg = self.__config["TOKEN"]["algorithm"]

    def __process_token(self, header: dict, ipaddr: str) -> (dict, int):

        try:
            token = header.get("Vireo-Token")

        except KeyError:
            return VResponse(BAD_REQUEST, "token")

        try:
            payload = jwt.decode(token, key=self.__secret, algorithms=self.__alg)

        except jwt.ExpiredSignatureError as e:
            logging.debug(f"{ipaddr} - session expire")
            return VResponse(UNAUTHORIZED, "token expire")

        username = payload["username"]
        password = payload["password"]

        hpasswd_resp = self.db_client.query(f"""
            SELECT Password FROM Channels WHERE USERNAME = '{username}';""")[0][0]

        if hpasswd_resp is None:
            return VResponse(INTERNAL_ERROR)

        try:
            hpasswd = hpasswd_resp

        except IndexError:
            logging.error(f"{ipaddr} - have jwt but his username dont exist")
            return VResponse(BAD_REQUEST, "bad-token-username")

        if not bcrypt.checkpw(password, hpasswd):
            return VResponse(BAD_REQUEST, "bad-token-password")

        return VResponse(SUCCESS)

    def __gen_token(self, username: str, hpasswd: str) -> str:
        expire = (datetime.now() + timedelta(hours=3)).timestamp()

        payload = {
            "username": username,
            "password": hpasswd,
            "exp": expire
        }

        return jwt.encode(payload, self.__secret, algorithm=self.__alg)

    def __query_video(self, query: str) -> (dict, int):
        search_query = f"""
            SELECT v.Title, c.Username, v.PathHash
            FROM Videos v
            JOIN Channels c
            ON v.ChannelID = c.ChannelID
            WHERE
                Title like '%{query}%' OR
                Description like '%{query}%';"""

        videos = self.db_client.query(search_query)

        if videos is None:
            return VResponse(INTERNAL_ERROR)

        response = []

        for video in videos:
            response.append(ResponseBody('video', video[1], video[0], video[2], None, None).asDict())

        return VResponse(SUCCESS, response)

    def __query_channel(self, query: str) -> (dict, int):

        # return channel name and the number of videos it has
        search_query = f"""
            SELECT c.Username, v.PathHash, COUNT(v.VideoID)
            FROM Channels c
            JOIN Videos v ON v.ChannelID = c.ChannelID
            WHERE Username like '%{query}%';"""

        channels = self.db_client.query(search_query)

        if channels is None:
            return VResponse(INTERNAL_ERROR)

        response = []

        for channel in channels:
            response.append(
                ResponseBody('channel', channel[0], None, channel[1], channel[2], None).asDict()
            )

        return VResponse(SUCCESS, response)

    def __create_thumbnail(self, tmp_fp: str, hash_path: str):

        # TODO: resize for best thumbnails

        video = cv2.VideoCapture(tmp_fp)

        if not video.isOpened():
            raise Exception("Unable to load video")

        frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
        frame_id = random.randint(0, frames)

        video.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

        success, frame = video.read()

        tmp_img = os.path.join(self.__data_dir, f"tmp/{hash_path}.png")

        cv2.imwrite(tmp_img, frame)

    def handle_signin(self, data, ipaddr: str) -> (dict, int):

        # validate body
        if not _validate_body(data, ["username", "password"]):
            return {"response": ""}, BAD_REQUEST

        try:
            username, hpassword = self.db_client.query(f"""
                SELECT Username,Password 
                FROM Channels
                WHERE Username = '{data['username']}';""")[0]

        except VireoError as e:
            logging.error(e)
            return {"response": ""}, INTERNAL_ERROR
        except IndexError as e:
            return {"response": "username"}, UNAUTHORIZED

        if not bcrypt.checkpw(data["password"].encode('utf-8'), hpassword.encode('utf-8')):
            return {"response": "password"}, UNAUTHORIZED

        return {
            "response": {"token": self.__gen_token(username, hpassword)}
        }, SUCCESS

    def handle_sign_up(self, data: dict, ipaddr: str) -> (dict, int):

        if not _validate_body(data, SIGNUP_KEY):
            return {"response": ""}, BAD_REQUEST

        valid_username = False
        try:
            user = self.db_client.query(f"""
                SELECT Username
                FROM Channels
                WHERE Username = '{data["username"]}';""")[0][0]

        except VireoError as e:
            logging.error(f"{ipaddr} - {e}")
            return {"response": ""}, 500
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
            return {"response": ""}, 500
        except IndexError:
            valid_email = True

        if not valid_email:
            return {"response": "password"}, BAD_REQUEST

        middle_name = f"'{data['mname']}'" if data["mname"] else "NULL"

        birthday = datetime(data["year"], data["month"], data["day"])

        salt = bcrypt.gensalt(rounds=14)
        passwd = bcrypt.hashpw(data["password"].encode('utf-8'), salt)

        try:
            _id = self.db_client.query("""SELECT COUNT(ChannelID) FROM Channels;""")[0][0] + 1

        except VireoError as e:
            logging.error(f"{ipaddr} - {e}")
            return {"response": ""}, INTERNAL_ERROR

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
            return {"response": ""}, INTERNAL_ERROR

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
        try:
            self.db_client.insert(insert2)

        except VireoError as e:
            logging.error(f"{ipaddr} - {e}")
            return {"response": ""}, INTERNAL_ERROR

        return {"response": "success"}, 200

    def handle_upload(self, data: bytes, header: dict, ipaddr: str) -> (dict, int):
        # TODO: validate size
        # TODO: make sure that the user cant upload more than one video at time

        payload, result = self.__process_token(header, ipaddr)

        if result != SUCCESS:
            return payload, result

        tmp = os.path.join(self.__data_dir, f"tmp/{ipaddr}.mp4")

        with open(tmp, "wb") as f:
            f.write(data)
            f.close()

        decoder = FFdecoder(tmp)

        try:
            video_info = decoder.metadata["vireo"]

        except KeyError:
            return {"response": "vireo"}, BAD_REQUEST

        if _validate_body(video_info, ["title", "description"]):
            return {}, BAD_REQUEST

        possibility = string.ascii_lowercase + string.ascii_lowercase + string.digits
        hpath = "".join(random.choice(possibility) for c in range(7))

        try:
            channel_id = self.db_client.query(
                f"""SELECT ChannelID FROM Channels WHERE Username = '{payload["username"]}';"""
            )[0][0]
        except VireoError as e:
            logging.error(f"{ipaddr} - {e}")
            return {"response": ""}, INTERNAL_ERROR

        insert = f"""
            INSERT INTO Videos(
                PathHash,
                ChannelID,
                Title,
                Description,
                Upload
            )
            VALUE (
                '{hpath}',
                '{channel_id}',
                '{video_info["title"]}',
                '{video_info["description"]}',
                Date('{datetime.now().timestamp()}')
            );"""

        try:
            self.db_client.insert(insert)

        except VireoError as e:
            logging.error(f"{ipaddr} - {e}")
            return {"response": ""}, BAD_REQUEST

        try:
            self.__create_thumbnail(tmp, hpath)

        except Exception as e:
            logging.error(e)
            return VResponse(INTERNAL_ERROR)

        dest = os.path.join(self.__data_dir, f"videos/{hpath}.mp4")

        shutil.copy(tmp, dest)

        return {"response": hpath}, SUCCESS

    def retrieve_video_info(self, name: str | None) -> (dict, str):

        query = """
            SELECT v.PathHash, v.Title, c.Username, v.Upload
            FROM Videos v
            JOIN Channels c ON v.ChannelID = c.ChannelID"""

        if name is None:
            query = f"""{query}\nWHERE c.Username = '{self}';"""

        info = []

        videos = self.db_client.query(query)

        if videos is None:
            return VResponse(INTERNAL_ERROR)

        for video in videos:
            info.append(
                ResponseBody('video', video[2], video[1], video[0], video[3], None).asDict()
            )

        return VResponse(SUCCESS, info)

    def handle_search(self, squery: str, stype: str) -> (dict, str):

        response = []
        # TODO: add duration of info return
        # TODO: make different type of query like for only channel
        match stype:
            case "all":
                videos, status = self.__query_video(squery)

                if status != SUCCESS:
                    return videos, status

                for video in videos["response"]:
                    response.append(video)

                channels, status = self.__query_channel(squery)

                if status != SUCCESS:
                    return channels, status

                for channel in channels["response"]:
                    response.append(channel)

            case _:
                return {"response": "bad-search-type"}, BAD_REQUEST

        return {"response": response}, SUCCESS

    def get_thumbnail_path(self, hpath: str) -> (dict, int):
        thumbnails_dir = os.path.join(self.__data_dir, "thumbnails")

        if f"{hpath}.png" not in os.listdir(thumbnails_dir):
            return {"response": "no-thumbnail"}, BAD_REQUEST

        return {"response": os.path.join(thumbnails_dir, f"{hpath}.png")}, SUCCESS

    def get_video(self, hpath: str) -> (dict,):
        videos_dir = os.path.join(self.__data_dir, "videos")

        if f"{hpath}.mp4" not in os.listdir(videos_dir):
            return {"response": "no-video"}, BAD_REQUEST

        url = os.path.join(videos_dir, f"{hpath}.mp4")

        return {"response": url}, SUCCESS

    def get_vinfo(self, hpath: str):

        query = f"""
                    SELECT v.Title, c.Username,v.Description
                    FROM Videos v
                    JOIN Channels c
                    ON v.ChannelID = c.ChannelID
                    WHERE PathHash = '{hpath}';"""

        try:
            vinfo = self.db_client.query(query)[0]

        except VireoError as e:
            logging.error(f"database call failed: {e}")
            return {"response": ""}, INTERNAL_ERROR
        except IndexError:
            logging.error(f"video file exist but not in the database")
            return {"response": ""}, INTERNAL_ERROR

        return {"response": {
            "title": vinfo[0],
            "channel": vinfo[1],
            "description": vinfo[2],
            "hpath": hpath
        }
        }, SUCCESS
