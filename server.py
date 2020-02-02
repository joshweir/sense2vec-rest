#!/usr/bin/python3

import os
from flask import Flask, request, Response
import json
import datetime
from sense2vec import Sense2Vec
import re
import random
# from textblob import Word
from data.load_google_ngrams_pickle import GoogleNgrams
import statistics

app = Flask(__name__)
port = 80 if os.getuid() == 0 else 8000

print("loading model from disk..")
s2v = Sense2Vec().from_disk("/sense2vec-model")
print("model loaded.")
google_ngrams_picklefile = '/google-ngrams.pkl'
ngrams_lookup = GoogleNgrams(google_ngrams_picklefile)
s2v_all_keys = list(s2v.keys())
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


# def get_lemma(word, pos_tag):
#   tag = get_generic_sense(pos_tag)
#   if (tag == 'unknown'):
#     lemma = Word(word).lemmatize()
#     # print('lemma', lemma, word, pos_tag)
#     return lemma

#   lemma = Word(word).lemmatize(tag)
#   # print('lemma', lemma, word, pos_tag)
#   return lemma


def is_single_word(text):
  return text.find("_") == -1


def is_downcase_alpha(text):
  return re.search(r'^[a-z]+$', text)


def filter_min_score(results, min_score):
  return list(filter(lambda x: x['score'] > min_score, results))


def filter_min_word_len(results, min_word_len):
  return list(filter(lambda x: len(x['value']) >= min_word_len, results))


def filter_n_results(results, n):
  return results[0:n]


def sense_matches_result(input_sense):

  def h(r):
    return input_sense == get_generic_sense(extract_sense_from_result(r))

  return h


def extract_sense_from_s2v_tuple(d):
  return s2v.split_key(d)[1]


def extract_sense_from_result(d):
  return s2v.split_key(d.get('value'))[1]


def uniq(l):
  return list(set(l))


def filter_match_input_sense(results, d):
  if isinstance(d, str):
    term, sense = s2v.split_key(d)
    generic_sense = get_generic_sense(sense)
    if generic_sense == 'unknown':
      return results
    return list(filter(sense_matches_result(generic_sense), results))

  # only if all input term senses map to the same sense
  # filter on this sense, otherwise return all results
  distinct_input_senses = uniq(map(extract_sense_from_s2v_tuple, d))
  if len(distinct_input_senses) > 1:
    return results

  generic_sense = get_generic_sense(distinct_input_senses[0])
  if generic_sense == 'unknown':
    return results

  return list(filter(sense_matches_result(generic_sense), results))


def filter_reduce_multicase(data, d):
  seen, result = set(), []
  input_lower = [d.lower()] if isinstance(d, str) else list(
      map(lambda x: x.lower(), d))
  for item in data:
    value_lower = item.get('value').lower()
    if value_lower not in seen and value_lower not in input_lower:
      seen.add(value_lower)
      result.append(item)
  return result


def join_word_and_sense(word, sense):
  return "{0}|{1}".format(word, sense)


# def filter_reduce_multi_wordform(data, d):
#   seen, result = set(), []
#   input_list = list(
#       map(s2v.split_key, [d] if isinstance(d, str) else d))
#   input_list_reduced_to_lemma = list(
#       map(lambda x: [get_lemma(x[0], x[1]), x[1]], input_list))
#   for item in data:
#     value = item.get('value')
#     value_word, value_sense = s2v.split_key(value)
#     value_word_lemma = get_lemma(value_word, value_sense)
#     value_word_lemma_sense_joined = join_word_and_sense(value_word_lemma, value_sense)

#     if value_word_lemma_sense_joined not in seen and [
#         value_word_lemma, value_sense
#     ] not in input_list_reduced_to_lemma:
#       seen.add(value_word_lemma_sense_joined)
#       result.append(item)
#   return result


def filter_reduce_compound_nouns(data, d):
  result = []
  input_list = list(map(s2v.split_key, [d] if isinstance(d, str) else d))
  if len(input_list) > 1 or not is_single_word(input_list[0][0]):
    return data

  input_value = input_list[0][0]
  for item in data:
    value = item.get('value')
    value_word, value_sense = s2v.split_key(value)

    compound_prefix_pattern = r"._" + re.escape(input_value) + r"$"
    compound_suffix_pattern = r"^" + re.escape(input_value) + r"_."
    if not re.search(compound_prefix_pattern,
                     value_word, re.IGNORECASE) and not re.search(
                         compound_suffix_pattern, value_word, re.IGNORECASE):
      result.append(item)
  return result


