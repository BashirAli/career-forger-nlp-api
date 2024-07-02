import spacy
from configuration.env import settings
from collections import defaultdict
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
import re

class NLP_Analyser:
    def __init__(self):
        self.nlp = None
        self.stop_words = None

    def set_nltk_resources(self):
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))

    def load_spacy_model(self):
        if settings.is_test_env:
            model_file_path = "../resources/models/en_core_web_lg"

        else:
            # TODO LOAD SPACY MODEL FROM BUCKET
            model_file_path = ""
            pass
        self.nlp = spacy.load(model_file_path)


