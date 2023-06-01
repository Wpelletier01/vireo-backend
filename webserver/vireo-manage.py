
from flask import Flask



app = Flask(__name__)


@app.route("/",method=['GET'])
def get_root():
    return "../" 