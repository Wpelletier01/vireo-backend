import os 
from database.client import DbClient
from manager.error import UploadErr,UploadErrType

import random
import string

TMP_DIR = "videodb-tmp/"

UPLOAD_KEY = [
    "title",
    "description",
    "date",
    "length",
    "video",
]


class UploadManager:

    def __init__(self):

        self.buffer = []

    def __validateJsonBody(self,data:dict,expect_key:list):
        
        for key in expect_key:

            found = False
        
            if key in data.keys():
                found = True

            if not found: 
                raise SignUpReqError(UploadErrType.MissingField,key) 


    def pushToBuffer(self,data):

        _id = len(self.buffer)

        self.buffer.append(data)

        return _id 

    
    def write(self,data,name:str): 

        with open(os.path.join(TMP_DIR,f"{name}.mp4"),"wb") as f:    
            f.write(data)
            f.close()


    def handle(self,data:dict,uploader:str,db_client:DbClient):
        
        self.__validateJsonBody(data, UPLOAD_KEY)

        path = "".join(
            random.choice(
                string.ascii_lowercase + string.ascii_lowercase + string.digits,
                k=7
                )
            )

    
        channelID = db_client.queryForValue(f"""
            SELECT ChannelID FROM Channels WHERE Username = '{uploader}';""")[0][0]

        self.write(data["buffer_id"], path)

        db_client.insert(f"""

            INSERT INTO Videos(
                PathHash,
                ChannelID,
                Title,
                Length,
                Description,
                Upload
            )
            VALUE (
                '{path}',
                '{channelID}',
                '{data["title"]}',
                '{data["length"]}',
                '{data["description"]}',
                Date('{data["date"]}')
            )"""
        )
        print("insert")
        self.write(data["video"], path) 
        print("upload")