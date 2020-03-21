import random
from itertools import product
from functools import cmp_to_key

class S2vKeyCaseAndSenseVariations:

  def __init__(self, s2v_util, s2v_senses):
    self.s2v_util = s2v_util
    self.s2v_senses = s2v_senses

  def call(self, k, attempt_phrase_join_for_compound_phrases=None, flag_joined_phrase_variations=False, random_sample_matching_sense_unknown_keys=False, phrase_is_proper=None, return_only_top_priority=False):
    self.flag_joined_phrase_variations = flag_joined_phrase_variations
    if phrase_is_proper is None:
      phrase_is_proper = self.s2v_util.phrase_is_proper(list(map(lambda x: self.s2v_util.s2v.split_key(x['wordsense'])[0], k)))
    combinations = []
    k_len = len(k)
    if k_len >= 2 and attempt_phrase_join_for_compound_phrases:
      combinations += self.collect_compound_phrase_joined_combinations(k)
    if k_len > 2  and attempt_phrase_join_for_compound_phrases:
      combinations += self.collect_last_compound_joined_combinations(k)  
    combinations += self.collect_combinations_based_on_each_keys_combinations(k)
    if random_sample_matching_sense_unknown_keys and len(combinations) <= 0:
      combinations = self.collect_combinations_based_on_each_keys_combinations(
        k,
        random_sample_matching_sense_unknown_keys = True,
      )
    # print('check for key!', k)
    # print('combinations', combinations)
    combinations.sort(key=cmp_to_key(self.sort_by_joined_then_case_match_to_key(k, phrase_is_proper)))
    combinations = self.assign_priority_scores(combinations, phrase_is_proper, return_only_top_priority)
    return combinations


  def collect_combinations_based_on_each_keys_combinations(self, k, random_sample_matching_sense_unknown_keys=False):
    return self.collect_key_sense_combinations(k, random_sample_matching_sense_unknown_keys)


  def collect_last_compound_joined_combinations(self, k):
    last_compound_pair_joined_key = ' '.join(map(lambda x: self.s2v_util.s2v.split_key(x['wordsense'])[0], k[-2:]))
    if len(self.s2v_senses.get_noun_based_senses(last_compound_pair_joined_key)) <= 0:
      return []
    new_k = k[:-2] + [{ 'wordsense': self.s2v_util.s2v.make_key(last_compound_pair_joined_key, 'NOUN'), 'required': True, 'is_joined': True }]
    return self.collect_key_sense_combinations(new_k)


  def collect_key_sense_combinations(self, k, random_sample_matching_sense_unknown_keys=False):
    result = []
    inner_result = []
    len_k = len(k)
    for sub_k in k:
      sub_k_result = []
      word, sense = self.s2v_util.s2v.split_key(sub_k['wordsense'])
      sense_based_senses = self.s2v_senses.get_adjective_based_senses(word) if sense in self.s2v_util.s2v_adj_tags else self.s2v_senses.get_noun_based_senses(word)
      if random_sample_matching_sense_unknown_keys and len(sense_based_senses) <= 0:
        sense_based_senses = [self.random_sample_matching_sense(sense)]
      for s in sense_based_senses:
        if len_k > 1:
          v = { 'wordsense': s, 'required': sub_k['required'] }
          if self.flag_joined_phrase_variations:
            v['is_joined'] = sub_k['is_joined'] if 'is_joined' in sub_k else False
          sub_k_result.append(v)
        else:
          v = { 'wordsense': s, 'required': sub_k['required'] }
          if self.flag_joined_phrase_variations:
            v['is_joined'] = sub_k['is_joined'] if 'is_joined' in sub_k else False
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


  def sort_by_joined_then_case_match_to_key(self, k, phrase_is_proper):
    k_len = len(k)
    k_words = self.s2v_util.words_only(k)
    def the_actual_sort(a, b):
      a_len = len(a)
      b_len = len(b)
      if b_len > 0 and not a_len > 0:
        return 1
      elif a_len > 0 and not b_len > 0:
        return -1


      if b_len == 1 and b[0]['is_joined'] and not a[0]['is_joined']:
        return 1
      elif a_len == 1 and a[0]['is_joined'] and not b[0]['is_joined']:
        return -1
      else:
        a_is_joined_len = len(list(filter(lambda x: 'is_joined' in x and x['is_joined'], a)))
        b_is_joined_len = len(list(filter(lambda x: 'is_joined' in x and x['is_joined'], b)))
        if b_is_joined_len > 0 and b_is_joined_len > a_is_joined_len:
          return 1
        elif a_is_joined_len > 0 and a_is_joined_len > b_is_joined_len:
          return -1

      a_words = self.s2v_util.words_only(a)
      b_words = self.s2v_util.words_only(b)
      a_sense = self.s2v_util.s2v.split_key(a[0]['wordsense'])[1]
      b_sense = self.s2v_util.s2v.split_key(b[0]['wordsense'])[1]

      if not phrase_is_proper and a_len == b_len == 1:
        # take as priority: 
        # 1. the NOUN groups that are not title cased and not all upper case
        # 2. if not enough synonyms in 1, then take the remaining NOUN groups
        # 3. then remaining other sense noun based groups taking the top scoring from those groups
        if b_sense == 'NOUN' and a_sense != 'NOUN':
          return 1
        elif a_sense == 'NOUN' and b_sense != 'NOUN':
          return -1
        else:
          a_upper_or_title_cased = self.phrase_has_title_cased(a_words) or self.phrase_has_upper_cased(a_words)
          b_upper_or_title_cased = self.phrase_has_title_cased(b_words) or self.phrase_has_upper_cased(b_words)
          if not b_upper_or_title_cased and a_upper_or_title_cased:
            return 1
          elif not a_upper_or_title_cased and b_upper_or_title_cased:
            return -1

      if a_words == b_words:
        return 0

      # k_words is the source (list of words)
      # words is what will be scored for matching (list of words) 
      # 
      # score highest in order:
      # all words match exactly
      if b_words == k_words:
        return 1
      elif a_words == k_words:
        return -1

      k_words_joined = '_'.join(k_words)
      k_words_joined_lower = k_words_joined.lower()
      a_words_joined = '_'.join(a_words)
      a_words_joined_lower = a_words_joined.lower()
      b_words_joined = '_'.join(b_words)
      b_words_joined_lower = b_words_joined.lower()

      # if one matches case insensitive and the other doesnt then return the case insenstive match
      if k_words_joined_lower == b_words_joined_lower and k_words_joined_lower != a_words_joined_lower:
        return 1
      elif k_words_joined_lower == a_words_joined_lower and k_words_joined_lower != b_words_joined_lower:
        return -1

      # match case of each word - from first word the more that match case the better,
      # title case (if first letter of first word is upper), 
      # lower case, 
      # remaining
      if k_words[0][0].isupper():
        a_words_joined_title = ' '.join(a_words).title().replace(' ', '_')
        b_words_joined_title = ' '.join(b_words).title().replace(' ', '_')
        if b_words_joined_title == k_words_joined and a_words_joined_title != k_words_joined:
          return 1
        elif a_words_joined_title == k_words_joined and b_words_joined_title != k_words_joined:
          return -1

      if a_len < k_len and b_len >= k_len:
        return 1
      elif b_len < k_len and a_len >= k_len:
        return -1

      # return the best match letter for letter
      for k_letter, a_letter, b_letter in zip(list(k_words_joined), list(a_words_joined), list(b_words_joined)):
        if b_letter == k_letter and a_letter != k_letter:
          return 1
        elif a_letter == k_letter and b_letter != k_letter:
          return -1

      return 0
    
    return the_actual_sort


  def assign_priority_scores(self, combinations, phrase_is_proper, return_only_top_priority):
    initial_score = 1
    current_score = initial_score
    new_combinations = []
    last_combination = None
    for i, c in enumerate(combinations):
      if i > 0:
        if len(last_combination['key']) == 1 and 'is_joined' in last_combination['key'][0] and \
            last_combination['key'][0]['is_joined'] and \
            (len(last_combination['key']) > 1 or 'is_joined' not in c[0] or c[0]['is_joined'] != last_combination['key'][0]['is_joined']):
          current_score += 1
        else:
          c_is_joined_len = len(list(filter(lambda x: 'is_joined' in x and x['is_joined'], c)))
          prev_is_joined_len = len(list(filter(lambda x: 'is_joined' in x and x['is_joined'], last_combination['key'])))
          if c_is_joined_len != prev_is_joined_len:
            current_score += 1
          else:
            words = self.s2v_util.words_only(c)
            prev_words = self.s2v_util.words_only(last_combination['key'])
            if words != prev_words:
              current_score += 1
            elif not phrase_is_proper and len(last_combination['key']) == len(c) == 1:
              current_sense = self.s2v_util.s2v.split_key(c[0]['wordsense'])[1]
              prev_sense = self.s2v_util.s2v.split_key(last_combination['key'][0]['wordsense'])[1]
              if (current_sense == 'NOUN' and prev_sense != 'NOUN') or (current_sense != 'NOUN' and prev_sense == 'NOUN'):
                current_score += 1
      
      if return_only_top_priority and current_score > initial_score:
        break

      new_combination = { 'key': c, 'priority': current_score }
      new_combinations.append(new_combination)
      last_combination = new_combination

    return new_combinations


  def phrase_has_title_cased(self, words):
    return not next((w for w in words if w[0].isupper()), None) is None


  def phrase_has_upper_cased(self, words):
    return not next((w for w in words if w.isupper()), None) is None
