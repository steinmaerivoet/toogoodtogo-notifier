FROM python:3.8

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/ .
COPY tgtg.conf .

CMD ["python", "-u", "./main.py"]