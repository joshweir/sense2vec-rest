FROM python:3.7

RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    # supervisor \
    curl \
    nginx \
    python-dev \
    git &&\
    apt-get -q clean -y && rm -rf /var/lib/apt/lists/* && rm -f /var/cache/apt/*.bin

RUN mkdir /sense2vec-model
RUN mkdir /app

RUN [ -f /app/sense2vec-vectors.zip ] || \
  wget -O /app/sense2vec-vectors.zip https://github.com/explosion/sense2vec/releases/download/v1.0.0a2/sense2vec-vectors.zip

RUN unzip /app/sense2vec-vectors.zip -d /sense2vec-model
RUN rm -rf /app/sense2vec-vectors.zip

RUN pip install textblob
RUN python -m textblob.download_corpora

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

ADD . /app

CMD gunicorn --bind 0.0.0.0:80 \
  --worker-tmp-dir /dev/shm \
  --workers=2 --threads=4 --worker-class=gthread \
  --log-file=- \
  wsgi:app
