from helper.utils import read_validate_message_data
from nlp_analysis import RegexProcessor
from pydantic_model.api_model import EmailInfo


class CareerForgerTextProcessor:
    def __init__(self, nlp_analyser):
        self.nlp_analyser = nlp_analyser
        self.regex_tagger = RegexProcessor()

    def process(self, message):
        # 1. decode and validate pubsub message
        email_data = read_validate_message_data(message, EmailInfo)
        raw_email_text = email_data["content"]

        # 2. preprocess/clean/tokenize sentences for NLP (removing stopwords)
        preprocessed_text = self.nlp_analyser.preprocess_raw_text(raw_email_text)

        # 3. extract phrases from sentences
        feedback_phrases = self.nlp_analyser.extract_relevant_phrases(preprocessed_text)

        # 4. categorise as str/weak/improvements - including categorisation when not matched to regex

        categorised_phrases = self.regex_tagger.categorise_feedback_phrases(feedback_phrases)

        # 5.  tag with additional info and join
        tagged_phrases = self.regex_tagger.categorise_feedback_phrases(feedback_phrases)

        enriched_phrases = self.regex_tagger.join_category_and_tags(categorised_phrases, tagged_phrases)

        # 6. redact PII on certain fields (to be listed)
        redactable_list = ["sender", "recipient", "title"]

        # 7. clean and publish output to pubsub/bq sub
