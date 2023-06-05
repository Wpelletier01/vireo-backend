from database.client import DbClient,DatabaseError
from manager.signin import SignInManager
from manager.signup import SignUpManager
from manager.error import SignInError,SignUpError,SignInErrType
from datetime import datetime, timedelta

import jwt

TMP_SECRET = "1dcd2fbc17612a8ef4b5c860ed951942989b76f612e952551f9f9865c8344c71"
ALG = "HS256"

class Server:

    def __init__(self,inDevelopment:bool):

        self.db_client = DbClient()
        self.db_client.initiate_connection(inDevelopment)
        self.signin = SignInManager()
        self.signup = SignUpManager()

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

        return token,200


    def tokenExpire(self,expire_time:float) -> bool:

        if datetime.now().timestamp() >= expire_time:
            return True
        
        return False


    def handleAuthToken(self,auth:str):

        token = auth.split(" ")[1]
        payload = jwt.decode(token,key=TMP_SECRET,algorithms=ALG)

        if self.tokenExpire(payload["expire"]):

            return "expire",400
        
        return "success",200


