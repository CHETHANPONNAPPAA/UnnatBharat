
nlp = None


def _load_spacy():
    global nlp
    try:
        import spacy

        try:
            nlp = spacy.load("en_core_web_sm")
        except Exception:
            nlp = spacy.blank("en")
    except Exception:
        nlp = None


def extract_entities(text):
   
    #Uses spaCy if available; otherwise extracts capitalized tokens as a fallback.

    global nlp
    if nlp is None:
        _load_spacy()

    if nlp is not None:
        doc = nlp(text)
        entities = []
        for ent in doc.ents:
            entities.append({"text": ent.text, "label": ent.label_})
        return entities

    # fallback: simple regex-based proper noun finder
    import re

    tokens = re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b", text)
    return [{"text": t, "label": "PROPER_NOUN"} for t in tokens]