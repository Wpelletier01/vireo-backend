from functools import wraps
from manager.server import Server,VResponse

from flask import Flask, request, send_file, make_response, send_from_directory,abort
from datetime import datetime, timedelta

app = Flask(__name__)
server = Server(True)


@app.route("/signin", methods=['POST'])
def signin():
    return server.handle_signin(request.get_json())


@app.route("/signup", methods=['POST'])
def signup():
    return server.handle_sign_up(request.get_json(), request.remote_addr)


@app.route("/upload/v/<string:hpath>", methods=['POST'])
def upload_video(hpath: str):
    return server.upload_video(request.get_data(),hpath)

@app.route("/upload", methods=['POST'])
def upload_video_info():
    return server.handle_upload(dict(request.headers), request.get_json())


@app.route("/video/d/<string:hpath>")
def get_video(hpath: str):
    response = server.get_video_path(hpath)

    if isinstance(response, VResponse):
        return response.send()

    return send_file(response)


@app.route("/video/<string:hpath>")
def get_video_info(hpath: str):
    return server.get_vinfo(hpath)


@app.route("/videos/all", methods=['GET'])
@app.route("/videos/channel/<string:name>", methods=['GET'])
def get_videos(name: str | None = None):
    return server.retrieve_video_info(name)


@app.route("/thumbnails/<string:hpath>", methods=['GET'])
def get_thumbnails(hpath: str):

    response = server.get_thumbnail_path(hpath)

    if isinstance(response, VResponse):
        return response.send()

    return send_file(response)


@app.route("/search/<string:stype>/<string:squery>")
def get_search_result(stype: str, squery: str):
    return server.handle_search(squery, stype)


if __name__ == "__main__":
    app.run(debug=True, port=8900)
