import os
import pandas as pd


class GoogleNgrams:

  def __init__(self, picklefile):
    self.load(filename)

  def load(self, picklefile):
    print("loading ngrams pickle file..")
    self.ngrams_dict = pd.read_pickle(picklefile)
    print("ngrams pickle file loaded.")

  def __getitem__(self, k):
    v = self.ngrams_dict[k.lower()]['v']
    if v:
      return float(v)

    return 1.0