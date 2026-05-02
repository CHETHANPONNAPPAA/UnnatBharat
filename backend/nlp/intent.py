def detect_intent(text):
    text = text.lower()
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "yo"]
    for g in greetings:
        if g in text:
            return "greeting"

    if any(keyword in text for keyword in ["summarize", "summariser", "summarizer", "summary", "summarise"]):
        return "summarize"
    elif "apply" in text:
        return "application"
    elif "eligible" in text:
        return "eligibility"
    elif "document" in text:
        return "documents"
    elif "benefit" in text:
        return "benefits"
    else:
        return "search"