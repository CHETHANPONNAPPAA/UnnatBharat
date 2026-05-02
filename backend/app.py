import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import session

from nlp.intent import detect_intent
from nlp.ner import extract_entities
from services.scheme_service import get_best_schemes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
# a simple secret key for session; in production use a secure env var
app.secret_key = "dev-secret-key"
CORS(app)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def index():
    return jsonify({"service": "SchemeSathi backend", "status": "running"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        if not data or "message" not in data:
            return jsonify({"error": "missing 'message' in request body"}), 400

        user_input = data.get("message", "")

        # NLP pipeline
        intent = detect_intent(user_input)
        entities = extract_entities(user_input)

        # Greeting response
        if intent == "greeting":
            reply_text = "hi how can i assist you"

            # store last interaction but don't overwrite last_query on greetings
            session["last_intent"] = intent
            return jsonify({"intent": intent, "entities": entities, "schemes": [], "reply": f"<div>{reply_text}</div>"})

        # summarization requests should use the previous query when needed
        if intent == "summarize":
            use_last_query = _is_handoff_summarize(user_input)
            if use_last_query:
                query = session.get("last_query")
                if not query:
                    reply_text = "I don't have a previous request to summarize. Please ask about a scheme first."
                    session["last_intent"] = intent
                    return jsonify({
                        "intent": intent,
                        "entities": entities,
                        "schemes": [],
                        "reply": f"<div>{reply_text}</div>"
                    })
            else:
                query = user_input
                session["last_query"] = query

            schemes = get_best_schemes(query)
            session["last_intent"] = intent
            return jsonify({
                "intent": intent,
                "entities": entities,
                "schemes": schemes,
                "reply": _build_summary_html(query, schemes)
            })

        
        schemes = get_best_schemes(user_input)
        if not schemes:
            reply_text = "Please give me a valid input."
            session["last_intent"] = intent
            return jsonify({
                "intent": intent,
                "entities": entities,
                "schemes": [],
                "reply": f"<div>{reply_text}</div>"
            })

        session["last_query"] = user_input
        session["last_intent"] = intent

        return jsonify({
            "intent": intent,
            "entities": entities,
            "schemes": schemes,
            "reply": _build_reply_html(intent, entities, schemes)
        })
    except Exception as e:
        logger.exception("Error handling /chat request")
        return jsonify({"error": str(e)}), 500


def _build_reply_html(intent, entities, schemes):
   

    #This is rendered by the frontend directly into the chat UI.

    if not schemes:
        return "<div>Please give me a valid input.</div>"

    html = ""
    for s in schemes:
        html += f'<div class="card">'
        html += f'<b>{s.get("name","Unnamed")}</b><br>'
        details = s.get("details", "")
        # keep description short
        html += f'<div class="card-details">{details[:400]}{"..." if len(details)>400 else ""}</div>'
        html += f'<div><b>Benefits:</b> {s.get("benefits","-")}</div>'
        html += f'<div><b>Eligibility:</b> {s.get("eligibility","-")}</div>'
        html += f'<div><b>Apply:</b> {s.get("application","-")}</div>'
        html += '</div>'

    return html


def _is_handoff_summarize(text):
    normalized = text.strip().lower()
    return normalized in {
        "summarize",
        "summarize me",
        "summarize this",
        "summarize that",
        "please summarize",
        "summarize please",
    }


def _build_summary_html(query, schemes):
    if not schemes:
        return "<div>Please give me a valid input.</div>"

    html = f'<div><b>Summary for:</b> {query}</div>'
    for s in schemes:
        html += f'<div class="card">'
        html += f'<b>{s.get("name","Unnamed")}</b><br>'
        summary_text = s.get("details", "")
        html += f'<div class="card-details">{summary_text[:300]}{"..." if len(summary_text) > 300 else ""}</div>'
        html += f'<div><b>Benefits:</b> {s.get("benefits","-")}</div>'
        html += f'<div><b>Eligibility:</b> {s.get("eligibility","-")}</div>'
        html += '</div>'

    return html


if __name__ == "__main__":
   
    app.run(host="0.0.0.0", port=5000, debug=False)