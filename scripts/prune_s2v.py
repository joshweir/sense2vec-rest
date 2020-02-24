#!/usr/bin/env python

# example run for s2v old model and 2019:
# (ensure that the sense2vec branch: `feature/prune-vocab` is checkout out and pip install .)
# or ensure its merged to master and that release is installed

# cd
# cd sense2vec-rest
# python scripts/prune_s2v.py /Users/josh/Downloads/s2v_old/ /Users/josh/Downloads/s2v_old_pruned/ -r 0.01 -s 0.7
# python scripts/prune_s2v.py /Users/josh/Downloads/s2v_reddit_2019_lg/ /Users/josh/Downloads/s2v_reddit_2019_lg_pruned/ -r 0.01 -s 0.7


from collections import OrderedDict, defaultdict
import re
import plac
from wasabi import msg
from pathlib import Path
from sense2vec import Sense2Vec
from sense2vec.util import split_key, cosine_similarity


sense_whitelist = ["SYM", "MONEY", "PERCENT", "PRODUCT", "LANGUAGE", "LOC", "CARDINAL", "LAW", "ORG", "EVENT", "PERSON", "ADJ", "NOUN", "NORP", "WORK_OF_ART", "ADV", "FAC", "GPE", "PROPN"]


def get_blacklisted_sense_keys(freqs):
  """Remove keys with sense that is blacklisted"""
  discarded = []
  for key, freq in freqs.items():
    try:
      term, sense = split_key(key)
    except ValueError:
      continue
    if sense and sense not in sense_whitelist:
      discarded.append(key)
  return discarded


def get_markdown_and_url_keys(freqs):
  """Remove keys that are markdown syntax or full urls"""
  discarded = []
  for key, freq in freqs.items():
    try:
      term, sense = split_key(key)
    except ValueError:
      continue

    # remove keys that contain: `http://` or `https://` or `](` or (
    #   (`.php` or `.html` or `.asp`) and also contain `?` or `/`
    # )
    if term:
      if re.search(r'(\]\()|(http:\/\/)|(https:\/\/)', term) or (re.search(r'(\.php)|(\.html)|(\.asp)', term) and re.search(r'[\?\/]', term)):
        discarded.append(key)
        
  return discarded


def get_minority_keys(freqs, min_ratio):
    """Remove keys that are too infrequent relative to a main sense."""
    by_word = defaultdict(list)
    for key, freq in freqs.items():
        try:
            term, sense = split_key(key)
        except ValueError:
            continue
        if freq:
            by_word[term.lower()].append((freq, key))
    discarded = []
    for values in by_word.values():
        if len(values) >= 2:
            values.sort(reverse=True)
            freq1, key1 = values[0]
            for freq2, key2 in values[1:]:
                ratio = freq2 / freq1
                if ratio < min_ratio:
                    discarded.append(key2)
    return discarded


def get_redundant_keys(vocab, vectors, min_distance):
    if min_distance <= 0.0:
        return []
    by_word = defaultdict(list)
    for key, freq in vocab.items():
        try:
            term, sense = split_key(key)
        except ValueError:
            continue
        term = term.split("_")[-1]
        by_word[term.lower()].append((freq, key))
    too_similar = []
    for values in by_word.values():
        if len(values) >= 2:
            values.sort(reverse=True)
            freq1, key1 = values[0]
            vector1 = vectors[key1]
            for freq2, key2 in values[1:]:
                vector2 = vectors[key2]
                sim = cosine_similarity(vector1, vector2)
                if sim >= (1 - min_distance):
                    too_similar.append(key2)
    return too_similar


@plac.annotations(
    model_path=("Path to sense2vec model directory", "positional", None, str),
    out_dir=("Path to save the pruned sense2vec model", "positional", None, str),
    min_freq_ratio=(
        "Frequency ratio threshold for discarding minority senses or casings.",
        "option",
        "r",
        float,
    ),
    min_distance=(
        "Similarity threshold for discarding redundant keys.",
        "option",
        "s",
        float,
    ),
)
def main(
  model_path,
  out_dir,
  min_freq_ratio=0.0,
  min_distance=0.0,
):
  s2v = Sense2Vec().from_disk(model_path)
  output_path = Path(out_dir)
  vocab = {}
  for key, score in s2v.frequencies:
    vocab[key] = score
  vectors = {}
  for key, val in s2v:
    vectors[key] = val
  msg.info("loading vectors")
  for key, val in s2v:
    vector_size = len(val)
    break
  all_senses = s2v.senses
  msg.info("loaded vectors")

  discarded = set()
  discarded.update(get_blacklisted_sense_keys(vocab))
  discarded.update(get_markdown_and_url_keys(vocab))
  discarded.update(get_minority_keys(vocab, min_freq_ratio))
  discarded.update(get_redundant_keys(vocab, vectors, min_distance))
  n_vectors = len(vectors) - len(discarded)
  s2v = Sense2Vec(shape=(n_vectors, vector_size), senses=all_senses)
  for key, vector in vectors.items():
    if key not in discarded:
      s2v.add(key, vector)
      if key in vocab:
        s2v.set_freq(key, vocab[key])
  msg.good("Created the sense2vec model")
  msg.info(f"{n_vectors} vectors, {len(all_senses)} total senses")
  s2v.to_disk(output_path)
  msg.good("Saved model to directory", out_dir)

if __name__ == "__main__":
  try:
    plac.call(main)
  except KeyboardInterrupt:
    msg.warn("Cancelled.")
