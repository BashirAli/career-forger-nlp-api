import os

import nltk
import spacy
from nltk.corpus import stopwords
from textblob import TextBlob

from configuration.env import settings
from helper.utils import read_json_file, build_regex_from_list

CURRENT_PATH = os.path.dirname(__file__)
categories_file = "data/nlp_regex_categories.json"
tags_file = "data/nlp_regex_tags.json"


class NLP_Analyser:
    def __init__(self):
        self.nlp = None  # Placeholder for spaCy NLP pipeline
        self.stop_words = None  # Placeholder for NLTK stopwords list
        self.excluded_entity_types = (
            'PERSON', 'ORG', 'GPE', 'EMAIL')  # tuple of excluded entity types for privacy purposes

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
            model_file_path = "../../tests/integration_tests/models/en_core_web_lg"  # Test environment model path
        else:
            # TODO: Load spaCy model from Google Cloud Storage (GCS) bucket
            model_file_path = ""
            # Example: model_file_path = "gs://your-bucket-name/models/en_core_web_lg"

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
                   and token.ent_type_ not in self.excluded_entity_types
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
                if ent.label_ not in self.excluded_entity_types
            )

        return extracted_phrases  # Return list of extracted relevant phrases


class RegexProcessor:
    def __init__(self):
        self.categories = read_json_file(f"{CURRENT_PATH}/../{categories_file}")
        self.tags = read_json_file(f"{CURRENT_PATH}/../{tags_file}")

    def match_and_redact_pii(self):
        return ""

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
            #TODO improve this as sentiment isnt enough
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
