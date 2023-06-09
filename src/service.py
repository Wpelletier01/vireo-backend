from functools import wraps
from manager.server import Server

from flask import Flask, request, send_file, make_response, send_from_directory,abort
from datetime import datetime, timedelta

app = Flask(__name__)
server = Server()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        code = server.process_token(request.headers, request.remote_addr)
        if code != 200:
            abort(code)

        return f(*args, **kwargs)

    return decorated


@app.route("/signin", methods=['POST'])
def signin():
    return server.handle_signin(request.get_json(),request.remote_addr)

@app.route("/signup", methods=['POST'])
def signup():
    return server.signup(request.get_json(),request.remote_addr)



if __name__ == "__main__":
    app.run(debug=True, port=8900)
