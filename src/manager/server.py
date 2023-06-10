from src.database.client import DbClient
from src.database.container import Channel

# from src.manager.upload import UploadManager
from src.manager.error import VireoError, ErrorType
from datetime import datetime, timedelta
from deffcode import FFdecoder
from functools import wraps

import logging
import jwt
import bcrypt
import configparser
import os
import random
import string
import cv2
import shutil

# TODO: Make that when vireo exception is raised than log them automatically

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


def _validate_body(body: dict, keys: list) -> bool:
    for key in keys:
        found = False

        if key in body.keys():
            found = True

        if not found:
            return False

    return True


# TODO: use join table query for getting username of the channel with videos

class Server:

    def __init__(self):

        # TODO: make sure all important key are there
        self.__config = configparser.ConfigParser()
        self.__config.read("config.ini")

        self.__data_dir = self.__config['DEVELOPMENT']['db-dir']

        # TODO: implement when not in development
        logfile = os.path.join(self.__data_dir, "app.log")

        self.db_client = DbClient(dict(self.__config["DATABASE"]))
        self.db_client.initiate_connection()

        self.__secret = self.__config["TOKEN"]["secret"]
        self.__alg = self.__config["TOKEN"]["algorithm"]

    def __process_token(self, header: dict, ipaddr: str) -> (dict, int):

        try:
            token = header.get("Vireo-Token")

        except KeyError:
            return {"response": "token"}, BAD_REQUEST

        try:
            payload = jwt.decode(token, key=self.__secret, algorithms=self.__alg)

        except jwt.ExpiredSignatureError as e:
            logging.debug(f"{ipaddr} - session expire")
            return {"response": "token expire"}, UNAUTHORIZED

        username = payload["username"]
        password = payload["password"]

        try:
            hpasswd = self.db_client.query(f"""
            SELECT Password FROM Channels WHERE USERNAME = '{username}';""")[0][0]

        except VireoError as e:
            logging.error(f"{ipaddr} - {e}")
            return {"response": ""}, INTERNAL_ERROR

        except IndexError:
            logging.error(f"{ipaddr} - have jwt but his username dont exist")
            return {"response": "bad-token-username"}, BAD_REQUEST

        if not bcrypt.checkpw(password, hpasswd):
            return {"response": "bad-token-password"}, BAD_REQUEST

        return {}, SUCCESS

    def __gen_token(self, username: str, hpassword: str) -> str:
        expire = (datetime.now() + timedelta(hours=3)).timestamp()

        payload = {
            "username": username,
            "password": hpassword,
            "exp": expire
        }

        return jwt.encode(payload, self.__secret, algorithm=self.__alg)

    def __query_video(self, squery: str) -> (dict, int):
        query = f"""
            SELECT v.Title, c.Username, v.PathHash
            FROM Videos v
            JOIN Channels c
            ON v.ChannelID = c.ChannelID
            WHERE
                Title like '%{squery}%' OR
                Description like '%{squery}%';"""

        try:
            videos = self.db_client.query(query)
        except VireoError as e:
            logging.error(f"database call failed: {e}")
            return {"response": ""}, INTERNAL_ERROR

        response = []
        for video in videos:
            info = {
                "type":         "video",
                "title":        video[0],
                "channel":      video[1],
                "thumbnail":    video[2]
            }

            response.append(info)

        return {"response": response}, SUCCESS

    def __query_channel(self, squery: str) -> (dict, int):
        # TODO: add query for the number of video that each channels have

        try:
            channels = self.db_client.query(f"""
                SELECT Username
                FROM Channels
                WHERE Username like '%{squery}%';""")
        except VireoError as e:
            logging.error(f"database call failed: {e}")
            return {"response": ""}, INTERNAL_ERROR

        response = []

        for channel in channels:
            info = {
                "type": "channel",
                "channel": channel[0],
                "title": None,
                "hpath": None

            }
            response.append(info)

        return {"response": response}, SUCCESS

    def __create_thumbnail(self, tmp_fp: str, hash_path: str):

        # TODO: check for error
        # TODO: resize for best thumbnails
        video = cv2.VideoCapture(tmp_fp)

        frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
        frame_id = random.randint(0, frames)

        video.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

        success, frame = video.read()

        cv2.imwrite(os.path.join(self.__data_dir, f"thumbnails/{hash_path}.png"), frame)

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

        self.__create_thumbnail(tmp, hpath)

        shutil.copy(tmp, os.path.join(self.__data_dir, f"videos/{hpath}.mp4"))

        return {"response": hpath}, SUCCESS

    def retrieve_video_info(self, rtype: str, channel: str | None) -> (dict, str):

        videos = []
        info = []
        query = ""

        match rtype:
            case "all":
                query = f"""
                    SELECT v.PathHash, v.Title, c.Username, v.Upload
                    FROM Videos v
                    JOIN Channels c
                    ON v.ChannelID = c.ChannelID;"""

            case "channel":
                if channel is None:
                    logging.error("try retrieve channel video but no username is passed")
                    return {"response": ""}, INTERNAL_ERROR

                query = f"""
                    SELECT v.PathHash, v.Title, c.Username, v.Upload
                    FROM Videos v
                    JOIN Channels c
                    ON v.ChannelID = c.ChannelID 
                    WHERE c.Username = '{channel}';"""

            case _:
                return {"response": "bad-url-type"}, BAD_REQUEST

        info = []

        try:
            videos = self.db_client.query(query)

        except VireoError as e:
            logging.error(f"database call failed: {e}")
            return {}, INTERNAL_ERROR

        for video in videos:
            hpath = video[0]
            date = video[3]
            title = video[1]
            nchannel = video[2]

            info.append({
                "thumbnail":    hpath,
                "channel":      nchannel,
                "title":        title,
                "upload":       date
            })

        return {"response": info}, SUCCESS

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
            "hpath":  hpath
            }
        }, SUCCESS
