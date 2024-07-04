import re

import nltk
import spacy
from nltk.corpus import stopwords

# Download NLTK stop words
nltk.download('stopwords')

# Load spaCy model
nlp = spacy.load("en_core_web_lg")
stop_words = set(stopwords.words('english'))

# Sample feedback text
example_text = """
Your technical skills are impressive, especially your proficiency in Python and algorithms. 
However, there is room for improvement in your knowledge of machine learning algorithms and data structures. 
In non-technical aspects, your communication skills are excellent, and you work well in teams. 
However, sometimes you struggle with time management and meeting deadlines, which can affect project timelines. 
You might want to focus on developing your project management skills and improving your ability to prioritise tasks effectively. 
Your involvement in extracurricular activities, such as the coding club and volunteering for community projects, is commendable. 
You showed remarkable leadership during the last project, but there were instances where you could have delegated tasks more efficiently. 
For career advice, I suggest you keep honing your public speaking skills and seek opportunities for mentorship to further enhance your leadership abilities.
"""


# Step 1: Prepare the Text and Remove Stop Words
def preprocess_text(text):
    # Process the text with spaCy to convert it into a Doc object
    doc = nlp(text.lower())
    # Filter out stop words and punctuation from each sentence
    return [
        " ".join(
            token.text for token in sent if not token.is_stop and not token.is_punct and token.text not in stop_words)
        for sent in doc.sents
    ]


# Step 2: Identify Key Phrases and Relevant Nouns
def extract_phrases(sentences):
    phrases = []
    # Process each preprocessed sentence
    for sent in sentences:
        doc_sent = nlp(sent)
        for chunk in doc_sent.noun_chunks:
            # Include the root verb for better context
            root_verb = next((token.lemma_ for token in chunk.root.head.children if token.pos_ == "VERB"), None)
            phrase = f"{chunk.text} {root_verb}" if root_verb else chunk.text
            phrases.append(phrase)
        for ent in doc_sent.ents:
            phrases.append(ent.text)
    return phrases


# Step 3: Categorise Phrases/Nouns
# Define words or phrases for each category
categories_words = {
    "strengths": [
        "impress",
        "proficien",
        "excell",
        "commend",
        "remarkable",
        "outstanding",
        "exceptional",
        "superb",
        "skill",
        "talent",
        "capable",
        "reliable",
        "dependable",
        "diligent",
        "innovative",
        "creative",
        "adaptable",
        "collaborat",
        "leader",
        "dedicated",
        "motivated",
        "enthusiastic",
        "passionate",
        "knowledgeable",
        "expert",
        "proactive",
        "efficien"
    ],
    "weaknesses": [
        "room for",
        "struggle",
        "could have",
        "lack",
        "weak",
        "inadequate",
        "deficient",
        "subpar",
        "below expect",
        "careless",
        "negligent",
        "error-prone",
        "disorganised",
        "unfocused",
        "distracted",
        "procrastinate",
        "misses deadlines",
        "you show a lack of ",
        "unmotivated",
        "rigid",
        "resistant to ",
        "reactive",
        "complacent",
        "overconfident",
        "hesitant"
    ],
    "improvements": [
        "focus on",
        "improv",
        "keep",
        "seek",
        "could benefit",
        "should work on",
        "recommend",
        "suggest",
        "advised to",
        "aim to",
        "encouraged to",
        "prioritise",
        "could enhance",
        "should develop",
        "could improv",
        "recommended to",
        "should consider",
        "could strengthen",
        "work on",
        "should practice",
        "should seek",
        "could work on",
        "aim to",
        "advise",
        "suggest working on"
    ]
}

# Create regex patterns for categories
categories_regex = {category: re.compile(r".*\b(" + "|".join(map(re.escape, words)) + r")\b.*", re.IGNORECASE) for
                    category, words in categories_words.items()}

from textblob import TextBlob  # Assuming TextBlob is imported


def categorise_phrases(phrases):
    categorised = {}

    for phrase in phrases:
        matched_category = None

        # Check if the phrase matches any predefined regex patterns for categories
        for category, regex in categories_regex.items():
            if regex.search(phrase):
                matched_category = category
                break

        # If no regex match, analyze sentiment using TextBlob polarity
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


