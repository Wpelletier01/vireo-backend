
from flask import Flask,request


app = Flask(__name__)




@app.route("/test",methods=['POST'])
def test():

    data = request.get_json()
    

    print(data,flush=False)


    return f"username: {data['username']} password: {data['password']}"



if __name__ == "__main__":
    app.run(debug=True,port=8900)