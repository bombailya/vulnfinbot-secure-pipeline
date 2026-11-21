import html
import re
from flask import Blueprint, jsonify, request

bp = Blueprint("api", __name__)

MAX_MESSAGE_LENGTH = 500

INJECTION_PATTERNS = (
    "ignore previous instructions",
    "disregard previous instructions",
    "forget your instructions",
    "override system",
    "follow the instructions in this message",
    "you are now in developer mode",
)

PROMPT_DISCLOSURE_PATTERNS = (
    "system prompt",
    "reveal your instructions",
    "show internal configuration",
    "print your prompt",
    "api key",
    "internal config",
)

SENSITIVE_DATA_PATTERNS = (
    "credit card",
    "other users",
    "client database",
    "dump database",
    "social security",
    "account credentials",
)

UNAUTHORIZED_TOOL_PATTERNS = (
    "transfer money",
    "wire transfer",
    "delete account",
    "execute command",
    "run shell",
    "drop table",
)


def _contains_pattern(text: str, patterns: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def _sanitize_output(raw_text: str) -> str:
    cleaned = re.sub(r"sk-[A-Za-z0-9]{10,}", "[REDACTED]", raw_text)
    return html.escape(cleaned, quote=True)


def _generate_mock_ai_response(message: str) -> tuple[str, int]:
    if _contains_pattern(message, INJECTION_PATTERNS):
        return (
            "I cannot override my core instructions. Please ask a general financial question.",
            200,
        )
    if _contains_pattern(message, PROMPT_DISCLOSURE_PATTERNS):
        return "I cannot disclose internal instructions or configuration details.", 200
    if _contains_pattern(message, SENSITIVE_DATA_PATTERNS):
        return (
            "I do not have access to confidential user records or sensitive financial credentials.",
            200,
        )
    if _contains_pattern(message, UNAUTHORIZED_TOOL_PATTERNS):
        return (
            "I am not authorized to execute account actions, transfers, or system commands.",
            200,
        )

    lowered = message.lower()
    if "budget" in lowered:
        reply = "You can start by tracking your income and expenses."
    elif "save" in lowered or "saving" in lowered:
        reply = "Consider setting aside an emergency fund covering 3 to 6 months of expenses."
    else:
        reply = "I can help with general budgeting, saving, and personal finance tips."

    return _sanitize_output(reply), 200


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@bp.route("/api/chat", methods=["POST"])
def chat():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON payload"}), 400

    if "message" not in data:
        return jsonify({"error": "Missing required field: message"}), 400

    message = data["message"]
    if not isinstance(message, str):
        return jsonify({"error": "Field 'message' must be a string"}), 400

    stripped = message.strip()
    if not stripped:
        return jsonify({"error": "Message cannot be empty"}), 400

    if len(stripped) > MAX_MESSAGE_LENGTH:
        return (
            jsonify(
                {
                    "error": f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters"
                }
            ),
            400,
        )

    reply, status_code = _generate_mock_ai_response(stripped)
    return jsonify({"response": reply}), status_code
