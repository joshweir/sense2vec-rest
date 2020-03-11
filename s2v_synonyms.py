import re
import os
from functools import cmp_to_key

MAX_CACHED_KEYS=15

class S2vSynonyms:

  # allow_non_cached_keys when set to True will pass the list of keys in the call through to s2v.most_similar 
  # disregarding most_similar cache. s2v most_similar cache is single key based, multiple keys will be ignored 
  # except for the last key in the list. 
  # allow_non_cached_keys when set to False will pass through single key list entries to most_similar, 
  # multiple keys will be first joined and asserted as existing before passing to most_similar
  # 
  # allow_non_cached_keys defaults to False and will currently throw exception if set to True because:
  # * s2v 1.0.2 most_similar will use cache when available, but will always use the cache and if multiple keys 
  #   are sent to most_similar it will just use the last key to collect most_similar entries
  # * even if i fix this above (by first checking if the key is in cache and process accordingly (in s2v.most_similar)), 
  #   the most_similar cosine similarity is very slow, would need to run on a gpu

  def __init__(self, s2v_util, s2v_key_variations, s2v_key_commonizer, allow_non_cached_keys=False):
    self.s2v_util = s2v_util
    self.s2v_key_variations = s2v_key_variations
    self.s2v_key_commonizer = s2v_key_commonizer
    self.allow_non_cached_keys = allow_non_cached_keys
    if self.allow_non_cached_keys:
      raise ValueError('allow_non_cached_keys cannot currently be truthy, see comment in S2vSynonyms class for more info')


  def call(self, d, req_args={}):
    return self.most_similar_wrapper(
      self.commonize_input(d), 
      req_args,
    )


  def commonize_input(self, d):
    d_list = None
    if isinstance(d, str):
      d_list = [d]
    elif isinstance(d, list):
      d_list = d
    elif isinstance(d, dict):
      d_list = [d['phrase']] if isinstance(d['phrase'], str) else d['phrase']
    else:
      raise ValueError("dont recognize type of input: {0} {1}".format(type(d), d))
    d_common_input = self.s2v_key_commonizer.call(d_list)
    is_proper = d['is_proper'] if 'is_proper' in d else self.s2v_util.phrase_is_proper(list(map(lambda x: self.s2v_util.s2v.split_key(x['wordsense'])[0], d_common_input)))
    return { 'phrase': d_common_input, 'is_proper': is_proper }


  def most_similar_wrapper(self, d, req_args):
    result = []
    k_len = len(d['phrase'])
    d_keys = list(map(lambda x: x['wordsense'], d['phrase']))
    n_results = req_args.get('n') and int(req_args.get('n')) or 10
    attempt_phrase_join_for_compound_phrases = req_args.get('attempt-phrase-join-for-compound-phrases')
    d_variations = self.s2v_key_variations.call(
      d['phrase'], 
      attempt_phrase_join_for_compound_phrases,
      flag_joined_phrase_variations = True,
      phrase_is_proper = d['is_proper'],
    )

    current_priority = 1
    current_priority_group = []
    for d_variation in d_variations:
      priority = d_variation['priority']
      if priority != current_priority:
        result, reached_limit = self.merge_current_priority_group_with_result(
          current_priority_group,
          result,
          n_results,
          req_args,
          d_keys,
        )
        current_priority_group = []
        if reached_limit:
          break
        current_priority = priority

      is_phrase_joined = d_variation['key'][0]['is_joined']
      d_variation_keys = list(map(lambda x: x['wordsense'], d_variation['key']))
      d_variation_keys_words = self.s2v_util.words_only(d_variation['key'])

      if os.getenv('S2V_VERBOSE'):
        print()
        print('k', d_variation_keys, ':')
        print()
      if len(d_variation_keys) <= 1 or self.allow_non_cached_keys:
        for r in self.s2v_util.s2v.most_similar(d_variation_keys, n=min([MAX_CACHED_KEYS, max([n_results * 2, 10])])):
          value, score = r
          if os.getenv('S2V_VERBOSE'):
            print(value, score)
          word, sense = self.s2v_util.s2v.split_key(value)
          if self.matches_required_properness(word, d['is_proper']):
            current_priority_group = self.merge_synonym_result_with_list(current_priority_group, word, sense, score)

    result, reached_limit = self.merge_current_priority_group_with_result(
      current_priority_group,
      result,
      n_results,
      req_args,
      d_keys,
    )  
    return result


  def merge_synonym_result_with_list(self, result, word, sense, score):
    new_result = []
    score = round(float(score), 3)
    found = False
    for r in result:
      if r['word'] == word:
        found = True
        if score > r['score']:
          new_result.append({
            'word': word,
            'sense': sense,
            'score': score,
          })
        else:
          new_result.append(r)
      else:
        new_result.append(r)
    if not found:
      new_result.append({
        'word': word,
        'sense': sense,
        'score': score,
      })
    return new_result


  def merge_current_priority_group_with_result(
    self,
    current_priority_group,
    result,
    n_results,
    req_args,
    d_keys,
  ):
    current_priority_group = self.reduce_results_based_on_req_args(current_priority_group, d_keys, req_args)
    current_priority_group.sort(key=cmp_to_key(self.sort_by_score))
    result_len = len(result)
    count_remaining = n_results - result_len
    if count_remaining > 0:
      result += current_priority_group[:count_remaining]
    reached_limit = True if count_remaining <= 0 or len(current_priority_group) >= count_remaining else False
    return (result, reached_limit)


  def sort_by_score(self, a, b):
    if b['score'] > a['score']:
      return 1
    else:
      return -1


  def reduce_results_based_on_req_args(self, results, d, req_args):
    if req_args.get('reduce-multicase'):
      results = self.filter_reduce_multicase(results, d)

    # if req_args.get('reduce-multi-wordform'):
    #   results = self.filter_reduce_multi_wordform(results, d)

    if req_args.get('match-input-sense'):
      results = self.filter_match_input_sense(results, d)

    if req_args.get('reduce-compound-nouns'):
      results = self.filter_reduce_compound_nouns(results, d)

    if req_args.get('min-word-len'):
      results = self.filter_min_word_len(results, int(req_args.get('min-word-len')))

    if req_args.get('min-score'):
      results = self.filter_min_score(results, float(req_args.get('min-score')))

    return results


  # remove synonyms that match input sense first word or last word 
  # like input: foo then remove synonyms like: foo_bar or baz_foo
  def filter_reduce_compound_nouns(self, data, d):
    result = []
    
    input_list = list(map(self.s2v_util.s2v.split_key, [d] if isinstance(d, str) else d))
    if len(input_list) > 1 or not self.s2v_util.is_single_word(input_list[0][0]):
      return data

    input_value = input_list[0][0]
    for item in data:
      value_word = item.get('word')
      value_sense = item.get('sense')
      compound_prefix_pattern = r"._" + re.escape(input_value) + r"$"
      compound_suffix_pattern = r"^" + re.escape(input_value) + r"_."
      if not re.search(
        compound_prefix_pattern,
        value_word,
        re.IGNORECASE,
      ) and not re.search(
        compound_suffix_pattern,
        value_word,
        re.IGNORECASE,
      ):
        result.append(item)
    return result


  def filter_reduce_multicase(self, data, d):
    seen, result = set(), []
    input_lower = [d.lower()] if isinstance(d, str) else list(map(lambda x: x.lower(), d))
    for item in data:
      value_lower = item.get('word').lower()
      if value_lower not in seen and value_lower not in input_lower:
        seen.add(value_lower)
        result.append(item)
    return result


  def filter_match_input_sense(self, results, d):
    input_list = [d] if isinstance(d, str) else d
    if len(input_list) == 1:
      term, sense = self.s2v_util.s2v.split_key(input_list[0])
      generic_sense = self.s2v_util.get_generic_sense(sense)
      if generic_sense == 'unknown':
        return results
      return list(filter(self.sense_matches_result(generic_sense), results))

    # only if all input term senses map to the same sense
    # filter on this sense, otherwise return all results
    distinct_input_senses = self.s2v_util.uniq(map(self.extract_sense_from_s2v_tuple, d))
    if len(distinct_input_senses) > 1:
      return results

    generic_sense = self.s2v_util.get_generic_sense(distinct_input_senses[0])
    if generic_sense == 'unknown':
      return results

    return list(filter(self.sense_matches_result(generic_sense), results))


  def filter_min_score(self, results, min_score):
    return list(filter(lambda x: x['score'] >= min_score, results))


  def filter_min_word_len(self, results, min_word_len):
    return list(filter(lambda x: len(x['word']) >= min_word_len, results))


  def sense_matches_result(self, input_sense):
    def h(r):
      return input_sense == self.s2v_util.get_generic_sense(self.extract_sense_from_result(r))
    return h


  def extract_sense_from_s2v_tuple(self, d):
    return self.s2v_util.s2v.split_key(d)[1]


  def extract_sense_from_result(self, d):
    return d.get('sense')


  def matches_required_properness(self, phrase, is_proper):
    if is_proper is None:
      return True
    phrase_properness = self.s2v_util.phrase_is_proper([phrase])
    return phrase_properness == is_proper

  # def filter_reduce_multi_wordform(self, data, d):
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

