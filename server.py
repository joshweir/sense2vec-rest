#!/usr/bin/python3

import os
from flask import Flask, request, Response
import json
import datetime
from sense2vec import Sense2Vec
import re
from textblob import Word

app = Flask(__name__)
port = 80 if os.getuid() == 0 else 8000

s2v = Sense2Vec().from_disk("/sense2vec-model/sense2vec-vectors")
s2v_noun_tags = [
    'PROPN', 'NOUN', 'NUM', 'PERSON', 'NORP', 'FACILITY', 'ORG', 'GPE', 'LOC',
    'PRODUCT', 'EVENT', 'LANGUAGE', 'WORK_OF_ART'
]
s2v_adj_tags = ['ADJ']
s2v_verb_tags = ['VERB']


def lemma_word_tag(s2v_tag):
  if s2v_tag in s2v_adj_tags:
    return 'a'

  if s2v_tag in s2v_verb_tags:
    return 'v'

  return 'n'


# pos_tag: 'a', 'n', 'v'
def get_lemma(word, pos_tag):
  return Word(word).lemmatize(lemma_word_tag(pos_tag))


# PROPN, NOUN, NUM, PERSON, NORP, FACILITY, ORG, GPE, LOC, PRODUCT, EVENT, LANGUAGE, WORK_OF_ART
# ADJ
# VERB
def s2v_transform(d):
  results = [{
      'value': v[0],
      'score': float(v[1])
  } for v in s2v.most_similar(d, n=10)]

  return results


@app.route('/', methods=['POST', 'GET'])
def index():
  start = datetime.datetime.utcnow()
  data = request.data.decode('utf-8')
  if not data:
    return Response(status=500, response="no data")

  # print("got something: '%s'" % data)
  parsed = json.loads(data)

  try:
    result = s2v_transform(parsed)
  except Exception as e:
    err = str(e)
    if err.find("Can't find key") != -1:
      # if parsed is a string (single key) and it doesnt contain _ (its single word)
      # and is all lowercase a-z try uppercase version
      if isinstance(parsed, str) and re.search(r'^[a-z]+$',
                                               parsed.split('|')[0]):
        term, sense = parsed.split('|')
        try:
          result = s2v_transform("{0}|{1}".format(term.upper(), sense))
        except Exception as e2:
          err2 = str(e2)
          if err2.find("Can't find key") != -1:
            result = []
          else:
            raise
      else:
        result = []
    else:
      raise

  fin = datetime.datetime.utcnow()
  print(fin - start, 'req time')
  # print('result ', result)

  return Response(
      status=200, response=json.dumps(result), content_type="application/json")


if __name__ == '__main__':
  app.run(port=port, host="0.0.0.0")
