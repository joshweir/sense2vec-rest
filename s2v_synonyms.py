import re

class S2vSynonyms:

  def __init__(self, s2v_util):
    self.s2v_util = s2v_util


  def call(self, d, req_args):
    d_list = [d] if isinstance(d, str) else d
    return self.most_similar_reduced(d_list, req_args)


  def most_similar_reduced(self, d, req_args):
    n_results = req_args.get('n') and int(req_args.get('n')) or 10

    d_with_case_variations = list(filter(self.s2v_util.case_variant_if_not_in_s2v, d))
    if None in d_with_case_variations:
      return []

    results = [{
        'value': v[0],
        'score': float(v[1])
    } for v in self.s2v_util.s2v.most_similar(
        d_with_case_variations, n=max([n_results * 2, 10]))]

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

    results = self.filter_n_results(results, n_results)

    return results

  
  def filter_reduce_compound_nouns(self, data, d):
    result = []
    input_list = list(map(self.s2v_util.s2v.split_key, [d] if isinstance(d, str) else d))
    if len(input_list) > 1 or not self.s2v_util.is_single_word(input_list[0][0]):
      return data

    input_value = input_list[0][0]
    for item in data:
      value = item.get('value')
      value_word, value_sense = self.s2v_util.s2v.split_key(value)

      compound_prefix_pattern = r"._" + re.escape(input_value) + r"$"
      compound_suffix_pattern = r"^" + re.escape(input_value) + r"_."
      if not re.search(compound_prefix_pattern,
                      value_word, re.IGNORECASE) and not re.search(
                          compound_suffix_pattern, value_word, re.IGNORECASE):
        result.append(item)
    return result


  def filter_reduce_multicase(self, data, d):
    seen, result = set(), []
    input_lower = [d.lower()] if isinstance(d, str) else list(
        map(lambda x: x.lower(), d))
    for item in data:
      value_lower = item.get('value').lower()
      if value_lower not in seen and value_lower not in input_lower:
        seen.add(value_lower)
        result.append(item)
    return result


  def filter_match_input_sense(self, results, d):
    if isinstance(d, str):
      term, sense = self.s2v_util.s2v.split_key(d)
      generic_sense = self.s2v_util.get_generic_sense(sense)
      if generic_sense == 'unknown':
        return results
      return list(filter(sense_matches_result(generic_sense), results))

    # only if all input term senses map to the same sense
    # filter on this sense, otherwise return all results
    distinct_input_senses = self.s2v_util.uniq(map(extract_sense_from_s2v_tuple, d))
    if len(distinct_input_senses) > 1:
      return results

    generic_sense = self.s2v_util.get_generic_sense(distinct_input_senses[0])
    if generic_sense == 'unknown':
      return results

    return list(filter(sense_matches_result(generic_sense), results))


  def filter_min_score(self, results, min_score):
    return list(filter(lambda x: x['score'] > min_score, results))


  def filter_min_word_len(self, results, min_word_len):
    return list(filter(lambda x: len(x['value']) >= min_word_len, results))


  def filter_n_results(self, results, n):
    return results[0:n]


  def sense_matches_result(self, input_sense):
    def h(r):
      return input_sense == self.s2v_util.get_generic_sense(extract_sense_from_result(r))

    return h


  def extract_sense_from_s2v_tuple(self, d):
    return self.s2v_util.s2v.split_key(d)[1]


  def extract_sense_from_result(self, d):
    return self.s2v_util.s2v.split_key(d.get('value'))[1]


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