if __name__ == '__main__':
  from sense2vec import Sense2Vec
  from s2v_util import S2vUtil
  from s2v_senses import S2vSenses
  from s2v_key_case_and_sense_variations import S2vKeyCaseAndSenseVariations
  from s2v_key_commonizer import S2vKeyCommonizer
  print("loading model from disk..", os.getenv('S2V_MODEL_PATH_DEV'))
  s2v = Sense2Vec().from_disk(os.getenv('S2V_MODEL_PATH_DEV'))
  print("model loaded.")
  s2v_util = S2vUtil(s2v)
  s2v_senses = S2vSenses(s2v_util)
  s2v_key_variations = S2vKeyCaseAndSenseVariations(s2v_util, s2v_senses)
  s2v_key_commonizer = S2vKeyCommonizer()
  syn_service = S2vSynonyms(s2v_util, s2v_key_variations, s2v_key_commonizer)
  req_args = { 
    'attempt-phrase-join-for-compound-phrases': 1,
    'min-score': 0.5,
    'n': 10,
    'match-input-sense': 1,
    'reduce-multi-case': 1,
    'reduce-compound-nouns': 1,
    'min-word-len': 2,
  }
  k = ["black|NOUN"]
  result = syn_service.call(k, req_args)
  print(result)
  print()
  k = { 'phrase': ["New_York|LOC"], 'is_proper': True }
  result = syn_service.call(k, req_args)
  print(result)
  print()
  k = ["big|ADJ", "apple|NOUN"]
  result = syn_service.call(k, req_args)
  print('should return no results because input phrase is not proper')
  print(result)
  print() 
