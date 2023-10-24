FROM python:latest

WORKDIR /vireo-python 

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

COPY requirements.txt requirements.txt 

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 3000

WORKDIR src
CMD [ "mkdir", "../log"]

CMD [ "python3", "-m" , "flask", "run", "-p", "3000"]