def s2v_most_similar_reduced(d, req_args):
  n_results = req_args.get('n') and int(req_args.get('n')) or 10

  d_with_case_variations = list(filter(case_variation_found_in_s2v, d))
  if None in d_with_case_variations:
    return []

  results = [{
      'value': v[0],
      'score': float(v[1])
  } for v in s2v.most_similar(
      d_with_case_variations, n=max([n_results * 2, 10]))]

  if req_args.get('reduce-multicase'):
    results = filter_reduce_multicase(results, d)

  # if req_args.get('reduce-multi-wordform'):
  #   results = filter_reduce_multi_wordform(results, d)

  if req_args.get('match-input-sense'):
    results = filter_match_input_sense(results, d)

  if req_args.get('reduce-compound-nouns'):
    results = filter_reduce_compound_nouns(results, d)

  if req_args.get('min-word-len'):
    results = filter_min_word_len(results, int(req_args.get('min-word-len')))

  if req_args.get('min-score'):
    results = filter_min_score(results, float(req_args.get('min-score')))

  results = filter_n_results(results, n_results)

  return results


def s2v_most_similar_reduced_handle_error_when_no_result(d, req_args):
  d_list = [d] if isinstance(d, str) else d
  return s2v_most_similar_reduced(d_list, req_args)


def in_s2v(d):
  return d in s2v


def not_in_s2v(d):
  return d not in s2v


def random_sample_matching_sense(matching_sense):
  matching_sample = None
  while True:
    samples = random.sample(s2v_all_keys, 50)
    for sample in samples:
      if sample[-2:] != '|X':
        word, sense = s2v.split_key(sample)
        if sense == matching_sense:
          matching_sample = sample
          break

    if matching_sample:
      return matching_sample


def s2v_key_titlecase(d, only_first_word=False):
  word, sense = s2v.split_key(d)
  if only_first_word:
    s = list(word)
    s[0] = s[0].upper()
    return join_word_and_sense("".join(s), sense)

  return join_word_and_sense(word.title(), sense)


def s2v_key_case_variations(d):
  result = []
  result.append(d)
  word, sense = s2v.split_key(d)
  result.append(join_word_and_sense(word.lower(), sense))
  result.append(d.upper())
  result.append(s2v_key_titlecase(d))
  result.append(s2v_key_titlecase(d, only_first_word=True))

  return uniq(result)


def case_variation_found_in_s2v(d):
  if in_s2v(d):
    return d

  return next((x for x in s2v_key_case_variations(d) if in_s2v(x)), None)


def random_sample_matching_sense_if_case_variation_not_found_in_s2v(d):
  found_in_s2v = case_variation_found_in_s2v(d['wordsense'])
  if found_in_s2v:
    return found_in_s2v

  return None if d['required'] == True else random_sample_matching_sense(
      s2v.split_key(d['wordsense'])[1])


def word_sense_ngram_score(d):
  key = ' '.join(list(map(lambda x: s2v.split_key(x['wordsense'])[0], d)))
  return ngrams_lookup[key]


def s2v_similarity_item_norm(d):
  if isinstance(d, str):
    return {'wordsense': d, 'required': False}

  return d


def s2v_similarity_handle_error_when_no_result(k1, k2):
  try:
    k1_common_input = list(map(s2v_similarity_item_norm, k1))
    k2_common_input = list(map(s2v_similarity_item_norm, k2))
    k1_ngram_score = word_sense_ngram_score(k1)
    k2_ngram_score = word_sense_ngram_score(k2)

    if len(k1_common_input) == 1 and not case_variation_found_in_s2v(
        k1_common_input[0]['wordsense']):
      return (float(0), k1_ngram_score, k2_ngram_score)

    if len(k2_common_input) <= 1 and not case_variation_found_in_s2v(
        k2_common_input[0]['wordsense']):
      return (float(0), k1_ngram_score, k2_ngram_score)

    k1_mapped = list(
        map(random_sample_matching_sense_if_case_variation_not_found_in_s2v,
            k1_normalized))
    k2_mapped = list(
        map(random_sample_matching_sense_if_case_variation_not_found_in_s2v,
            k2_normalized))

    if None in k1_mapped or None in k2_mapped:
      return (float(0), k1_ngram_score, k2_ngram_score)

    result = s2v.similarity(k1_mapped, k2_mapped)
  except Exception as e:
    err = str(e)
    if err.find("unsupported operand type") != -1:
      result = (float(0), k1_ngram_score, k2_ngram_score)
    else:
      raise

  return (result, k1_ngram_score, k2_ngram_score)


@app.route('/', methods=['POST', 'GET'])
def index():
  start = datetime.datetime.utcnow()
  data = request.data.decode('utf-8')
  if not data:
    return Response(status=500, response="no data")

  # print("got something: '%s'" % data)
  parsed = json.loads(data)

  results = []
  for item in parsed:
    result = s2v_most_similar_reduced_handle_error_when_no_result(
        item, request.args)
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
    return Response(status=500, response="no data")

  # print("got something: '%s'" % data)
  parsed = json.loads(data)

  results = []
  for item in parsed:
    result = s2v_similarity_handle_error_when_no_result(item[0], item[1])
    results.append(float(result))

  fin = datetime.datetime.utcnow()
  print(fin - start, 'req time')
  # print('result ', result)

  return Response(
      status=200, response=json.dumps(results), content_type="application/json")


if __name__ == '__main__':
  app.run(port=port, host="0.0.0.0")
