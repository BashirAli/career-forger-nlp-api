import os
import tempfile
import nltk
import re
import spacy
from nltk.corpus import stopwords
from textblob import TextBlob
from configuration.logger_config import logger_config

from error.custom_exceptions import ManualDLQError
from gcp.gcs import GoogleCloudStorage
from configuration.env import settings
from helper.utils import read_json_file, build_regex_from_list
from pydantic_model.api_model import ErrorEnum

CURRENT_PATH = os.path.dirname(__file__)
categories_file = "data/nlp_regex_categories.json"
tags_file = "data/nlp_regex_tags.json"


class NLP_Analyser:
    def __init__(self):
        self.nlp = None  # Placeholder for spaCy NLP pipeline
        self.stop_words = None  # Placeholder for NLTK stopwords list
        self.excluded_entity_types_in_txt = (
            'PERSON', 'ORG', 'GPE', 'EMAIL')  # tuple of excluded entity types for privacy purposes

        self.redact_text = '[REDACTED]'

        self.gcs_client = GoogleCloudStorage(settings.gcp_project_id)

    def set_nltk_resources(self):
        """
        Method to download NLTK stopwords resource and set up stop words for filtering.
        """
        nltk.download('stopwords')  # Download NLTK stopwords if not already downloaded
        self.stop_words = set(stopwords.words('english'))  # Set stopwords for English language

    def load_spacy_model(self):
        """
        Method to load spaCy model based on environment (test or production).
        """
        if settings.is_test_env:
            model_file_path = "../tests/integration_tests/models/en_core_web_lg"  # Test environment model path
        else:
            with tempfile.TemporaryDirectory() as model_file_path:
                # Download the entire model folder from GCS to the temporary directory
                self.gcs_client.download_model_from_gcs(settings.nlp_bucket, settings.nlp_dir_to_model, model_file_path)

                # Check if meta.json is present
                meta_path = os.path.join(model_file_path, 'meta.json')
                if not os.path.exists(meta_path):
                    error_value = f"meta.json not found when downloading Spacy model to temp dir: {model_file_path}"
                    raise ManualDLQError(
                        original_request=logger_config.context.get().get("original_request"),
                        error_desc=error_value,
                        error_stage=ErrorEnum.FILE_NOT_FOUND,
                    )

        self.nlp = spacy.load(model_file_path)  # Load spaCy model into self.nlp

    def preprocess_raw_text(self, text):
        """
        Method to preprocess raw text:
        - Converts text to lowercase
        - Removes stopwords, punctuation, and entities like names, addresses, emails using spaCy's entity recognition.

        Args:
        - text (str): Raw text to be preprocessed.

        Returns:
        - List of cleaned sentences.
        """
        doc = self.nlp(text.lower())  # Process the text with spaCy and convert to lowercase

        cleaned_sentences = []

        for sent in doc.sents:  # Iterate through each sentence in the processed document
            # Filter tokens to exclude stopwords, punctuation, and specific entity types
            cleaned_tokens = [
                token.text for token in sent
                if not token.is_stop and not token.is_punct
                   and token.text not in self.stop_words
                   and token.ent_type_ not in self.excluded_entity_types_in_txt
            ]
            cleaned_sentences.append(" ".join(cleaned_tokens))  # Join cleaned tokens into a sentence

        return cleaned_sentences  # Return list of cleaned sentences

    def extract_relevant_phrases(self, filtered_doc_tokens):
        """
        Method to extract relevant phrases from preprocessed document tokens.
        Uses spaCy for identifying noun chunks and named entities, excluding specific entity types.

        Args:
        - filtered_doc_tokens (list): List of preprocessed document tokens.

        Returns:
        - List of extracted relevant phrases.
        """
        extracted_phrases = []

        for doc_token in filtered_doc_tokens:  # Iterate through each preprocessed document token
            doc_sent = self.nlp(doc_token)  # Process the token with spaCy

            for chunk in doc_sent.noun_chunks:  # Iterate through noun chunks in the processed token
                # Get root verb for better context if available
                root_verb = next((token.lemma_ for token in chunk.root.head.children if token.pos_ == "VERB"), None)
                if root_verb:
                    extracted_phrases.append(chunk.text + " " + root_verb)  # Append noun chunk with root verb
                else:
                    extracted_phrases.append(chunk.text)  # Append noun chunk

            # Extend extracted_phrases with named entities, excluding specific entity types
            extracted_phrases.extend(
                ent.text for ent in doc_sent.ents
                if ent.label_ not in self.excluded_entity_types_in_txt
            )

        return extracted_phrases  # Return list of extracted relevant phrases

    def redact_personal_info_in_text(self, text):
        """
        Method to redact PII data such as names, addresses, emails, and mobile numbers using spaCy's entity recognition.

        Args:
        - text (str): Raw text from which PII needs to be redacted.

        Returns:
        - str: Text with PII redacted.
        """
        doc = self.nlp(text)  # Process the text with spaCy

        redacted_text = text

        # Regular expression for mobile numbers (simplified example, may need adjustment)
        mobile_number_pattern = re.compile(r'\b(\+?\d{1,3})?[-.\s]?(\d{1,4})[-.\s]?(\d{1,4})[-.\s]?(\d{1,9})\b')

        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                # Split the person's name and redact the last name if applicable
                name_parts = ent.text.split()
                if len(name_parts) > 1:
                    first_name = name_parts[0]
                    last_name_redacted = ' '.join([self.redact_text for _ in name_parts[1:]])
                    redacted_text = redacted_text.replace(ent.text, first_name + ' ' + last_name_redacted)
            elif ent.label_ == 'EMAIL':
                # Redact email address except for domain part
                local_part, domain_part = ent.text.split('@')
                redacted_text = redacted_text.replace(local_part, self.redact_text)
            elif ent.label_ == 'GPE':
                # Assuming GPE is used for geopolitical entities (like cities and countries)
                # Keep only city and country if applicable
                geopolitical_parts = ent.text.split(',')
                if len(geopolitical_parts) > 1:
                    redacted_text = redacted_text.replace(ent.text, geopolitical_parts[-1].strip())
            elif ent.label_ == 'PHONE':
                # Redact mobile numbers except for the country code
                matches = re.findall(mobile_number_pattern, ent.text)
                for match in matches:
                    if match[0]:  # Check if there is a country code
                        redacted_text = redacted_text.replace(match[1], self.redact_text)
                    else:
                        redacted_text = redacted_text.replace(ent.text, self.redact_text)

        return redacted_text


