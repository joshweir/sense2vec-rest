import pytest
from s2v_key_case_and_sense_variations import S2vKeyCaseAndSenseVariations

@pytest.fixture
def s2v_mock():
    from sense2vec import Sense2Vec
    import numpy as np
    s2v = Sense2Vec(shape=(14, 4))
    s2v.add('New_York|GPE', np.asarray([1, 1, 1, 1], dtype=np.float32))
    s2v.add('New_York|NOUN', np.asarray([1, 2, 1, 1], dtype=np.float32))
    s2v.add('big|ADJ', np.asarray([2, 5, 4, 2], dtype=np.float32))
    s2v.add('BIG|ADJ', np.asarray([2, 5, 4, 1], dtype=np.float32))
    s2v.add('apple|NOUN', np.asarray([1, 3, 9, 3], dtype=np.float32))
    s2v.add('big_apple|NOUN', np.asarray([6, 6, 6, 6], dtype=np.float32))
    s2v.add('Big_Apple|NOUN', np.asarray([6, 6, 6, 6], dtype=np.float32))
    s2v.add('Big_Apple|LOC', np.asarray([6, 6, 6, 6], dtype=np.float32))
    s2v.add('Big_apple|NOUN', np.asarray([6, 6, 6, 6], dtype=np.float32))
    s2v.add('BIG_apple|NOUN', np.asarray([6, 6, 6, 6], dtype=np.float32))
    s2v.add('BIG_Apple|NOUN', np.asarray([6, 6, 6, 6], dtype=np.float32))
    s2v.add('BIG_APPLE|NOUN', np.asarray([6, 6, 6, 6], dtype=np.float32))
    s2v.add('black|NOUN', np.asarray([6, 6, 6, 6], dtype=np.float32))
    s2v.add('black|ADJ', np.asarray([5, 5, 5, 5], dtype=np.float32))
    return s2v


@pytest.fixture
def the_service(s2v_mock):
    from s2v_util import S2vUtil
    from s2v_senses import S2vSenses
    from s2v_key_case_and_sense_variations import S2vKeyCaseAndSenseVariations
    s2v_util = S2vUtil(s2v_mock)
    s2v_senses = S2vSenses(s2v_util)
    return S2vKeyCaseAndSenseVariations(s2v_util, s2v_senses)


def test_noun_senses_with_matching_key_are_equal_priority_when_phrase_is_proper(the_service, s2v_mock):
    k = [
      { 'wordsense': 'New_York|LOC', 'required': True },
    ]
    result = the_service.call(
      k, 
      attempt_phrase_join_for_compound_phrases = True,
      flag_joined_phrase_variations = True,
      phrase_is_proper = True,
    )
    expected = [
      # LOC and GPE senses are synonymous, LOC does not exist for this key in s2v, therefore GPE is selected
      { 'key': [{ 'wordsense': 'New_York|GPE', 'required': True, 'is_joined': False }], 'priority': 1 },
      { 'key': [{ 'wordsense': 'New_York|NOUN', 'required': True, 'is_joined': False }], 'priority': 1 },
    ]
    assert result == expected


def test_proper_noun_phrase_is_correctly_identified_without_phrase_is_proper_input_flagged(the_service, s2v_mock):
    k = [
      { 'wordsense': 'New_York|LOC', 'required': True },
    ]
    result = the_service.call(
      k, 
      attempt_phrase_join_for_compound_phrases = True,
      flag_joined_phrase_variations = True,
    )
    result_phrase_is_proper_flagged = the_service.call(
      k, 
      attempt_phrase_join_for_compound_phrases = True,
      flag_joined_phrase_variations = True,
      phrase_is_proper = True,
    )
    expected = [
      # LOC and GPE senses are synonymous, LOC does not exist for this key in s2v, therefore GPE is selected
      { 'key': [{ 'wordsense': 'New_York|GPE', 'required': True, 'is_joined': False }], 'priority': 1 },
      { 'key': [{ 'wordsense': 'New_York|NOUN', 'required': True, 'is_joined': False }], 'priority': 1 },
    ]
    assert result == result_phrase_is_proper_flagged == expected


def test_ranks_joined_keys_higher_than_non_joined_then_ranks_better_case_matches_higher_and_non_proper_phrase_correctly_identified(the_service, s2v_mock):
    k = [
      { 'wordsense': 'big|ADJ', 'required': False },
      { 'wordsense': 'apple|NOUN', 'required': False },
    ]
    result = the_service.call(
      k, 
      attempt_phrase_join_for_compound_phrases = True,
      flag_joined_phrase_variations = True,
    )
    result_phrase_is_proper_flagged = the_service.call(
      k, 
      attempt_phrase_join_for_compound_phrases = True,
      flag_joined_phrase_variations = True,
      phrase_is_proper = False,
    )
    expected = [
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'big_apple|NOUN'}], 'priority': 1},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_apple|NOUN'}], 'priority': 2},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_Apple|NOUN'}], 'priority': 3},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_apple|NOUN'}], 'priority': 4},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_Apple|NOUN'}], 'priority': 5},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_APPLE|NOUN'}], 'priority': 6},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_Apple|LOC'}], 'priority': 7},
      {'key': [
        {'is_joined': False, 'required': False, 'wordsense': 'big|ADJ'}, 
        {'is_joined': False, 'required': False, 'wordsense': 'apple|NOUN'}], 'priority': 8},
      {'key': [
        {'is_joined': False, 'required': False, 'wordsense': 'BIG|ADJ'}, 
        {'is_joined': False, 'required': False, 'wordsense': 'apple|NOUN'}], 'priority': 9},
    ]
    assert result == result_phrase_is_proper_flagged == expected


