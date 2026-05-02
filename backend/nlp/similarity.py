from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def find_similarity(user_input, documents):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([user_input] + documents)

    scores = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
    return scores