class RegexProcessor:
    def __init__(self):
        self.categories = read_json_file(f"{CURRENT_PATH}/../{categories_file}")
        self.tags = read_json_file(f"{CURRENT_PATH}/../{tags_file}")

    def categorise_feedback_phrases(self, extracted_phrases):
        """
        Categorize feedback phrases based on predefined regex patterns and sentiment analysis.
        Args:
            extracted_phrases (list): List of phrases to categorize.
        Returns:
            dict: Dictionary mapping phrases to their categories.
        """
        categorised = {}
        categories_regex = build_regex_from_list(self.categories)

        for phrase in extracted_phrases:
            matched_category = None

            # Check if the phrase matches any predefined regex patterns for categories
            for category, regex in categories_regex.items():
                if regex.search(phrase):
                    matched_category = category
                    break

            # If no regex match, analyze sentiment using TextBlob polarity
            # TODO improve this as sentiment isn't enough
            if matched_category is None:
                polarity = TextBlob(phrase).sentiment.polarity
                if polarity > 0:
                    matched_category = "strengths"
                elif polarity < 0:
                    matched_category = "weaknesses"
                else:
                    matched_category = "improvements"

            # Store the matched category for the phrase
            categorised[phrase] = matched_category

        return categorised

    def tag_feedback_phrases(self, extracted_phrases):
        """
        Tag feedback phrases based on predefined regex patterns.
        Args:
            extracted_phrases (list): List of phrases to tag.
        Returns:
            dict: Dictionary mapping phrases to their tags.
        """
        tags_regex = build_regex_from_list(self.tags)
        # TODO improve this as its not tagging all phrases

        return {
            phrase: [tag for tag, regex in tags_regex.items() if regex.match(phrase)]
            for phrase in extracted_phrases
        }

    @staticmethod
    def join_category_and_tags(categorised, tagged):
        results = []

        for phrase in categorised.keys():
            result = {
                'phrase': phrase,
                'category': categorised[phrase],
                'tags': tagged.get(phrase, [])
            }
            results.append(result)

        return results
