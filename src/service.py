
from manager.server import Server
from flask import Flask,request
  
app = Flask(__name__)  
server = Server(True) 


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

    
    server.handleAuthToken(request.headers["authorization"])

    return "",200


if __name__ == "__main__":

    app.run(debug=True,port=8900)