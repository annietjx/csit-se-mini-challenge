FROM python:3.8-slim-buster

WORKDIR /python-docker

COPY app.py app.py
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
EXPOSE 8080

CMD [ "python3", "app.py"]
