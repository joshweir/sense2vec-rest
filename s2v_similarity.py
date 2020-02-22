import random
import os

class S2vSimilarity:

  def __init__(self, s2v_util):
    self.s2v_util = s2v_util


  def call(self, k1, k2, req_args={}):
    self.req_args = req_args
    try:
      k1_common_input = self.s2v_similarity_key_norm(k1)
      k2_common_input = self.s2v_similarity_key_norm(k2)

      result = self.s2v_similarity_wrapper(k1_common_input, k2_common_input)
    except Exception as e:
      err = str(e)
      if err.find("unsupported operand type") != -1:
        result = float(0)
      else:
        raise

    return result


  def s2v_similarity_key_norm(self, k):
    result = list(map(self.s2v_similarity_item_norm, k))
    if len(result) == 1:
      result[0]['required'] = True
    return result


  def s2v_similarity_item_norm(self, d):
    if isinstance(d, str):
      return { 
        'wordsense': d,
        'required': False,
      }
    
    return d


  def s2v_similarity_wrapper(self, k1, k2):
    similarity_combinations = self.collect_similarity_combinations(k1, k2)
    return self.s2v_similarity_select_best(similarity_combinations)


  def collect_similarity_combinations(self, k1, k2):
    combinations = []
    k1_combinations = self.collect_combinations_for_key(k1)
    k2_combinations = self.collect_combinations_for_key(k2)
    for k1_combination in k1_combinations:
      for k2_combination in k2_combinations:
        combinations.append([k1_combination, k2_combination])
    return combinations


  def collect_combinations_for_key(self, k):
    combinations = []
    combinations.append(k)
    k_len = len(k)
    if k_len == 1:
      combinations += self.collect_ner_location_combinations(k)
    elif self.req_args.get('attempt-phrase-join-for-compound-phrases') and (k_len == 2 or (k_len >= 2 and self.all_key_words_are_required(k))):
      combinations += self.collect_compound_phrase_joined_combinations(k)
    return combinations


  def collect_ner_location_combinations(self, k):
    result = []
    word, sense = self.s2v_util.s2v.split_key(k[0]['wordsense'])
    if sense in self.s2v_util.s2v_ner_tags:
      # LOC and GPE seem to be interchangeable for LOCATION NER, ensure both senses are checked for similarity
      if sense == 'LOC':
        result.append([{ 'wordsense': self.s2v_util.join_word_and_sense(word, 'GPE'), 'required': k[0]['required'] }])
      if sense == 'GPE':
        result.append([{ 'wordsense': self.s2v_util.join_word_and_sense(word, 'LOC'), 'required': k[0]['required'] }])
      # also fall back to NOUN sense
      result.append([{ 'wordsense': self.s2v_util.join_word_and_sense(word, 'NOUN'), 'required': k[0]['required'] }])
    return result


  def collect_compound_phrase_joined_combinations(self, k):
    result = []
    joined_key = '_'.join(map(lambda x: self.s2v_util.s2v.split_key(x['wordsense'])[0], k))
    result.append([{ 'wordsense': "{0}|NOUN".format(joined_key), 'required': True }])
    return result


  def all_key_words_are_required(self, k):
    for part in k:
      if not part['required']:
        return False
    return True


  def s2v_similarity_select_best(self, similarity_combinations):
    result = 0.0
    for k1, k2 in similarity_combinations:
      k1_mapped = list(
          map(self.case_variant_if_not_in_s2v_or_random_sample_matching_sense,
              k1))
      k2_mapped = list(
          map(self.case_variant_if_not_in_s2v_or_random_sample_matching_sense,
              k2))

      if None in k1_mapped or None in k2_mapped:
        r = 0.0
      else:
        if os.getenv('S2V_VERBOSE'):
          print()
          print('similarity comparing')
          print('k1', k1_mapped)
          print('k2', k2_mapped)
        r = self.s2v_util.s2v.similarity(k1_mapped, k2_mapped)
        if os.getenv('S2V_VERBOSE'):
          print('result', r)
          print()
      if r > result:
        result = r
    return round(float(result), 3)


  def case_variant_if_not_in_s2v_or_random_sample_matching_sense(self, d):
    found_in_s2v = self.s2v_util.case_variant_if_not_in_s2v(d['wordsense'])
    if found_in_s2v:
      return found_in_s2v

    return None if d['required'] == True else self.random_sample_matching_sense(
        self.s2v_util.s2v.split_key(d['wordsense'])[1])


  def random_sample_matching_sense(self, matching_sense):
    matching_sample = None
    while True:
      samples = random.sample(self.s2v_util.s2v_all_keys, 50)
      for sample in samples:
        if sample[-2:] != '|X':
          word, sense = self.s2v_util.s2v.split_key(sample)
          if sense == matching_sense:
            matching_sample = sample
            break

      if matching_sample:
        return matching_sample


if __name__ == '__main__':
  from sense2vec import Sense2Vec
  from s2v_util import S2vUtil
  print("loading model from disk..")
  s2v = Sense2Vec().from_disk("/Users/josh/Downloads/s2v_old")
  print("model loaded.")
  s2v_util = S2vUtil(s2v)
  similarity_service = S2vSimilarity(s2v_util)
  k1 = ["New_York|LOC"]
  k2 = ["big|ADJ", "apple|NOUN"]
  result = similarity_service.call(k1, k2)
  print(result)
  print()
  k1 = ["New_York|LOC"]
  k2 = ["big|NOUN", "apple|NOUN"]
  result = similarity_service.call(k1, k2)
  print(result)
  print()
  k1 = ["New_York|LOC"]
  k2 = ["big|ADJ", "apple|NOUN"]
  result = similarity_service.call(k1, k2, { 'attempt-phrase-join-for-compound-phrases': 1 })
  print(result)
  print()
  k1 = ["New_York|LOC"]
  k2 = ["big_apple|NOUN"]
  result = similarity_service.call(k1, k2)
  print(result)
  print()
  k1 = ["New_York|LOC"]
  k2 = ["love|ADJ", "big|ADJ", "apple|NOUN"]
  result = similarity_service.call(k1, k2, { 'attempt-phrase-join-for-compound-phrases': 1 })
  print(result)
  print()
  k1 = ["New_York|LOC"]
  k2 = [{ 'wordsense': "love|ADJ", 'required': True }, { 'wordsense': "big|ADJ", 'required': True }, { 'wordsense': "apple|NOUN", 'required': True }]
  result = similarity_service.call(k1, k2, { 'attempt-phrase-join-for-compound-phrases': 1 })
  print(result)
  print()
