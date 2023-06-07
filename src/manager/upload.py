from database.client import DbClient
from manager.error import UploadErr,UploadErrType

import os 
import random
import string
import cv2
import time

TMP_VIDEO = "testdb/videos"
TMP_THUMB = "testdb/thumbnails"

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
        print(f"buffer length: {len(self.buffer)}")
        return _id 

    
    def write(self,index:int,name:str): 

        print(f"index: {index}",flush=False)
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
            );"""
        )

        self.write(data["buffer_id"], path)

        

        self.choose_thumbnails(path)
        

    def get_video_length(self,name): 
        #TODO: make sure that the video exist
        video = cv2.VideoCapture(os.path.join(TMP_DIR,f"{name}.mp4"))
        
        frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = video.get(cv2.CAP_PROP_FPS)
        print(f"frames: {frames}")
        print(f"fps: {fps}")

        return round(frames / fps)

    def choose_thumbnails(self,name:str):

        #TODO: make sure that the video exist
        video = cv2.VideoCapture(os.path.join(TMP_DIR,f"{name}.mp4"))
  
    
        frames = video.get(cv2.CAP_PROP_FRAME_COUNT)    
        frame_id = random.randint(0, frames)
    
        
        print(f"frame id: {frame_id}")

        video.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

        success,frame = video.read()

        cv2.imwrite(os.path.join(TMP_THUMB,f"{name}.png"),frame)

     

