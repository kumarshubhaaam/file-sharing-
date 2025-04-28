FROM python:3.10-slim-buster

RUN apt-get update && apt-get install -y git

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
