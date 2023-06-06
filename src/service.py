from functools import wraps
from manager.server import Server
from flask import Flask,request
from datetime import datetime, timedelta
import jwt

TMP_SECRET = "1dcd2fbc17612a8ef4b5c860ed951942989b76f612e952551f9f9865c8344c71"
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

@app.route("/upload",methods=['POST'])
def upload():

    if "video" in request.content_type:
        data = request.get_data()
        id_ = server.addVideo(data)
        print(id_)
        return id_
    elif "application/json":
        data = request.get_json()
        print(data)
        resp = server.handleVideo(data)
        print(resp)

        return resp
    

    #TODO: implement for other content type
    
    return "",400


if __name__ == "__main__":

    app.run(debug=True,port=8900)