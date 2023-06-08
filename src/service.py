from functools import wraps
from manager.server import Server
from flask import Flask,request,send_file,make_response,send_from_directory
from datetime import datetime, timedelta

import jwt
import os 
import time

TMP_SECRET = "1dcd2fbc17612a8ef4b5c860ed951942989b76f612e952551f9f9865c8344c71"
TMP_VIDEO = "testdb/videos"
TMP_THUMB = "testdb/thumbnails"
ALG = "HS256"

app = Flask(__name__)  
server = Server(True) 


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        
    
        
        token =  request.headers["Authorization"].split(" ")[1]
        payload = jwt.decode(token,key=TMP_SECRET,algorithms=ALG)

        if datetime.now().timestamp() >= payload["expire"]:
            return  {"reason": "expire"},404
        
        print(request.get_json(),flush=False)

        return f(payload, *args, **kwargs)

    return decorated

@app.route("/signin",methods=['POST'])
def signin():
    resp = server.handleSignIn(request.get_json())
    print(resp)
    return resp


@app.route("/signup",methods=['POST'])
def signup():
    resp = server.handleSignUp(request.get_json())
    print(resp)
    return resp

@app.route("/upload/video",methods=['POST'])
def upload():

    data = request.get_data()
    id_ = server.addVideo(data)
    print(id_)
    return id_
    
    
   
@app.route("/upload/videoinfo",methods=['POST'])
def uploadvideoinfo():
    time.sleep(3)
    data = request.get_json()
    print(data)
    resp = server.handleVideo(data)
    print(resp)

    return resp


@app.route("/videos",methods=["GET"])
def home_video():
    
    data = server.retreive_video_info()

    print(data)
    return data 

@app.route("/thumbnail/<string:hpath>",methods=["GET"])
def get_thumbnail(hpath):
    return send_file(os.path.join(TMP_THUMB,f"{hpath}.png"))

@app.route("/video/<string:hpath>")
def getVideo(hpath): 

    return make_response(send_from_directory(TMP_VIDEO, f"{hpath}.mp4"))

@app.route("/video/info/<string:hpath>")
def getVideoInfo(hpath):
    return server.getVideoInfo(hpath)

@app.route("/channel/videos/<string:channel>",methods=["GET"])
def getChannelVideos(channel):
    data = server.getChannelVideo(channel)
    print(data)
    return data

@app.route("/search/<string:stype>/<string:query>")
def search(stype,query):
    print("holdup")
    data = server.search(stype,query)
    print(data)
    return data
    


if __name__ == "__main__":

    app.run(debug=True,port=8900)