# Predefined keyword lists for each tag
tags_words = {
    "technical": [
        "technical",
        "python",
        "algorithm",
        "machine learning",
        "data",
        "software",
        "coding",
        "program",
        "technical expertise",
        "sql",
        "system",
        "data engineer",
        "data science",
        "artificial intelligence",
        "cloud computing",
        "database",
        "network",
        "architecture",
        "IT skills",
        "DevOps",
        "web",
        "develop",
        "backend",
        "frontend",
        "cybersecurity",
        "blockchain",
        "mobile",
        "testing",
        "automation",
        "version control",
        "git"
    ],
    "non-technical": [
        "non technical",
        "communication",
        "teams",
        "time manag",
        "project manag",
        "timeline",
        "leadership",
        "teamwork",
        "collaborat",
        "soft skill",
        "problem solv",
        "critical think",
        "creativity",
        "adaptability",
        "flexibility",
        "interpersonal",
        "conflict resolution",
        "emotional intelligence",
        "negotiat",
        "public speak",
        "presentation",
        "customer service",
        "client relation",
        "decision mak",
        "organisational",
        "multitask",
        "attention to detail",
        "work ethic",
        "professional",
        "motivat",
        "enthusiasm",
        "dedicat",
        "reliability",
        "dependability",
        "initiative",
        "stress management",
        "work life"
    ],
    "next_steps": [
        "developing",
        "improv",
        "prioritise",
        "honing",
        "seek opportunities",
        "focus on",
        "enhancing skill",
        "next step",
        "career progress",
        "career develop",
        "growth area",
        "plan",
        "professional growth",
        "future goal",
        "short term goal",
        "long term goal",
        "career planning",
        "personal develop",
        "continuous improvement",
        "skill enhancement",
        "learning new",
        "upskill",
        "reskill",
        "professional train",
        "certificat",
        "workshop",
        "seminar",
        "networking",
        "mentor",
        "coach",
        "feedback",
        "self improvement"
    ],
    "standout_performance": [
        "remarkable",
        "outstanding",
        "exceptional",
        "superb",
        "noteworthy",
        "excellent",
        "excell",
        "superior",
        "first rate",
        "top notch",
        "stellar",
        "impressive",
        "exemplary",
        "brilliant",
        "fantastic",
        "phenomenal",
        "extraordinary",
        "unparalleled",
        "unmatched",
        "unrivaled",
        "leading",
        "trailblasing",
        "groundbreaking",
        "pioneer",
        "dominant",
        "commendable",
        "laudable",
        "notable",
        "significant achievement",
        "major accomplishment",
        "heroic",
        "valiant",
        "distinguished",
        "acclaimed",
        "celebrated",
        "honored",
        "recognised",
        "praised",
        "admired",
        "respected",
        "appreciated",
        "acknowledged"
    ],
    "career_advice": [
        "career advice",
        "seek mentor",
        "leadership abilit",
        "career path",
        "journey",
        "transition",
        "role",
        "career change",
        "advance",
        "promotion",
        "career move",
        "professional advice",
        "job",
        "interview",
        "resume",
        "cover letter",
        "networking strategies",
        "industry",
        "career goal",
        "job market",
        "culture",
        "salary negotiation",
        "workplace",
        "professional relationship",
        "career opportunities",
        "job satisfaction",
        "workplace productivity",
        "performance",
        "career success",
        "professional milestone",
        "goal setting",
        "self assessment",
        "strengths",
        "weaknesses",
        "review",
        "career mentor",
        "personal brand"
    ],
    "other": [
        "club",
        "volunteer",
        "extracurricular",
        "community",
        "side project",
        "hobbies",
        "interests",
        "passions",
        "personal project",
        "charity",
        "philanthropy",
        "social responsibil",
        "team outing",
        "company event",
        "networking event",
        "industry conference",
        "trade show",
        "professional association",
        "affinity group",
        "diversity initiative",
        "inclusivity program",
        "workshop",
        "seminar",
        "webinar",
        "online course",
        "elearning",
        "professional member",
        "certification",
        "award",
        "recognition",
        "competition",
        "hackathon",
        "marathon",
        "team building",
        "retreat",
        "volunteer program",
        "fundraiser",
        "scholarship",
        "grants",
        "fellowship"
    ]
}

# Create regex patterns for tags
tags_regex = {tag: re.compile(r".*\b(" + "|".join(map(re.escape, words)) + r")\b.*", re.IGNORECASE)
              for tag, words in tags_words.items()}


# Step 4: Tag Phrases/Nouns
def tag_phrases(phrases):
    return {
        phrase: [tag for tag, regex in tags_regex.items() if regex.match(phrase)]
        for phrase in phrases
    }


# Step 5: Return Results
def get_results(categorised, tagged):
    results = []

    for phrase in categorised.keys():
        result = {
            'phrase': phrase,
            'category': categorised[phrase],
            'tags': tagged.get(phrase, [])
        }
        results.append(result)

    return results

# Process the text
filtered_sents = preprocess_text(example_text)  # Step 1: Preprocess text
print(filtered_sents)
phrases = extract_phrases(filtered_sents)  # Step 2: Extract phrases
print(phrases)
categorised = categorise_phrases(phrases)  # Step 3: Categorise phrases
print(categorised)
tagged = tag_phrases(phrases)  # Step 4: Tag phrases
print(tagged)
results = get_results(categorised, tagged)  # Step 5: Get results

# Output the results
for result in results:
    print(f"Phrase: {result['phrase']}\nCategory: {result['category']}\nTags: {', '.join(result['tags'])}\n")
