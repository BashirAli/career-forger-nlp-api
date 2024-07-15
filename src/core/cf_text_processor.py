import logging

from helper.utils import read_validate_message_data
from core.nlp_analysis import RegexProcessor
from pydantic_model.api_model import EmailInfo
from gcp.pubsub import PubSubPublisher
from configuration.env import settings
import pendulum

class CareerForgerTextProcessor:
    def __init__(self, nlp_analyser):
        self.nlp_analyser = nlp_analyser
        self.regex_tagger = RegexProcessor()
        self._pubsub_client = PubSubPublisher(project_id=settings.gcp_project_id,
                                              topic=settings.pubsub_publish_topic_id)

    def process(self, message):
        pubsub_data = {}
        # 1. decode and validate pubsub message
        email_data = read_validate_message_data(message, EmailInfo).model_dump(exclude_none=True)
        logging.info("REQUEST DUMP")
        logging.info(email_data)

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
        pubsub_data["enriched_phrases"] = enriched_phrases
        logging.info("ENRICHED PHRASES")
        logging.info(enriched_phrases)

        # 6. redact PII on certain fields
        redactable_list = ["sender", "recipient", "title"]
        for sensitive_data in redactable_list:
            pubsub_data[sensitive_data] = self.nlp_analyser.redact_personal_info_in_text(raw_email_text[sensitive_data])

        logging.info("PUBSUB DATA")
        logging.info(pubsub_data)

        # 7. clean and publish output to pubsub/bq sub
        self._pubsub_client.publish(data=pubsub_data, source_publish_time=str(pendulum.now("Europe/London")))

