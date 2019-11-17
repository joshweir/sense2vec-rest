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
    'PRODUCT', 'EVENT', 'LANGUAGE', 'WORK_OF_ART', 'n'
]
s2v_adj_tags = ['ADJ', 'a']
s2v_verb_tags = ['VERB', 'v']


def get_generic_sense(sense):
  if sense in s2v_adj_tags:
    return 'a'

  if sense in s2v_verb_tags:
    return 'v'

  if sense in s2v_noun_tags:
    return 'n'

  return 'unknown'


def get_lemma(word, pos_tag):
  tag = get_generic_sense(pos_tag)
  if (tag == 'unknown'):
    return Word(word).lemmatize()

  return Word(word).lemmatize(tag)


def is_single_word(text):
  return text.find("_") == -1


def is_downcase_alpha(text):
  return re.search(r'^[a-z]+$', text)


def filter_min_score(results, min_score):
  return list(filter(lambda x: x['score'] > min_score, results))


def filter_n_results(results, n):
  return results[0:n]


def sense_matches_result(input_sense):

  def h(r):
    return input_sense == get_generic_sense(extract_sense_from_result(r))

  return h


def extract_sense_from_s2v_tuple(d):
  return d.split('|')[1]


def extract_sense_from_result(d):
  print('check', d, d.get('value').split('|')[1])
  return d.get('value').split('|')[1]


def uniq(l):
  return list(set(l))


def filter_match_input_sense(results, d):
  if isinstance(d, str):
    term, sense = d.split('|')
    generic_sense = get_generic_sense(sense)
    if generic_sense == 'unknown':
      return results
    return list(filter(sense_matches_result(generic_sense), results))

  # only if all input term senses map to the same sense
  # filter on this sense, otherwise return all results
  distinct_input_senses = uniq(map(extract_sense_from_s2v_tuple, d))
  if len(distinct_input_senses) == 1:
    generic_sense = get_generic_sense(distinct_input_senses[0])
    if generic_sense == 'unknown':
      return results
    return list(filter(sense_matches_result(generic_sense), results))


def s2v_transform(d, req_args):
  n_results = req_args.get('n') and int(req_args.get('n')) or 10

  results = [{
      'value': v[0],
      'score': float(v[1])
  } for v in s2v.most_similar(d, n=max([n_results * 2, 10]))]

  if req_args.get('match-input-sense'):
    results = filter_match_input_sense(results, d)

  if req_args.get('min-score'):
    results = filter_min_score(results, float(req_args.get('min-score')))

  results = filter_n_results(results, n_results)

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
    result = s2v_transform(parsed, request.args)
  except Exception as e:
    err = str(e)
    if err.find("Can't find key") != -1:
      # if parsed is a string (single key) and it doesnt contain _ (its single word)
      # and is all lowercase a-z try uppercase version
      if isinstance(parsed, str):
        term, sense = parsed.split('|')
        if is_single_word(term) and is_downcase_alpha(term):
          try:
            result = s2v_transform("{0}|{1}".format(term.upper(), sense),
                                   request.args)
          except Exception as e2:
            err2 = str(e2)
            if err2.find("Can't find key") != -1:
              result = []
            else:
              raise
        else:
          result = []
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
