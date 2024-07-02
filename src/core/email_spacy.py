import spacy
from collections import defaultdict
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
import re
import constants
import example_text
# Download NLTK stop words
nltk.download('stopwords')

# Load spaCy model
nlp = spacy.load("models/en_core_web_lg")
stop_words = set(stopwords.words('english'))

# Sample feedback text

# Step 1: Prepare the Text and Remove Stop Words
def preprocess_text(text):
    # Process the text with spaCy to convert it into a Doc object
    doc = nlp(text.lower())
    # Filter out stop words and punctuation from each sentence
    filtered_sents = []
    for sent in doc.sents:
        filtered_tokens = [token.text for token in sent if
                           not token.is_stop and not token.is_punct and token.text not in stop_words]
        filtered_sents.append(" ".join(filtered_tokens))
    return filtered_sents

# Step 2: Identify Key Phrases and Relevant Nouns
def extract_phrases(doc):
    phrases = []
    # Extract noun chunks and named entities from each sentence
    for sent in doc:
        doc_sent = nlp(sent)
        for chunk in doc_sent.noun_chunks:
            # Include the root verb for better context
            root_verb = [token.lemma_ for token in chunk.root.head.children if token.pos_ == "VERB"]
            if root_verb:
                phrases.append(chunk.text + " " + root_verb[0])
            else:
                phrases.append(chunk.text)
        for ent in doc_sent.ents:
            phrases.append(ent.text)
    return phrases

# Step 3: Categorise Phrases/Nouns
# Define words or phrases for each category
categories_words = constants.categories_words

# Create regex patterns for categories
categories_regex = {category: re.compile(r".*\b(" + "|".join(map(re.escape, words)) + r")\b.*", re.IGNORECASE) for
                    category, words in categories_words.items()}

def categorise_phrases(phrases):
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

# Predefined keyword lists for each tag
tags_words = constants.tags_words

# Create regex patterns for tags
tags_regex = {tag: re.compile(r".*\b(" + "|".join(map(re.escape, words)) + r")\b.*", re.IGNORECASE)
              for tag, words in tags_words.items()}

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

# Process the text
filtered_sents = preprocess_text(example_text.five)  # Step 1: Preprocess text
phrases = extract_phrases(filtered_sents)  # Step 2: Extract phrases
categorised = categorise_phrases(phrases)  # Step 3: Categorise phrases
tagged = tag_phrases(phrases)  # Step 4: Tag phrases
results = get_results(categorised, tagged)  # Step 5: Get results

# Output the results
for result in results:
    print(f"Phrase: {result['phrase']}\nCategory: {result['category']}\nTags: {', '.join(result['tags'])}\n")
