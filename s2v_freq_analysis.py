import os
import sys
import time
import re
import pandas as pd
import json
from sense2vec import Sense2Vec
from itertools import chain
import numpy as np
import statistics
import seaborn as sns
import matplotlib.pyplot as plt


def normalize_distribution(vals=[], min_val=0.0, max_val=1.0, inverse=False):
  vals_range = max_val - min_val
  input_array = np.array(vals)
  new_vals = list(
      np.around(
          (input_array - np.min(input_array)) / np.ptp(input_array),
          decimals=3))

  if inverse:
    return list(map(lambda x: round(vals_range - x - min_val, 3), new_vals))
  return new_vals


# vals = [0, 21, 2288, 52300, 35004]
# print(normalize_distribution(vals))
# print(normalize_distribution(vals, inverse=True))
# exit()

print("loading model from disk..")
s2v = Sense2Vec().from_disk(os.environ['S2V_MODEL_PATH'])
print("model loaded.")

# 2015 model: s2v keys len:  1195261
print("s2v keys len: ", len(s2v))

freq_by_word_count = {}
freq_distribution_by_word_count = {}

# for key in s2v.keys():
#   word_count = len(key.split('_'))
#   if word_count <= 9:
#     # if word_count > 6:
#     #   print('big word', word_count, key, s2v.get_freq(key))
#     if word_count in freq_by_word_count:
#       freq_by_word_count[word_count] += 1
#     else:
#       freq_by_word_count[word_count] = 1

#     if word_count in freq_distribution_by_word_count:
#       freq_distribution_by_word_count[word_count].append(s2v.get_freq(key))
#     else:
#       freq_distribution_by_word_count[word_count] = [s2v.get_freq(key)]

# # 2015 model: freq by word count {"1": 578422, "2": 517471, "3": 77237, "4": 10911, "5": 2028, "7": 245, "8": 178, "6": 461, "9": 151}
# print("freq by word count", json.dumps(freq_by_word_count))

# for word_count in freq_distribution_by_word_count:
#   freq_dist = freq_distribution_by_word_count[word_count]
#   filename = "s2v_word_count_{0}_freq_distribution.csv".format(word_count)
#   if os.path.exists(filename):
#     os.remove(filename)
#   f = open(filename, "a")
#   f.write("\n".join(str(v) for v in freq_dist))
#   f.close()

s2v_freq_dist = {}
for key in s2v.keys():
  word_count = len(key.split('_'))
  if word_count <= 9:
    freq = s2v.get_freq(key)
    if type(freq) is int:
      if freq < 1000:
        s2v_freq_dist[key] = freq
      else:
        s2v_freq_dist[key] = 1000
    # else:
    #   raise ValueError('oh {0} {1}'.format(freq, key))

s2v_freq_dist_normalized_df = []
s2v_freq_dist_vals = list(s2v_freq_dist.values())

sns.set(color_codes=True)
sns.distplot(s2v_freq_dist_vals, kde=False, rug=False)
plt.show()
exit()

s2v_freq_dist_normalized_vals = normalize_distribution(
    s2v_freq_dist_vals, inverse=True)
print(min(s2v_freq_dist.values()), max(s2v_freq_dist.values()))
print('mean', statistics.mean(s2v_freq_dist_vals))
print('stdev', statistics.pstdev(s2v_freq_dist_vals))

for k, v in zip(s2v_freq_dist.keys(), s2v_freq_dist_normalized_vals):
  s2v_freq_dist_normalized_df.append({'k': k, 'v': v})
  if k == 'natural_language_processing|NOUN' or k == 'Picasso|NOUN':
    print(k, v, s2v.get_freq(k))

df = pd.DataFrame(s2v_freq_dist_normalized_df)
df.head()
pickle_df = df.set_index('k').T
pickle_df.head()
pickle_df.to_pickle('data/s2v_freq_dist_normalized.pkl', protocol=2)
