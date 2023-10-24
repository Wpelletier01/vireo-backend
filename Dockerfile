FROM python:latest

WORKDIR /vireo-python 


COPY vireo-backend/requirements.txt requirements.txt 

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 3000

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "-p", "3000"]