import os


class S2vSimilarity:

  def __init__(self, s2v_util, s2v_key_variations, s2v_key_commonizer):
    self.s2v_util = s2v_util
    self.s2v_key_variations = s2v_key_variations
    self.s2v_key_commonizer = s2v_key_commonizer
    self.req_args = {}


  def call(self, k1, k2, req_args={}):
    self.req_args = req_args
    try:
      k1_common_input = self.s2v_key_commonizer.call(k1)
      k2_common_input = self.s2v_key_commonizer.call(k2)
      result = self.s2v_similarity_wrapper(k1_common_input, k2_common_input)
    except Exception as e:
      err = str(e)
      if err.find("unsupported operand type") != -1:
        result = float(0)
      else:
        raise

    return result


  def s2v_similarity_wrapper(self, k1, k2):
    key_variation_combinations = self.collect_key_variation_combinations(k1, k2)
    return self.s2v_similarity_select_best(key_variation_combinations)


  def collect_key_variation_combinations(self, k1, k2):
    combinations = []
    attempt_phrase_join_for_compound_phrases = self.req_args.get('attempt-phrase-join-for-compound-phrases')
    k1_variations = self.s2v_key_variations.call(
      k1, 
      attempt_phrase_join_for_compound_phrases,
      random_sample_matching_sense_unknown_keys = True,
      flag_joined_phrase_variations = True,
    )
    k2_variations = self.s2v_key_variations.call(
      k2, 
      attempt_phrase_join_for_compound_phrases,
      random_sample_matching_sense_unknown_keys = True,
      flag_joined_phrase_variations = True,
    )
    for k1_variation in k1_variations:
      for k2_variation in k2_variations:
        combinations.append([k1_variation, k2_variation])
    return combinations


  def s2v_similarity_select_best(self, similarity_combinations):
    result = 0.0
    for k1, k2 in similarity_combinations:
      k1_mapped = list(map(
        lambda x: x['wordsense'],
        k1,
      ))
      k2_mapped = list(map(
        lambda x: x['wordsense'],
        k2,
      ))

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


if __name__ == '__main__':
  from sense2vec import Sense2Vec
  from s2v_util import S2vUtil
  print("loading model from disk..")
  s2v = Sense2Vec().from_disk(os.getenv('S2V_MODEL_PATH'))
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
