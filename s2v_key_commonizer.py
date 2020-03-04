class S2vKeyCommonizer:

  def call(self, k):
    result = list(map(self.s2v_item_norm, k))
    if len(result) == 1:
      result[0]['required'] = True
    return result


  def s2v_item_norm(self, d):
    if isinstance(d, str):
      return { 
        'wordsense': d,
        'required': False,
      }
    return d
