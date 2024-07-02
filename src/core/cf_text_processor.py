from helper.utils import read_validate_message_data
from pydantic_model.api_model import EmailInfo


class CareerForgerTextProcessor:
    def __init__(self, nlp_analyser):
        pass

    def process(self, message):
        pass

        #1. decode and validate pubsub message
        email_data = read_validate_message_data(message, EmailInfo)
        raw_email_text = email_data["content"]

        #2. preprocess and clean text for NLP (removing stopwords)

        #3. tokenize text

        #4. extract phrases

        #5. categorise as str/weak/improvements - including categorisation when not matched to regex

        #6.  tag with additional info

        #7. redact PII on certain fields (to be listed)

        #8. clean and return output