def test_ranks_joined_keys_higher_than_non_joined_then_ranks_non_proper_phrases_higher_when_flagged_as_not_proper_phrase(the_service, s2v_mock):
    k = [
      { 'wordsense': 'BIG|ADJ', 'required': False },
      { 'wordsense': 'APPLE|NOUN', 'required': False },
    ]
    result = the_service.call(
      k, 
      attempt_phrase_join_for_compound_phrases = True,
      flag_joined_phrase_variations = True,
      phrase_is_proper = False,
    )
    expected = [
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'big_apple|NOUN'}], 'priority': 1},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_APPLE|NOUN'}], 'priority': 2},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_Apple|NOUN'}], 'priority': 3},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_apple|NOUN'}], 'priority': 4},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_Apple|NOUN'}], 'priority': 5},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_apple|NOUN'}], 'priority': 6},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_Apple|LOC'}], 'priority': 7},
      {'key': [
        {'is_joined': False, 'required': False, 'wordsense': 'BIG|ADJ'}, 
        {'is_joined': False, 'required': False, 'wordsense': 'apple|NOUN'}], 'priority': 8},
      {'key': [
        {'is_joined': False, 'required': False, 'wordsense': 'big|ADJ'}, 
        {'is_joined': False, 'required': False, 'wordsense': 'apple|NOUN'}], 'priority': 9},
    ]
    assert result == expected


def test_ranks_based_on_key_match_and_matching_keys_equal_priority_when_flagged_as_proper_phrase(the_service, s2v_mock):
    k = [
      { 'wordsense': 'BIG|ADJ', 'required': False },
      { 'wordsense': 'APPLE|NOUN', 'required': False },
    ]
    result = the_service.call(
      k, 
      attempt_phrase_join_for_compound_phrases = True,
      flag_joined_phrase_variations = True,
    )
    result_phrase_is_proper_flagged = the_service.call(
      k, 
      attempt_phrase_join_for_compound_phrases = True,
      flag_joined_phrase_variations = True,
      phrase_is_proper = True,
    )
    expected = [
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_APPLE|NOUN'}], 'priority': 1},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_Apple|NOUN'}], 'priority': 2},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_apple|NOUN'}], 'priority': 3},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_Apple|LOC'}], 'priority': 4},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_Apple|NOUN'}], 'priority': 4},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_apple|NOUN'}], 'priority': 5},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'big_apple|NOUN'}], 'priority': 6},
      {'key': [
        {'is_joined': False, 'required': False, 'wordsense': 'BIG|ADJ'}, 
        {'is_joined': False, 'required': False, 'wordsense': 'apple|NOUN'}], 'priority': 7},
      {'key': [
        {'is_joined': False, 'required': False, 'wordsense': 'big|ADJ'}, 
        {'is_joined': False, 'required': False, 'wordsense': 'apple|NOUN'}], 'priority': 8},
    ]
    assert result == result_phrase_is_proper_flagged == expected


def test_ranks_joined_keys_higher_than_non_joined_then_ranks_better_case_matches_higher_2(the_service, s2v_mock):
    k = [
      { 'wordsense': 'Big|ADJ', 'required': False },
      { 'wordsense': 'Apple|NOUN', 'required': False },
    ]
    result = the_service.call(
      k, 
      attempt_phrase_join_for_compound_phrases = True,
      flag_joined_phrase_variations = True,
    )
    expected = [
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_Apple|LOC'}], 'priority': 1},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_Apple|NOUN'}], 'priority': 1},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'Big_apple|NOUN'}], 'priority': 2},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_Apple|NOUN'}], 'priority': 3},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_APPLE|NOUN'}], 'priority': 4},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'BIG_apple|NOUN'}], 'priority': 5},
      {'key': [{'is_joined': True, 'required': True, 'wordsense': 'big_apple|NOUN'}], 'priority': 6},
      {'key': [{'is_joined': False, 'required': False, 'wordsense': 'BIG|ADJ'}, {'is_joined': False, 'required': False, 'wordsense': 'apple|NOUN'}], 'priority': 7},
      {'key': [{'is_joined': False, 'required': False, 'wordsense': 'big|ADJ'}, {'is_joined': False, 'required': False, 'wordsense': 'apple|NOUN'}], 'priority': 8},
    ]
    assert result == expected
