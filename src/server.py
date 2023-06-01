
from flask import Flask


app = Flask(__name__)




@app.route("/test")
def test():
    return "this a test"



if __name__ == "__main__":
    app.run(debug=True,port=8900)