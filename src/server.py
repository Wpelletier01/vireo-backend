
from db import DbClient
from flask import Flask,request


app = Flask(__name__)
db = DbClient(True)



@app.route("/login",methods=['POST'])
def login():

    data = request.get_json()
    
    if db.validate_logging(data['username'], data["password"]):
        return "success",200


    return "failed",401



if __name__ == "__main__":
    app.run(debug=True,port=8900)