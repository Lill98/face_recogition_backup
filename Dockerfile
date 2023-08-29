FROM python:3.8-slim-buster
RUN apt-get update
RUN pip install --upgrade pip
RUN apt-get install ffmpeg libsm6 libxext6  -y

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# CMD python3
# CMD gunicorn main:app -w 5  --bind 0.0.0.0:5001
CMD python3 main.py
# -k uvicorn.workers.UvicornWorker

