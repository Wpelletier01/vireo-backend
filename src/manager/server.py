#! /usr/bin/env python3
#
# Date:     10 jun 2023
# Author:   William Pelletier
# Email:    wpelletier.development@yahoo.com
#

from database.client import DbClient
from manager.vconf import validate_config_file
from manager.login import Login_manager, LResponse, Source_info, BLOCKED
from datetime import datetime, timedelta
from dataclasses import dataclass

# import logging
import jwt
import bcrypt
import configparser
import os
import random
import string
import cv2

# http error code
SUCCESS = 200
BAD_REQUEST = 400
UNAUTHORIZED = 401
FORBIDDEN = 403
INTERNAL_ERROR = 500
NOT_FOUND = 404

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


@dataclass
class ResponseBody:
    """
    Universal response body that describe a database entry video or channel
    @param stype: video or channel
    @param channel: the username
    @param title: title if its video
    @param thumbnail: hash path of a video or channel name
    @param upload: date when video has been uploaded
    @param description: description of the video
    @param nb_video: number of video that a channel has uploaded
    """
    stype: str
    channel: str
    title: str | None
    thumbnail: str
    upload: str | None
    description: str | None
    nb_video: int | None

    def asDict(self) -> dict:
        """ Put info into a dictionary for been place in the body request """
        return {
            "type": self.stype,
            "channel": self.channel,
            "title": self.title if self.title else "",
            "thumbnail": self.thumbnail,
            "nb_count": self.nb_video if self.nb_video else "",
            "upload": self.upload if self.upload else "",
            "description": self.description if self.description else ""
        }

    @classmethod
    def empty(cls) -> dict:
        return {
            "type": "",
            "channel": "",
            "title": "",
            "thumbnail": "",
            "nb_count": "",
            "description": "",
            "upload": ""
        }


class VResponse:
    def __init__(self, status: int, response: str | dict | list = "", headers: dict | None = None):
        """
        Initialise the VResponse class
        @param status: The http code
        @param response: message/body to be sent in a response
        @param headers: header value to be sent
        """
        self.status = status
        self.response = {"response": response}
        self.headers = headers

    def send(self) -> tuple:
        """ set the response value a way that Flask will understand"""
        if self.headers is not None:
            return self.response, self.status, self.headers.items()
        return self.response, self.status


def _validate_body(body: dict, keys: list) -> str | None:
    """
    Make sure that all the filed needed are there to be found

    @param body: The request body that needs to be validated
    @param keys: the keys that need to be found in the body
    @return: None if all keys are found, otherwise return the key missing
    """
    for key in keys:
        found = False

        if key in body.keys():
            found = True

        if not found:
            return key

    return None


