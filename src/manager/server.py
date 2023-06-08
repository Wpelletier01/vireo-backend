from database.client import DbClient,DatabaseError
from manager.signin import SignInManager
from manager.signup import SignUpManager
from manager.upload import UploadManager
from manager.error import SignInError,SignUpError,SignInErrType,UploadErr
from datetime import datetime, timedelta

import os
import jwt

TMP_VIDEO = "../testdb/videos"
TMP_THUMB = "../testdb/thumbnails"
VIDEO_CHUNK = 20
TMP_SECRET = "1dcd2fbc17612a8ef4b5c860ed951942989b76f612e952551f9f9865c8344c71"

class Server:

    def __init__(self,inDevelopment:bool):

        self.db_client = DbClient()
        self.db_client.initiate_connection(inDevelopment)
        self.signin = SignInManager()
        self.signup = SignUpManager()
        self.upload = UploadManager()

    def handleSignIn(self,data):
        
        try:
            self.signin.handle(data, self.db_client)

            ctime = datetime.utcnow() + timedelta(hours=1)
            
            payload = {
                

            "username": data["username"],
            "password": data["password"],
            "expire": ctime.timestamp()

            
            }
            
            return { "token": jwt.encode(payload, TMP_SECRET) }

        except DatabaseError as e: 
            return e.msg,500
        
        except SignInError as e:
            
            if e.etype == SignInErrType.WrongPassword:    
                return e.msg,401

            return e.msg,400


    def handleSignUp(self,body:dict):
        
        try:
            self.signup.handle(body, self.db_client)
        
        except DatabaseError as e:
            return e.msg,500

        except SignUpError as e:
            return e.msg,400

        return "",200

    def addVideo(self,data):
        #TODO: validate size
        buffer_id = self.upload.pushToBuffer(data)
        print(buffer_id,flush=True)
        
        return {"buffer_id": buffer_id},200


    def handleVideo(self,data:dict):
        
        try:
            self.upload.handle(data, self.db_client)
            return "uploaded",200
        
        except UploadErr as e:
            print(e.msg,flush=True)
            return e.msg,400
        except DatabaseError as e:
            return "Database",500,


    def retreive_video_info(self,chunks:int):
        #TODO: check how we can join this function with getVideoInfo
        info = { "videos": [] }

        videos = self.db_client.queryForValue("""
            SELECT PathHash,ChannelID,Title
            FROM Videos;""")
        print(videos)
        i = 0
        
        while i < len(videos):

            if i >= (VIDEO_CHUNK*chunks):
                break

            hpath = videos[i][0]
            cid = videos[i][1]
            title = videos[i][2]

            channel = self.db_client.queryForValue(f"""
                SELECT Username
                FROM Channels
                WHERE ChannelID = '{cid}';

            """)[0][0]

            info["videos"].append({
                "thumbnail":    hpath,
                "channel":      channel,
                "title":        title,
                "hpath":        hpath
            })
        
            i+=1
        
        return info,200



    def getVideoInfo(self,hpath:str):

        #TODO: validate that hpath exist

        try:
            title,desc,date,cid = self.db_client.queryForValue(f"""
                    SELECT Title,Description,Upload,ChannelID
                    FROM Videos
                    WHERE PathHash = '{hpath}';""")[0]
        
        except IndexError: 
            return {"status": "NOT FOUND"},200 

        channel  = self.db_client.queryForValue(f"""
                SELECT Username
                FROM Channels
                WHERE ChannelID = '{cid}'""")[0][0]
            
        return {
            "status": "FOUND",
            "title":title,
            "channel":channel,
            "description": desc,
            "date": f"{date.year}-{date.month}-{date.day}"}, 200
            