from database.container import UserInfo
from database.client import DbClient

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

class SignUpReqError(Exception):
    def __init__(self):
        super().__init__("Invalid Json body")


def __validSignUpJson(data:dict) -> bool:

    for key in SIGNUP_KEY:

        found = False
        
        if key in data.keys():
            found = True

        if not found: 
            return False
    
    return True


def handle_signup_request(data:dict,client:DbClient): 

    if not __validSignUpJson(data):

        raise SignUpReqError()

    middle_name = data["mname"]

    if middle_name == "":
        middle_name = None

    birthday = f"{data['year']}-{data['month']}-{data['day']}"

    info = UserInfo(
        data["username"], 
        data["password"], 
        data["fname"], 
        data["mname"], 
        data["lname"], 
        data["email"],
        birthday
        )

    client.insertNewAccount(info)