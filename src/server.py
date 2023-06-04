
from database.client import DbClient, InsertAccountErr

from signup import handle_signup_request,SignUpReqError
from flask import Flask,request


app = Flask(__name__)

db = DbClient()


@app.route("/login",methods=['POST'])
def login():

    data = request.get_json()
    
    if db.validate_logging(data['username'], data["password"]):
        return "success",200
    return "failed",401

@app.route("/signup",methods=['POST'])
def signup():

    data = request.get_json()

    try:
        handle_signup_request(data,db_client)

    except InsertAccountErr:
        return "",500
    except SignUpReqError:
        return "",400

    return "",200


if __name__ == "__main__":


    db_client = DbClient()
    db_client.initiate_connection(True)
    app.run(debug=True,port=8900)