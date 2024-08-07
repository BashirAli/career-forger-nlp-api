import pytest
from unittest.mock import Mock, patch
import spacy

from core.nlp_analysis import NLP_Analyser, RegexProcessor
from error.custom_exceptions import ManualDLQError


@patch('nltk.download')
@patch('nltk.corpus.stopwords.words', return_value=['a', 'the', 'and'])
def test_set_nltk_resources(mock_stopwords, mock_download):
    analyser = NLP_Analyser()
    analyser.set_nltk_resources()

    assert analyser.stop_words == {'a', 'the', 'and'}
    mock_download.assert_called_with('stopwords')
    mock_stopwords.assert_called_once()


@patch('spacy.load')
@patch('tempfile.TemporaryDirectory', return_value='/mock/temp/dir')
@patch('os.path.exists', return_value=True)
def test_load_spacy_model_production_env(mock_exists, mock_tempdir, mock_spacy_load):
    settings = Mock()
    settings.is_test_env = False
    settings.nlp_bucket = 'my-bucket'
    settings.nlp_dir_to_model = 'my-model-dir'

    gcs_client_mock = Mock()
    analyser = NLP_Analyser()
    analyser.gcs_client = gcs_client_mock
    analyser.load_spacy_model()

    gcs_client_mock.download_model_from_gcs.assert_called_with(settings.nlp_bucket, settings.nlp_dir_to_model,
                                                               '/mock/temp/dir')
    mock_spacy_load.assert_called_once_with('/mock/temp/dir')


@patch('spacy.load')
@patch('os.path.exists', return_value=False)  # Simulate missing meta.json
def test_load_spacy_model_meta_json_missing(mock_exists, mock_spacy_load):
    settings = Mock()
    settings.is_test_env = False

    gcs_client_mock = Mock()
    analyser = NLP_Analyser()
    analyser.gcs_client = gcs_client_mock

    with pytest.raises(ManualDLQError) as excinfo:
        analyser.load_spacy_model()

    assert "meta.json not found when downloading Spacy model to temp dir" in str(excinfo.value)


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
