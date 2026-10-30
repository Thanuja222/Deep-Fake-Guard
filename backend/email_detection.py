import re
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify

email_bp = Blueprint("email_detection", __name__)

# Common phishing and email fraud keywords
SUSPICIOUS_KEYWORDS = [
    "verify your account",
    "account suspended",
    "account blocked",
    "urgent action required",
    "update your password",
    "confirm your identity",
    "click here immediately",
    "claim your reward",
    "you have won",
    "lottery winner",
    "free gift",
    "limited time offer",
    "bank account blocked",
    "unauthorized transaction",
    "send otp",
    "share otp",
    "share your password",
    "confirm bank details",
    "transfer money",
    "pay immediately",
    "refund pending",
    "kyc update",
    "upi pin",
    "card details"
]

# Common URL shorteners used to hide destination links
URL_SHORTENERS = [
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "is.gd",
    "cutt.ly",
    "shorturl.at"
]

# Trusted domains are NOT automatically guaranteed safe.
# This list is only used to identify obvious lookalike domains.
KNOWN_BRANDS = [
    "google.com",
    "microsoft.com",
    "amazon.com",
    "paypal.com",
    "apple.com",
    "sbi.co.in",
    "hdfcbank.com",
    "icicibank.com"
]


def extract_urls(text):
    pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+'
    return re.findall(pattern, text, re.IGNORECASE)


def analyse_email(sender, subject, body):

    score = 0
    indicators = []

    sender = sender.lower().strip()
    subject = subject.lower().strip()
    body = body.lower().strip()

    email_text = subject + " " + body

    # 1. Check suspicious keywords
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in email_text:
            score += 10
            indicators.append(
                f"Suspicious phrase detected: {keyword}"
            )

    # 2. Check sender email format
    if "@" not in sender or "." not in sender.split("@")[-1]:
        score += 20
        indicators.append("Invalid or suspicious sender email format")

    # 3. Check for suspicious sender names
    suspicious_sender_words = [
        "admin", "security", "support", "bank",
        "verification", "payment", "alert"
    ]

    if any(word in sender for word in suspicious_sender_words):
        indicators.append(
            "Sender uses a security or financial-related name; verify independently"
        )
        score += 5

    # 4. Check URLs
    urls = extract_urls(body)

    for url in urls:
        clean_url = url.rstrip(".,;!?)")
        if clean_url.lower().startswith("www."):
            clean_url = "http://" + clean_url

        domain = urlparse(clean_url).hostname or ""
        domain = domain.lower()

        if domain in URL_SHORTENERS:
            score += 20
            indicators.append(
                f"Shortened URL detected: {domain}"
            )

        if clean_url.lower().startswith("http://"):
            score += 10
            indicators.append(
                f"Unencrypted HTTP link detected: {domain}"
            )

        # Look for suspicious IP-address links
        if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", domain):
            score += 25
            indicators.append(
                "Link uses an IP address instead of a domain name"
            )

        # Check for misleading brand-like domains
        for brand in KNOWN_BRANDS:
            if brand in domain and domain != brand and not domain.endswith("." + brand):
                score += 25
                indicators.append(
                    f"Possible brand impersonation: {domain}"
                )
                break

    # 5. Check excessive urgency
    urgency_words = [
        "immediately", "urgent", "now",
        "within 24 hours", "last warning"
    ]

    urgency_count = sum(
        1 for word in urgency_words if word in email_text
    )

    if urgency_count >= 2:
        score += 10
        indicators.append("High-pressure or urgent language detected")

    # Keep score between 0 and 100
    score = min(score, 100)

    if score >= 50:
        result = "High Risk - Possible Phishing"
    elif score >= 20:
        result = "Medium Risk - Suspicious Email"
    else:
        result = "Low Risk - No Obvious Warning Signs"

    if not indicators:
        indicators.append(
            "No obvious phishing indicators detected by the rule-based checks"
        )

    return {
        "status": result,
        "risk_score": score,
        "indicators": indicators,
        "urls_found": urls,
        "method": "Rule-based email analysis"
    }


@email_bp.route("/api/analyze/email", methods=["POST"])
def detect_email():

    try:
        data = request.get_json(silent=True) or {}

        sender = data.get("sender", "")
        subject = data.get("subject", "")
        body = data.get("body", "")

        if not subject.strip() and not body.strip():
            return jsonify({
                "error": "Please enter an email subject or email body"
            }), 400

        result = analyse_email(sender, subject, body)

        return jsonify({
            "success": True,
            "message": "Email analysis completed",
            "analysis": result
        }), 200

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500