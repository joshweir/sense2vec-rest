#!/usr/bin/python3

import os
from flask import Flask, request, Response
import json
import datetime
from sense2vec import Sense2Vec
from s2v_util import S2vUtil
from s2v_similarity import S2vSimilarity
from s2v_synonyms import S2vSynonyms

app = Flask(__name__)
port = 80 if os.getuid() == 0 else 8000

print("loading model from disk..")
s2v = Sense2Vec().from_disk("/sense2vec-model")
print("model loaded.")
s2v_util = S2vUtil(s2v)
similarity_service = S2vSimilarity(s2v_util)
synonyms_service = S2vSynonyms(s2v_util)


@app.route('/', methods=['POST', 'GET'])
def index():
  start = datetime.datetime.utcnow()
  data = request.data.decode('utf-8')
  if not data:
    return Response(status=500, response="no data")

  if os.getenv('S2V_VERBOSE'):
    print("request body: '%s'" % data)
  parsed = json.loads(data)

  results = []
  for item in parsed:
    result = synonyms_service.call(item, request.args)
    results.append(result)

  fin = datetime.datetime.utcnow()
  print(fin - start, 'req time')
  # print('result ', result)

  return Response(
      status=200, response=json.dumps(results), content_type="application/json")


@app.route('/similarity', methods=['POST', 'GET'])
def similarity():
  start = datetime.datetime.utcnow()
  data = request.data.decode('utf-8')
  if not data:
    print('no data in request body!')
    return Response(status=500, response="no data")

  if os.getenv('S2V_VERBOSE'):
    print("request body: '%s'" % data)
  parsed = json.loads(data)

  results = []
  for item in parsed:
    result = similarity_service.call(item[0], item[1], request.args)
    results.append(result)

  fin = datetime.datetime.utcnow()
  print(fin - start, 'req time')
  # print('result ', result)

  return Response(
      status=200, response=json.dumps(results), content_type="application/json")


if __name__ == '__main__':
  app.run(port=port, host="0.0.0.0")
