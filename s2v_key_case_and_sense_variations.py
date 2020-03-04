import random
from itertools import product


class S2vKeyCaseAndSenseVariations:

  def __init__(self, s2v_util, s2v_senses):
    self.s2v_util = s2v_util
    self.s2v_senses = s2v_senses

  def call(self, k, attempt_phrase_join_for_compound_phrases=None, flag_joined_phrase_variations=False, random_sample_matching_sense_unkown_keys=False):
    self.flag_joined_phrase_variations = flag_joined_phrase_variations
    combinations = []
    k_len = len(k)
    combinations += self.collect_combinations_based_on_each_keys_combinations(k)
    if k_len >= 2 and attempt_phrase_join_for_compound_phrases:
      combinations += self.collect_compound_phrase_joined_combinations(k)
    if random_sample_matching_sense_unkown_keys and len(combinations) <= 0:
      combinations = self.collect_combinations_based_on_each_keys_combinations(
        k,
        random_sample_matching_sense_unkown_keys = True,
      )
    return combinations


  def collect_combinations_based_on_each_keys_combinations(self, k, random_sample_matching_sense_unkown_keys=False):
    result = []
    inner_result = []
    len_k = len(k)
    for sub_k in k:
      sub_k_result = []
      word, sense = self.s2v_util.s2v.split_key(sub_k['wordsense'])
      sense_based_senses = self.s2v_senses.get_adjective_based_senses(word) if sense in self.s2v_util.s2v_adj_tags else self.s2v_senses.get_noun_based_senses(word)
      if random_sample_matching_sense_unkown_keys and len(sense_based_senses) <= 0:
        sense_based_senses = [self.random_sample_matching_sense(sense)]
      for s in sense_based_senses:
        if len_k > 1:
          v = { 'wordsense': s, 'required': sub_k['required'] }
          if self.flag_joined_phrase_variations:
            v['is_joined'] = False
          sub_k_result.append(v)
        else:
          v = { 'wordsense': s, 'required': sub_k['required'] }
          if self.flag_joined_phrase_variations:
            v['is_joined'] = False
          result.append([v])
      if len_k > 1:
        inner_result.append(sub_k_result)
    # combine all inner combinations
    if len_k > 1:
      for to_append in list(product(*inner_result)):
        # print('check', to_append)
        result.append(list(to_append))
    return result


  def collect_compound_phrase_joined_combinations(self, k):
    result = []
    joined_key = ' '.join(map(lambda x: self.s2v_util.s2v.split_key(x['wordsense'])[0], k))
    for s in self.s2v_senses.get_noun_based_senses(joined_key):
      v = { 'wordsense': s, 'required': True }
      if self.flag_joined_phrase_variations:
        v['is_joined'] = True
      result.append([v])
    return result


  def random_sample_matching_sense(self, matching_sense):
    matching_sample = None
    while True:
      samples = random.sample(self.s2v_util.s2v_all_keys, min([50, self.s2v_util.s2v_all_keys_len]))
      for sample in samples:
        if sample[-2:] != '|X':
          word, sense = self.s2v_util.s2v.split_key(sample)
          if sense == matching_sense:
            matching_sample = sample
            break

      if matching_sample:
        return matching_sample