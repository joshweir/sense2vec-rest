import pytest
from s2v_similarity import S2vSimilarity

@pytest.fixture
def s2v_mock():
    from sense2vec import Sense2Vec
    import numpy as np
    s2v = Sense2Vec(shape=(10, 4))
    s2v.add('New_York|GPE', np.asarray([1, 1, 1, 1], dtype=np.float32))
    s2v.add('New_York|NOUN', np.asarray([1, 2, 1, 1], dtype=np.float32))
    s2v.add('big|ADJ', np.asarray([2, 5, 4, 2], dtype=np.float32))
    s2v.add('BIG|ADJ', np.asarray([2, 5, 4, 1], dtype=np.float32))
    s2v.add('apple|NOUN', np.asarray([1, 3, 9, 3], dtype=np.float32))
    s2v.add('big_apple|NOUN', np.asarray([6, 6, 6, 6], dtype=np.float32))
    return s2v


@pytest.fixture
def similarity_service(s2v_mock):
    from s2v_util import S2vUtil
    from s2v_senses import S2vSenses
    from s2v_key_case_and_sense_variations import S2vKeyCaseAndSenseVariations
    from s2v_key_commonizer import S2vKeyCommonizer
    s2v_util = S2vUtil(s2v_mock)
    s2v_senses = S2vSenses(s2v_util)
    s2v_key_variations = S2vKeyCaseAndSenseVariations(s2v_util, s2v_senses)
    s2v_key_commonizer = S2vKeyCommonizer()
    the_service = S2vSimilarity(s2v_util, s2v_key_variations, s2v_key_commonizer)

    return the_service


def test_similarity_combinations_includes_phrase_joined(similarity_service, s2v_mock):
    k1 = ["New_York|LOC"]
    k2 = ["big|ADJ", "apple|NOUN"]
    similarity_service.req_args = { 'attempt-phrase-join-for-compound-phrases': 1 }
    k1_common_input = similarity_service.commonize_input(k1)
    k2_common_input = similarity_service.commonize_input(k2)
    expected = [
      [
        [{'wordsense': 'New_York|GPE', 'required': True, 'is_joined': False}], 
        [{'wordsense': 'big_apple|NOUN', 'required': True, 'is_joined': True}],
      ],
      [
        [{'wordsense': 'New_York|NOUN', 'required': True, 'is_joined': False}], 
        [{'wordsense': 'big_apple|NOUN', 'required': True, 'is_joined': True}],
      ], 
    ]
    result = similarity_service.collect_key_variation_combinations(k1_common_input, k2_common_input)
    print('result!!')
    print(result)
    assert result == expected


def test_similarity_combinations_not_in_s2v(similarity_service, s2v_mock):
    k1 = ["apple|NOUN"]
    k2 = ["foo|ADJ", "apple|NOUN"]
    k1_common_input = similarity_service.commonize_input(k1)
    k2_common_input = similarity_service.commonize_input(k2)
    expected = ['foo']
    result = similarity_service.collect_key_variation_combinations(k1_common_input, k2_common_input)
    assert len(result) == 1
    assert len(result[0]) == 2
    assert result[0][0] == [{'required': True, 'wordsense': 'apple|NOUN', 'is_joined': False}]
    assert result[0][1][0] in [{'required': False, 'wordsense': 'BIG|ADJ', 'is_joined': False}, {'required': False, 'wordsense': 'big|ADJ', 'is_joined': False}]
    assert result[0][1][1] == {'required': False, 'wordsense': 'apple|NOUN', 'is_joined': False}


def test_ner_location_fallback_when_key_doesnt_exist(similarity_service, s2v_mock):
    k1 = ["New_York|LOC"]
    k2 = ["big|ADJ", "apple|NOUN"]
    expected = round(float(s2v_mock.similarity(["New_York|GPE"], k2)), 3)
    result = similarity_service.call(k1, k2)
    assert result == expected


def test_param_attempt_phrase_join_for_compound_phrase(similarity_service, s2v_mock):
    k1 = ["New_York|LOC"]
    k2 = ["big|ADJ", "apple|NOUN"]
    k3 = ["big_apple|NOUN"]
    expected = round(float(s2v_mock.similarity(["New_York|GPE"], k3)), 3)
    result = similarity_service.call(k1, k2, { 'attempt-phrase-join-for-compound-phrases': 1 })
    expected_without_compound_phrase_join = round(float(s2v_mock.similarity(["New_York|GPE"], k2)), 3)
    result_without_compound_phrase_join = similarity_service.call(k1, k2)
    assert result == expected
    assert result_without_compound_phrase_join != expected
    assert result_without_compound_phrase_join == expected_without_compound_phrase_join
    