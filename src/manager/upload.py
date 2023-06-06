import os 
from database.client import DbClient
from manager.error import UploadErr,UploadErrType

import random
import string

TMP_DIR = "videodb-tmp/"

UPLOAD_KEY = [
    "uploader", #TODO: tmp until token system setup
    "title",
    "description",
    "date",
    "buffer_id"
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
                raise UploadErr(UploadErrType.MissingField,key) 


    def pushToBuffer(self,data):

        _id = len(self.buffer)

        self.buffer.append(data)

        return _id 

    
    def write(self,index:int,name:str): 

        data = self.buffer[index]

        with open(os.path.join(TMP_DIR,f"{name}.mp4"),"wb") as f:    
            f.write(data)
            f.close()


    def handle(self,data:dict,db_client:DbClient):
        #TODO: validate that the path is unique
        #TODO: prevent file too big

        self.__validateJsonBody(data, UPLOAD_KEY)

        possibility = string.ascii_lowercase + string.ascii_lowercase + string.digits
        path = "".join(random.choice(possibility) for c in range(7))

    
        channelID = db_client.queryForValue(f"""
            SELECT ChannelID FROM Channels WHERE Username = '{data["uploader"]}';""")[0][0]

        print(data["buffer_id"],flush=True)

        db_client.insert(f"""

            INSERT INTO Videos(
                PathHash,
                ChannelID,
                Title,
                Description,
                Upload
            )
            VALUE (
                '{path}',
                '{channelID}',
                '{data["title"]}',
                '{data["description"]}',
                Date('{data["date"]}')
            )"""
        )
        
        self.write(data["buffer_id"], path)