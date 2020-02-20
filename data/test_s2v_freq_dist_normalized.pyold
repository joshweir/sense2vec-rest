import os
from sense2vec import Sense2Vec
import pandas as pd

print("loading model from disk..")
s2v = Sense2Vec().from_disk(os.environ['S2V_MODEL_PATH'])
print("model loaded.")

print("loading pickle file..")
picklefile = os.path.dirname(
    os.path.abspath(__file__)) + '/s2v_freq_dist_normalized.pkl.gz'
cached_freq_dist = pd.read_pickle(picklefile)
print("pickle file loaded.")

k = 'natural_language_processing|NOUN'
print(k)
print(cached_freq_dist[k]['v'])
print(s2v.get_freq(k))

k = 'Picasso|NOUN'
print(k)
print(cached_freq_dist[k]['v'])
print(s2v.get_freq(k))
