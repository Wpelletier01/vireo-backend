from functools import wraps
from manager.server import Server

from flask import Flask, request, send_file, make_response, send_from_directory,abort
from datetime import datetime, timedelta

app = Flask(__name__)
server = Server()


@app.route("/signin", methods=['POST'])
def signin():
    return server.handle_signin(request.get_json(), request.remote_addr)


@app.route("/signup", methods=['POST'])
def signup():
    return server.handle_sign_up(request.get_json(), request.remote_addr)


@app.route("/upload", methods=['POST'])
def upload_video():
    return server.handle_upload(request.get_data(), dict(request.headers), request.remote_addr)


@app.route("/video/d/<string:hpath>")
def get_video(hpath: str):
    response, status = server.get_video(hpath)

    if status != 200:
        return response, status

    return send_file(response["response"])


@app.route("/video/<string:hpath>")
def get_video_info(hpath: str):
    return server.get_vinfo(hpath)


@app.route("/videos/<string:rtype>", methods=['GET'])
@app.route("/videos/<string:rtype>/<string:name>", methods=['GET'])
def get_videos(rtype: str, name: str | None = None):
    return server.retrieve_video_info(rtype, name)


@app.route("/thumbnails/<string:hpath>", methods=['GET'])
def get_thumbnails(hpath: str):
    url, response = server.get_thumbnail_path(hpath)

    if response != 200:
        return url, response

    return send_file(url["response"])


@app.route("/search/<string:stype>/<string:squery>")
def get_search_result(stype: str, squery: str):
    return server.handle_search(squery, stype)


if __name__ == "__main__":
    app.run(debug=True, port=8900)
