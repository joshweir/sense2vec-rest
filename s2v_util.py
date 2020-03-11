import re
# from textblob import Word

PUNCTUATION = r'\`\>\<\■\|\^\~!-#-+=*,-/:;?\\[-\\]_{}\xa1\xa7\xab\xb6\xb7\xbb\xbf\u037e\u0387\u055a-\u055f\u0589\u058a\u05be\u05c0\u05c3\u05c6\u05f3\u05f4\u0609\u060a\u060c\u060d\u061b\u061e\u061f\u066a-\u066d\u06d4\u0700-\u070d\u07f7-\u07f9\u0830-\u083e\u085e\u0964\u0965\u0970\u0af0\u0df4\u0e4f\u0e5a\u0e5b\u0f04-\u0f12\u0f14\u0f3a-\u0f3d\u0f85\u0fd0-\u0fd4\u0fd9\u0fda\u104a-\u104f\u10fb\u1360-\u1368\u1400\u166d\u166e\u169b\u169c\u16eb-\u16ed\u1735\u1736\u17d4-\u17d6\u17d8-\u17da\u1800-\u180a\u1944\u1945\u1a1e\u1a1f\u1aa0-\u1aa6\u1aa8-\u1aad\u1b5a-\u1b60\u1bfc-\u1bff\u1c3b-\u1c3f\u1c7e\u1c7f\u1cc0-\u1cc7\u1cd3\u2010-\u2027\u2030-\u2043\u2045-\u2051\u2053-\u205e\u207d\u207e\u208d\u208e\u2329\u232a\u2768-\u2775\u27c5\u27c6\u27e6-\u27ef\u2983-\u2998\u29d8-\u29db\u29fc\u29fd\u2cf9-\u2cfc\u2cfe\u2cff\u2d70\u2e00-\u2e2e\u2e30-\u2e3b\u3001-\u3003\u3008-\u3011\u3014-\u301f\u3030\u303d\u30a0\u30fb\ua4fe\ua4ff\ua60d-\ua60f\ua673\ua67e\ua6f2-\ua6f7\ua874-\ua877\ua8ce\ua8cf\ua8f8-\ua8fa\ua92e\ua92f\ua95f\ua9c1-\ua9cd\ua9de\ua9df\uaa5c-\uaa5f\uaade\uaadf\uaaf0\uaaf1\uabeb\ufd3e\ufd3f\ufe10-\ufe19\ufe30-\ufe52\ufe54-\ufe61\ufe63\ufe68\ufe6a\ufe6b\uff01-\uff03\uff05-\uff0a\uff0c-\uff0f\uff1a\uff1b\uff1f\uff20\uff3b-\uff3d\uff3f\uff5b\uff5d\uff5f-\uff65'
PUNCTUATION_PATTERN = '[{0}]'.format(PUNCTUATION)

def flatten(items):
  flat_list = []
  for sublist in items:
    if isinstance(sublist, list):
      for item in sublist:
        flat_list.append(item)
    else:
      flat_list.append(sublist)
  return flat_list

def remove_punctuation(word):
  return re.sub(PUNCTUATION_PATTERN, ' ', word)

class S2vUtil:

  def __init__(self, s2v):
    self.s2v = s2v
    self.s2v_all_keys = list(s2v.keys())
    self.s2v_all_keys_len = len(self.s2v_all_keys)
    self.s2v_ner_tags = ['NUM', 'PERSON', 'NORP', 'FACILITY', 'ORG', 'GPE', 'LOC',
      'PRODUCT', 'EVENT', 'LANGUAGE', 'WORK_OF_ART']
    self.s2v_noun_tags = ['PROPN', 'NOUN', 'n'] + self.s2v_ner_tags
    self.s2v_adj_tags = ['ADJ', 'ADV', 'a']
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


  def phrase_is_proper(self, terms):
    words = flatten(map(lambda x: x.split(' '), terms))
    joined_terms = remove_punctuation(' '.join(words))
    return joined_terms != joined_terms.lower()


  def words_only(self, k):
    return flatten(map(lambda x: self.s2v.split_key(x['wordsense'])[0].split(' '), k))