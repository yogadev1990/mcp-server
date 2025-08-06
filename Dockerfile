FROM python:3.11-slim

RUN pip install --upgrade pip
WORKDIR /app

COPY manager/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY manager /app

EXPOSE 2005

CMD ["python", "app.py"]
