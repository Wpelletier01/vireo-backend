from flask import Flask, request, send_file
from manager.server import Server, VResponse

import time

app = Flask(__name__)
server = Server(True)


@app.route("/signin", methods=['POST'])
def signin():
    if not request.is_json:
        return {"response": "bad-content-type"}, 400

    return server.handle_signin(request.get_json(), request.remote_addr).send()


@app.route("/signup", methods=['POST'])
def signup():
    return server.handle_sign_up(request.get_json()).send()


@app.route("/upload/v/<string:hpath>", methods=['POST'])
def upload_video(hpath: str):
    return server.upload_video(request.get_data(), str(request.headers["Authorization"]), hpath).send()


@app.route("/upload", methods=['POST'])
def upload_video_info():
    return server.handle_upload(str(request.headers["Authorization"]), request.get_json()).send()


@app.route("/video/d/<string:hpath>")
def get_video(hpath: str):
    response = server.get_video_path(hpath)

    if isinstance(response, VResponse):
        return response.send()

    return send_file(response)


@app.route("/v/<string:hpath>")
def get_video_info(hpath: str):
    return server.get_vinfo(hpath).send()


@app.route("/videos/all", methods=['GET'])
@app.route("/videos/channel/<string:name>", methods=['GET'])
def get_videos(name: str | None = None):
    return server.retrieve_video_info(name).send()


@app.route("/thumbnails/<string:hpath>", methods=['GET'])
def get_thumbnails(hpath: str):
    response = server.get_thumbnail_path(hpath)

    if isinstance(response, VResponse):
        return response.send()

    return send_file(response)


@app.route("/search/<string:stype>/<string:squery>")
def get_search_result(stype: str, squery: str):
    return server.handle_search(squery, stype).send()


@app.route("/channel/picture/<string:name>", methods=["GET"])
def get_channel_picture(name: str):
    time.sleep(0.5)
    resp = server.get_channel_img_path(name)

    if resp.status != 200:
        return resp.send()


    return send_file(resp.response['response'])


if __name__ == "__main__":
    app.run(debug=True, port=8900)