class Server:

    def __init__(self, dev_mod: bool):
        """ initialize the Server class"""

        # gather all important config value
        self.__config = configparser.ConfigParser()
        self.__config.read("config.ini")
        # validate his content
        validate_config_file(self.__config)

        if dev_mod:

            self.__srv_conf = self.__config['DEVELOPMENT']
        else:
            self.__srv_conf = self.__config['PRODUCTION']

        # Where the server log would be
        slogfile = os.path.join(self.__srv_conf['log-dir'], "server.log")

        if not os.path.exists(slogfile):
            open(slogfile, 'a').close()

        # logging.basicConfig(filename=slogfile, filemode="a")
        # Create and start a connection with the database
        dlogfile = os.path.join(self.__srv_conf['log-dir'], "log/db.log")
        self.db_client = DbClient(dict(self.__config["DATABASE"]), dlogfile)
        self.db_client.initiate_connection()

        # secret and algorithm used for encode and decode jwt token
        self.__secret = self.__config["TOKEN"]["secret"]
        self.__alg = self.__config["TOKEN"]["algorithm"]

        self.__login_manager = Login_manager()

    def __process_token(self, auth: str) -> VResponse:
        """
        gather a request's header to extract a jwt token and validate his content
        @param header: the header of a rest request
        @return: VResponse with the status of the process
        """

        if auth == "":
            return VResponse(BAD_REQUEST, "token")

        # decode the token
        try:
            payload = jwt.decode(auth, key=self.__secret, algorithms=self.__alg)

        except jwt.ExpiredSignatureError:
            return VResponse(UNAUTHORIZED, "token expire")
        print(payload, flush=True)

        username = payload["username"]
        password = payload["password"]

        # make sure that a channel with the username in the payload exists
        hpasswd_resp = self.db_client.query(f"""
            SELECT Password FROM Channels WHERE USERNAME = '{username}';""")

        if hpasswd_resp is None:
            return VResponse(INTERNAL_ERROR)

        try:
            hpasswd = hpasswd_resp[0][0]

        except IndexError:
            return VResponse(BAD_REQUEST, "bad-token-username")

        # validate that the password in the payload is valid
        if password != hpasswd:
            return VResponse(BAD_REQUEST, "bad-token-password")

        return VResponse(SUCCESS, payload)

    def __gen_token(self, username: str, hpasswd: str, nb_hr: int = 3) -> str:
        """
        Generate a new token for a user after sign in
        @param username: name of the user
        @param hpasswd:  his hashed password
        @param nb_hr:  how long should it be valid
        @return: the token generated
        """

        expire = (datetime.now() + timedelta(hours=nb_hr)).timestamp()

        payload = {
            "username": username,
            "password": hpasswd,
            "exp": expire
        }

        return jwt.encode(payload, self.__secret, algorithm=self.__alg)

    def __query_video(self, query: str) -> VResponse:
        """
        Try to found videos that contains the query in the database
        @param query: value of the research
        @return: the result of the research if not failed
        """

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
            response.append(ResponseBody('video', video[1], video[0], video[2], None, None, None).asDict())

        return VResponse(SUCCESS, response)

    def __query_channel(self, query: str) -> VResponse:
        """
        Try to found channels that contains the query in the database
        @param query: value of the research
        @return: the result of the research if not failed
        """

        # return channel name and the number of videos it has
        search_query = f"""
            SELECT c.Username, v.PathHash, v.Upload, COUNT(v.VideoID)
            FROM Channels c
            JOIN Videos v ON v.ChannelID = c.ChannelID
            WHERE Username like '%{query}%';"""

        channels = self.db_client.query(search_query)

        if channels is None:
            return VResponse(INTERNAL_ERROR)

        if channels[0][3] == 0:
            return VResponse(SUCCESS, [])
        response = []

        for channel in channels:
            response.append(
                ResponseBody('channel', channel[0], None, channel[1], channel[2], None, channel[3]).asDict()
            )

        return VResponse(SUCCESS, response)

    def __create_thumbnail(self, fp: str, hash_path: str):
        """
        Take a random frame of a video to be used has a thumbnail for a video
        @param fp: the path of the video that need a thumbnail
        @param hash_path: the hashed path of a video
        """

        # TODO: resize for best thumbnails

        video = cv2.VideoCapture(fp)

        if not video.isOpened():
            raise Exception("Unable to load video")

        frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
        frame_id = random.randint(0, frames)

        video.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

        success, frame = video.read()

        tmp_img = os.path.join(self.__srv_conf["tmp-dir"], f"{hash_path}.png")

        cv2.imwrite(tmp_img, frame)

    def handle_signin(self, data: dict, ipaddr: str) -> VResponse:
        """
        Handle the request by client to login
        @param ipaddr: ip address of the request
        @param data: body of the request
        @return: response with a jwt token generated
        """

        key = _validate_body(data, ["username", "password"])
        if key is not None:
            return VResponse(BAD_REQUEST, {"response": {"missing-field": key}})

        source = Source_info(ipaddr, data['username'])

        lresp = self.__login_manager.can_try(source)

        if lresp.status == BLOCKED:
            return VResponse(FORBIDDEN, lresp.data)

        result = self.db_client.query(f"""
            SELECT Username,Password 
            FROM Channels
            WHERE Username = '{data['username']}';""")

        if result is None:
            return VResponse(INTERNAL_ERROR)

        try:
            username, hpassword = result[0]
        except IndexError:
            d = self.__login_manager.add_attempt(source)
            return VResponse(UNAUTHORIZED, d.data)

        if not bcrypt.checkpw(data["password"].encode('utf-8'), hpassword.encode('utf-8')):
            d = self.__login_manager.add_attempt(source)
            return VResponse(UNAUTHORIZED, d.data)

        self.__login_manager.remove_user(source)

        return VResponse(SUCCESS, {"vtoken": self.__gen_token(username, hpassword)})

    def handle_sign_up(self, data: dict) -> VResponse:
        """
        Handle request for create new account
        @param data: the body with the information to create an account
        @return: a success response if everything went fine
        """

        key = _validate_body(data, SIGNUP_KEY)
        if _validate_body(data, SIGNUP_KEY) is not None:
            return VResponse(BAD_REQUEST, {"missing-key": key})

        response = self.db_client.query(f"""
                SELECT Username
                FROM Channels
                WHERE Username = '{data["username"]}';""")

        if response is None:
            return VResponse(INTERNAL_ERROR)

        if len(response) > 0:
            return VResponse(BAD_REQUEST, "username")

        email_response = self.db_client.query(f"""
            SELECT Email
            FROM ChannelDetails
            WHERE Email = '{data["email"]}';""")

        if email_response is None:
            return VResponse(INTERNAL_ERROR)

        if len(email_response) > 0:
            return VResponse(BAD_REQUEST, "password")

        middle_name = f"'{data['mname']}'" if data["mname"] else "NULL"

        birthday = datetime(data["year"], data["month"], data["day"])

        salt = bcrypt.gensalt(rounds=14)
        passwd = bcrypt.hashpw(data["password"].encode('utf-8'), salt)

        response = self.db_client.query("""SELECT COUNT(ChannelID) FROM Channels;""")

        if response is None:
            return VResponse(INTERNAL_ERROR)

        _id = response[0][0] + 1

        insert1 = f"""
            INSERT INTO Channels (
                ChannelID,
	            Username,
                Password
            )
            VALUES 
            ( '{_id}','{data["username"]}','{passwd.decode('utf-8')}');"""

        resp_i1 = self.db_client.insert(insert1)

        if resp_i1 is None:
            return VResponse(INTERNAL_ERROR)

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
                '{data["fname"]}',
                {middle_name},
                '{data["lname"]}',
                '{data["email"]}',
                Date('{birthday.isoformat()}'));"""

        resp_i2 = self.db_client.insert(insert2)

        if resp_i2 is None:
            return VResponse(INTERNAL_ERROR)

        return VResponse(SUCCESS)

    def upload_video(self, data: bytes, auth: str, hpath: str) -> VResponse:
        """
        upload a video to the server
        @param auth: the token
        @param data: the video
        @param hpath: the unique hashed path of the video
        @return: status of the request
        """
        payload = self.__process_token(auth)

        if payload.status != SUCCESS:
            return payload

        fp = os.path.join(self.__srv_conf["db-dir"], f"videos/{hpath}.mp4")

        with open(fp, "wb") as f:
            f.write(data)
            f.close()

        try:
            self.__create_thumbnail(fp, hpath)

        except Exception:
            return VResponse(INTERNAL_ERROR)

        return VResponse(SUCCESS)

    def handle_upload(self, auth: str, body: dict) -> VResponse:
        """
        handle request for adding new video
        @param auth: the token
        @param body: the info about the video
        @return: the status of the request
        """
        payload = self.__process_token(auth)

        if payload.status != SUCCESS:
            return payload

        key = _validate_body(body, ["title", "description"])
        if key is not None:
            return VResponse(BAD_REQUEST, {"missing-key": key})

        possibility = string.ascii_lowercase + string.ascii_lowercase + string.digits
        hpath = "".join(random.choice(possibility) for _ in range(7))
        channel = payload.response["response"]["username"]

        print("first", flush=True)
        resp_cid = self.db_client.query(
            f"""SELECT ChannelID FROM Channels WHERE Username = '{channel}';""")

        if resp_cid is None:
            return VResponse(INTERNAL_ERROR)

        channel_id = resp_cid[0][0]

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
                '{body["title"]}',
                '{body["description"]}',
                Date('{datetime.now().isoformat()}')
            );"""
        print("second", flush=True)
        resp = self.db_client.insert(insert)

        if resp is None:
            return VResponse(INTERNAL_ERROR)

        return VResponse(SUCCESS, hpath)

    def retrieve_video_info(self, name: str | None) -> VResponse:
        """
        Retrieve video info store in the database
        @param name: a channel name if None we return all videos
        @return: a response with all the info found
        """

        query = """
            SELECT v.PathHash, v.Title, c.Username, v.Upload
            FROM Videos v
            JOIN Channels c ON v.ChannelID = c.ChannelID"""

        if name is not None:
            query = f"""{query}\nWHERE c.Username = '{name}';"""

        info = []

        videos = self.db_client.query(query)

        if videos is None:
            return VResponse(INTERNAL_ERROR)

        if len(videos) == 0:
            return VResponse(BAD_REQUEST, "no-channel")

        for video in videos:
            info.append(
                ResponseBody('video', video[2], video[1], video[0], video[3], None, None).asDict()
            )

        return VResponse(SUCCESS, info)

    def handle_search(self, squery: str, stype: str) -> VResponse:
        """
        handle a search query in the database
        @param squery: the value to found
        @param stype: either all or channel
        @return: a response with the info found
        """

        response = []
        # TODO: add duration of info return
        # TODO: make different type of query like for only channel
        match stype:
            case "all":
                videos_req = self.__query_video(squery)

                if videos_req.status != SUCCESS:
                    return videos_req

                videos = videos_req.response

                for video in videos["response"]:
                    response.append(video)

                channel_req = self.__query_channel(squery)

                if channel_req.status != SUCCESS:
                    return channel_req

                channels = channel_req.response

                for channel in channels["response"]:
                    response.append(channel)

            case _:
                return VResponse(BAD_REQUEST, "bad-search-type")

        return VResponse(SUCCESS, response)

    def get_thumbnail_path(self, hpath: str) -> str | VResponse:
        """
        found and return the path of the picture of a thumbnail video
        @param hpath: the hash path of the video that needs his thumbnail
        @return: the path of the thumbnail or an error response
        """
        thumbnails_dir = os.path.join(self.__srv_conf["db-dir"], "thumbnails")

        if f"{hpath}.png" not in os.listdir(thumbnails_dir):
            return VResponse(BAD_REQUEST, "no-thumbnails")

        return os.path.join(thumbnails_dir, f"{hpath}.png")

    def get_video_path(self, hpath: str) -> str | VResponse:
        """
        Found and return the path of the video in the server
        @param hpath: the hash path of the video
        @return: the path or an error response
        """
        videos_dir = os.path.join(self.__srv_conf['db-dir'], "videos")

        if f"{hpath}.mp4" not in os.listdir(videos_dir):
            return VResponse(BAD_REQUEST, "no-video")

        url = os.path.join(videos_dir, f"{hpath}.mp4")

        return url

    def get_vinfo(self, hpath: str) -> VResponse:
        """
        gather info of a specific video in the database
        @param hpath: the hash path of the video
        @return: response with the info found
        """
        query = f"""
            SELECT v.Title,c.Username,v.Description,v.Upload
            FROM Videos v
            JOIN Channels c ON v.ChannelID = c.ChannelID
            WHERE PathHash = '{hpath}';"""

        resp = self.db_client.query(query)
        if resp is None:
            return VResponse(INTERNAL_ERROR)

        if len(resp) != 0:
            vinfo = resp[0]
            info = ResponseBody('video', vinfo[1], vinfo[0], hpath, vinfo[3], vinfo[2], None).asDict()
            return VResponse(SUCCESS, info)

        return VResponse(NOT_FOUND)

    def get_channel_img_path(self, cname: str):

        query = f"""
        SELECT ChannelID 
        FROM Channels
        WHERE Username = '{cname}';"""
        resp = self.db_client.query(query)

        if resp is None:
            return VResponse(INTERNAL_ERROR)

        if len(resp) == 0:
            return VResponse(NOT_FOUND)

        url = os.path.join(self.__srv_conf['db-dir'], f"cpicture/c{resp[0][0]}.jpg")

        return VResponse(SUCCESS, url)

    def delete_account(self, auth: str) -> VResponse:

        payload, result = self.__process_token(auth)

        if result != SUCCESS:
            return VResponse(result, payload)

        q1 = f"""
        SELECT ChannelID 
        FROM Channels 
        WHERE Username = {payload["username"]};"""

        response = self.db_client.query(q1)

        if response is None:
            return VResponse(INTERNAL_ERROR)

        _id = response[0][0]

        del_channel_info = self.db_client.query(
            f"""
                DELETE from ChannelDetails
                WHERE ChannelID = {_id};"""
        )

        if del_channel_info is None:
            return VResponse(INTERNAL_ERROR)

        del_channel = self.db_client.query(
            f"""DELETE from Channels
                WHERE ChannelID = {_id};"""
        )

        if del_channel is None:
            return VResponse(INTERNAL_ERROR)

        return VResponse(SUCCESS)

    def delete_video(self, hpath: str, auth: str) -> VResponse:

        payload = self.__process_token(auth)

        if payload.status != 200:
            return payload

        channel = payload.response["repsonse"]["username"]

        q1 = f"""
            SELECT c.Username
            FROM Channels c
            JOIN Videos v ON v.ChannelID = c.ChannelID
            WHERE v.PathHash = '{hpath}';"""

        channel_resp = self.db_client.query(q1)

        if channel_resp is None:
            return VResponse(INTERNAL_ERROR)

        if channel_resp != channel:
            return VResponse(UNAUTHORIZED)

        q2 = f"""
            DELETE from Videos
            WHERE PathHash = {hpath};"""

        del_resp = self.db_client.query(q2)
        if del_resp is None:
            return VResponse(INTERNAL_ERROR)

        return VResponse(SUCCESS)
