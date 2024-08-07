import pytest
from unittest.mock import Mock, patch
import spacy

from core.nlp_analysis import NLP_Analyser, RegexProcessor


@patch('nltk.download')
@patch('nltk.corpus.stopwords.words')
def test_set_nltk_resources(mock_stopwords, mock_download):
    mock_stopwords.return_value = ['a', 'the', 'and']
    analyser = NLP_Analyser()
    analyser.set_nltk_resources()

    assert analyser.stop_words == {'a', 'the', 'and'}
    mock_download.assert_called_with('stopwords')
    mock_stopwords.assert_called_once()


@patch('gcp.gcs.GoogleCloudStorage')
@patch('spacy.load')
def test_load_spacy_model_test_env(mock_spacy_load, mock_gcs_client):
    # Mock settings
    settings = Mock()
    settings.is_test_env = True

    analyser = NLP_Analyser()
    analyser.gcs_client = mock_gcs_client
    analyser.load_spacy_model()

    mock_spacy_load.assert_called_with("../tests/integration_tests/models/en_core_web_lg")


@patch('gcp.gcs.GoogleCloudStorage')
@patch('spacy.load')
def test_load_spacy_model_production_env(mock_spacy_load, mock_gcs_client):
    # Mock settings
    settings = Mock()
    settings.is_test_env = False
    settings.nlp_bucket = 'my-bucket'
    settings.nlp_dir_to_model = 'my-model-dir'

    analyser = NLP_Analyser()
    analyser.gcs_client = mock_gcs_client
    analyser.load_spacy_model()

    # Ensure the model path was loaded correctly
    mock_spacy_load.assert_called_once_with("tmp/en_core_web_lg")


def test_preprocess_raw_text():
    analyser = NLP_Analyser()
    analyser.nlp = spacy.load('en_core_web_sm')
    analyser.stop_words = {'a', 'the', 'and'}

    text = "Alice and Bob went to the store."
    processed = analyser.preprocess_raw_text(text)

    assert processed == ["Alice Bob went store"]


def test_extract_relevant_phrases():
    analyser = NLP_Analyser()
    analyser.nlp = spacy.load('en_core_web_sm')

    tokens = ["Alice and Bob went to the store."]
    phrases = analyser.extract_relevant_phrases(tokens)

    assert "store" in phrases


def test_redact_personal_info_in_text():
    analyser = NLP_Analyser()
    analyser.nlp = spacy.load('en_core_web_sm')

    text = "Alice's email is alice@example.com."
    redacted_text = analyser.redact_personal_info_in_text(text)

    assert "[REDACTED]" in redacted_text
    assert "alice@example.com" not in redacted_text


@patch('your_module.read_json_file')
def test_categorise_feedback_phrases(mock_read_json_file):
    # Mock categories
    mock_read_json_file.return_value = {
        "strengths": r"\bexcellent\b",
        "weaknesses": r"\bpoor\b"
    }

    processor = RegexProcessor()

    phrases = ["The service was excellent", "The food was poor", "Average experience"]
    categorised = processor.categorise_feedback_phrases(phrases)

    assert categorised["The service was excellent"] == "strengths"
    assert categorised["The food was poor"] == "weaknesses"
    # Average experience has no regex match, so use sentiment
    assert categorised["Average experience"] == "improvements"


@patch('your_module.read_json_file')
def test_tag_feedback_phrases(mock_read_json_file):
    mock_read_json_file.return_value = {
        "tag1": r"\bquick\b",
        "tag2": r"\bfriendly\b"
    }

    processor = RegexProcessor()

    phrases = ["The quick brown fox", "Friendly staff", "Good service"]
    tagged = processor.tag_feedback_phrases(phrases)

    assert tagged["The quick brown fox"] == ["tag1"]
    assert tagged["Friendly staff"] == ["tag2"]
    assert tagged["Good service"] == []


def test_join_category_and_tags():
    categorised = {
        "The service was excellent": "strengths",
        "The food was poor": "weaknesses"
    }

    tagged = {
        "The service was excellent": ["tag1"],
        "The food was poor": []
    }

    results = RegexProcessor.join_category_and_tags(categorised, tagged)

    assert results == [
        {'phrase': "The service was excellent", 'category': "strengths", 'tags': ["tag1"]},
        {'phrase': "The food was poor", 'category': "weaknesses", 'tags': []}
    ]
