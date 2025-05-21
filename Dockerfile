# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-add-repository -y "deb http://security.ubuntu.com/ubuntu xenial-security main" && \
    apt-get update && \
    apt-get install -y wkhtmltopdf && \
    apt-get clean


RUN pip install --upgrade pip


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
