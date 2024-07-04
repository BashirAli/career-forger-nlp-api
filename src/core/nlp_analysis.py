import spacy
from configuration.env import settings
from helper.utils import read_json_file
from collections import defaultdict
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
import re
import os

CURRENT_PATH = os.path.dirname(__file__)
categories_file = "data/nlp_regex_categories.json"
tags_file = "data/nlp_regex_tags.json"


#
# categories_regex = {category: re.compile(r".*\b(" + "|".join(map(re.escape, words)) + r")\b.*", re.IGNORECASE) for
#                     category, words in categories_words.items()}
# tags_regex = {tag: re.compile(r".*\b(" + "|".join(map(re.escape, words)) + r")\b.*", re.IGNORECASE)
#               for tag, words in tags_words.items()}
class NLP_Analyser:
    def __init__(self):
        self.nlp = None
        self.stop_words = None
        self.categories = read_json_file(f"{CURRENT_PATH}/../{categories_file}")
        self.tags = read_json_file(f"{CURRENT_PATH}/../{tags_file}")

    def set_nltk_resources(self):
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))

    def load_spacy_model(self):
        if settings.is_test_env:
            model_file_path = "../../tests/integration_tests/models/en_core_web_lg"

        else:
            # TODO LOAD SPACY MODEL FROM GCS BUCKET
            # https://stackoverflow.com/questions/65071321/save-and-load-a-spacy-model-to-a-google-cloud-storage-bucket
            model_file_path = ""
            pass
        self.nlp = spacy.load(model_file_path)

    def preprocess_raw_text(self, text):
        # Process the text with spaCy to convert it into a Doc object
        spacy_doc_object = self.nlp(text.lower())
        # Filter out stop words and punctuation from each sentence
        filtered_tokens = []
        for doc_token in spacy_doc_object.sents:
            filtered_tokens = [token.text for token in doc_token if
                               not token.is_stop and not token.is_punct and token.text not in self.stop_words]
            filtered_tokens.append(" ".join(filtered_tokens))
        return filtered_tokens

    def extract_feedback_phrases(self, filtered_doc_tokens):
        #TODO make this more better at extracting phrases 
        extracted_phrases = []
        # Extract noun chunks and named entities from each sentence
        for doc_token in filtered_doc_tokens:
            doc_sent = self.nlp(doc_token)
            for chunk in doc_sent.noun_chunks:
                # Include the root verb for better context
                root_verb = [token.lemma_ for token in chunk.root.head.children if token.pos_ == "VERB"]
                if root_verb:
                    extracted_phrases.append(chunk.text + " " + root_verb[0])
                else:
                    extracted_phrases.append(chunk.text)
            for ent in doc_sent.ents:
                extracted_phrases.append(ent.text)
        return extracted_phrases

    def categorise_feedback_phrases(self, phrases):
        categorised = {"strengths": [], "weaknesses": [], "improvements": []}
        for phrase in phrases:
            matched = False
            # Check if the phrase matches any predefined regex patterns for categories
            for category, regex in categories_regex.items():
                if regex.match(phrase):
                    categorised[category].append(phrase)
                    matched = True
                    break
            # If the phrase doesn't match any predefined regex patterns
            if not matched:
                # Analyse sentiment using TextBlob polarity
                polarity = TextBlob(phrase).sentiment.polarity
                # Categorise based on sentiment polarity
                if polarity > 0:
                    categorised["strengths"].append(phrase)
                elif polarity < 0:
                    categorised["weaknesses"].append(phrase)
                else:
                    categorised["improvements"].append(phrase)
        return categorised

    # Step 4: Tag Phrases/Nouns
    def tag_phrases(phrases):
        tagged = defaultdict(list)
        for phrase in phrases:
            for tag, regex in tags_regex.items():
                if regex.match(phrase):
                    tagged[phrase].append(tag)
        return tagged

    # Step 5: Return Results
    def get_results(categorised, tagged):
        results = []
        for category, phrases in categorised.items():
            for phrase in phrases:
                results.append({"phrase": phrase, "category": category, "tags": tagged[phrase]})
        return results
