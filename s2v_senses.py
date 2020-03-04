
class S2vSenses:

  def __init__(self, s2v_util):
    self.s2v_util = s2v_util
    self.s2v_caseless_dict = self.build_caseless_dict()


  def build_caseless_dict(self):
    result = {}
    print('loading caseless s2v dict..')
    for key in self.s2v_util.s2v.keys():
      word, sense = self.s2v_util.s2v.split_key(key)
      word_lower = word.lower().replace('_', ' ')
      if not word_lower in result:
        result[word_lower] = []
      result[word_lower].append(key)
    return result


  def get_noun_based_senses(self, word, whitelist=None):
    result = []
    word = word.lower()

    if not whitelist:
      whitelist = self.s2v_util.s2v_noun_tags
    
    shortlist = self.s2v_caseless_dict[word] if word in self.s2v_caseless_dict else None
    if not shortlist:
      return result

    noun_keys = []
    propn_keys = []
    for key in shortlist:
      w, sense = self.s2v_util.s2v.split_key(key)
      if sense in whitelist:
        if sense == 'NOUN':
          noun_keys.append(key)
        elif sense == 'PROPN':
          propn_keys.append(key)
        else:
          result.append(key)

    return result + propn_keys + noun_keys


  def get_adjective_based_senses(self, word, whitelist=None):
    result = []
    word = word.lower()
    
    if not whitelist:
      whitelist = self.s2v_util.s2v_adj_tags
    
    shortlist = self.s2v_caseless_dict[word] if word in self.s2v_caseless_dict else None
    if not shortlist:
      return result

    for key in shortlist:
      w, sense = self.s2v_util.s2v.split_key(key)
      if sense in whitelist:
        result.append(key)

    return result