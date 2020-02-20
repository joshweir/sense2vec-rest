import re
# from textblob import Word

class S2vUtil:

  def __init__(self, s2v):
    self.s2v = s2v
    self.s2v_all_keys = list(s2v.keys())
    self.s2v_ner_tags = ['NUM', 'PERSON', 'NORP', 'FACILITY', 'ORG', 'GPE', 'LOC',
      'PRODUCT', 'EVENT', 'LANGUAGE', 'WORK_OF_ART']
    self.s2v_noun_tags = ['PROPN', 'NOUN', 'n'] + self.s2v_ner_tags
    self.s2v_adj_tags = ['ADJ', 'a']
    self.s2v_verb_tags = ['VERB', 'v']


  def s2v_key_case_variations(self, d):
    result = []
    result.append(d)
    word, sense = self.s2v.split_key(d)
    result.append(self.join_word_and_sense(word.lower(), sense))
    result.append(d.upper())
    result.append(self.s2v_key_titlecase(d))
    result.append(self.s2v_key_titlecase(d, only_first_word=True))

    return self.uniq(result)


  def case_variant_if_not_in_s2v(self, d):
    if self.in_s2v(d):
      return d

    return next((x for x in self.s2v_key_case_variations(d) if self.in_s2v(x)), None)

  
  def s2v_key_titlecase(self, d, only_first_word=False):
    word, sense = self.s2v.split_key(d)
    if only_first_word:
      s = list(word)
      s[0] = s[0].upper()
      return self.join_word_and_sense("".join(s), sense)

    return self.join_word_and_sense(word.title(), sense)


  def join_word_and_sense(self, word, sense):
    return self.s2v.make_key(word, sense)


  def in_s2v(self, d):
    return d in self.s2v


  def not_in_s2v(self, d):
    return d not in self.s2v


  def uniq(self, l):
    return list(set(l))


  def get_generic_sense(self, sense):
    if sense in self.s2v_adj_tags:
      return 'a'

    if sense in self.s2v_verb_tags:
      return 'v'

    if sense in self.s2v_noun_tags:
      return 'n'

    return 'unknown'


  # def get_lemma(self, word, pos_tag):
  #   tag = get_generic_sense(pos_tag)
  #   if (tag == 'unknown'):
  #     lemma = Word(word).lemmatize()
  #     # print('lemma', lemma, word, pos_tag)
  #     return lemma

  #   lemma = Word(word).lemmatize(tag)
  #   # print('lemma', lemma, word, pos_tag)
  #   return lemma


  def is_single_word(self, text):
    return text.find("_") == -1


  def is_downcase_alpha(self, text):
    return re.search(r'^[a-z]+$', text)