import json
import re
from config import DATA_PATH, TOP_K
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset once
with open(DATA_PATH, "r", encoding="utf-8") as f:
    schemes = json.load(f)


def _build_documents():
    docs = []
    for s in schemes:
        tags = s.get("tags") or ""
        if isinstance(tags, list):
            tags = " ".join(tags)
        text = " ".join([
            s.get("scheme_name", ""),
            s.get("details", ""),
            s.get("schemeCategory", ""),
            tags,
        ])
        docs.append(text)
    return docs


def _extract_top_k_from_text(text, default=TOP_K):
    text = text.lower()
    digit_match = re.search(r"\btop\s+(\d+)\b", text)
    if digit_match:
        return min(max(int(digit_match.group(1)), 1), 20)

    alt_digit_match = re.search(r"\b(\d+)\s+(?:top|best)\b", text)
    if alt_digit_match:
        return min(max(int(alt_digit_match.group(1)), 1), 20)

    word_map = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
    }
    word_match = re.search(r"\btop\s+(" + "|".join(word_map.keys()) + r")\b", text)
    if word_match:
        return word_map[word_match.group(1)]

    return default


STOPWORDS = {
    "the", "and", "or", "for", "to", "a", "an", "of", "in", "on", "with",
    "by", "is", "it", "this", "that", "please", "me", "schemes", "scheme",
    "top", "best", "give", "i", "you", "us", "my", "your"
}


def _normalize_text(text):
    return re.findall(r"\w+", str(text).lower())


def _extract_keywords(text):
    return {token for token in _normalize_text(text) if token not in STOPWORDS}


def _scheme_keywords(scheme):
    tags = scheme.get("tags") or ""
    if isinstance(tags, list):
        tags = " ".join(tags)
    text = " ".join([
        scheme.get("scheme_name", ""),
        scheme.get("schemeCategory", ""),
        tags,
    ])
    return set(_normalize_text(text))


CATEGORY_KEYWORDS = {
    "education": {"education", "learning", "school", "college", "student", "scholarship", "training"},
    "health": {"health", "healthcare", "medical", "hospital", "insurance", "clinic", "medicine", "wellness"},
    "agriculture": {"agriculture", "agri", "farmer", "farming", "crop", "rural"},
    "finance": {"finance", "financial", "bank", "loan", "investment", "subsidy"},
}


def _filter_schemes_by_category(user_input, all_schemes):
    text = user_input.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            filtered = [
                s for s in all_schemes
                if any(
                    keyword in str(s.get("schemeCategory", "")).lower()
                    or keyword in str(s.get("tags", "")).lower()
                    or keyword in str(s.get("scheme_name", "")).lower()
                    for keyword in keywords
                )
            ]
            return filtered if filtered else all_schemes
    return all_schemes


# Precompute TF-IDF vectors for all documents to avoid refitting every request
_documents = _build_documents()
_vectorizer = TfidfVectorizer()
_doc_vectors = _vectorizer.fit_transform(_documents)
_scheme_keyword_sets = [_scheme_keywords(s) for s in schemes]


def get_best_schemes(user_input):
    # allow users to specify top N results like "top 10"
    top_k = _extract_top_k_from_text(user_input)
    query_keywords = _extract_keywords(user_input)

    # if the user explicitly asks for education schemes, prefer that category
    filtered_schemes = _filter_schemes_by_category(user_input, schemes)
    filtered_indices = [i for i, s in enumerate(schemes) if s in filtered_schemes]

    # require keyword overlap with scheme metadata to avoid dump results
    if query_keywords:
        matched_indices = [
            i for i in filtered_indices
            if _scheme_keyword_sets[i] & query_keywords
        ]
    else:
        matched_indices = filtered_indices

    if not matched_indices:
        return []

    # transform user input using the pre-fit vectorizer
    query_vec = _vectorizer.transform([user_input])
    scores = cosine_similarity(query_vec, _doc_vectors).flatten()

    ranked = sorted(
        ((schemes[i], scores[i]) for i in matched_indices),
        key=lambda x: x[1],
        reverse=True,
    )

    results = []
    for s, score in ranked[:top_k]:
        results.append({
            "name": s.get("scheme_name", ""),
            "details": s.get("details", ""),
            "benefits": s.get("benefits", ""),
            "eligibility": s.get("eligibility", ""),
            "application": s.get("application", ""),
            "documents": s.get("documents", ""),
            "category": s.get("schemeCategory", ""),
            "level": s.get("level", ""),
            "score": float(score),
        })

    return results