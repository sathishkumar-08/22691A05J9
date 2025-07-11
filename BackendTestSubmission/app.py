from flask import Flask, request, jsonify, redirect
from datetime import datetime, timedelta
import string, random, json, os
from LoggingMiddleware.middleware import log

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'urls_db.json')

def load_data():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def generate_shortcode(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route("/shorturls", methods=["POST"])
def create_short_url():
    data = request.get_json()

    url = data.get("url")
    validity = data.get("validity", 30)
    custom_code = data.get("shortcode")

    if not url:
        log("backend", "error", "create_short_url", "Missing URL in request")
        return jsonify({"error": "URL is required"}), 400

    if not isinstance(validity, int):
        log("backend", "error", "create_short_url", "Invalid validity input")
        return jsonify({"error": "Validity must be an integer"}), 400

    db = load_data()

    if custom_code:
        if custom_code in db:
            log("backend", "error", "create_short_url", "Custom shortcode already exists")
            return jsonify({"error": "Shortcode already exists"}), 409
        shortcode = custom_code
    else:
        shortcode = generate_shortcode()
        while shortcode in db:
            shortcode = generate_shortcode()

    expiry_time = datetime.utcnow() + timedelta(minutes=validity)

    db[shortcode] = {
        "url": url,
        "created_at": datetime.utcnow().isoformat(),
        "expiry": expiry_time.isoformat(),
        "clicks": []
    }

    save_data(db)

    log("backend", "info", "create_short_url", f"Short URL created: {shortcode}")

    return jsonify({
        "shortLink": f"http://127.0.0.1:5000/{shortcode}",
        "expiry": expiry_time.isoformat() + "Z"
    }), 201

@app.route("/<shortcode>", methods=["GET"])
def redirect_to_url(shortcode):
    db = load_data()

    if shortcode not in db:
        log("backend", "error", "redirect", "Shortcode not found")
        return jsonify({"error": "Shortcode not found"}), 404

    url_data = db[shortcode]
    expiry = datetime.fromisoformat(url_data["expiry"])

    if datetime.utcnow() > expiry:
        log("backend", "warning", "redirect", "Shortcode expired")
        return jsonify({"error": "Shortcode expired"}), 410

    click_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "referrer": request.referrer,
        "location": request.remote_addr  # simple IP address, no geo lookup
    }

    url_data["clicks"].append(click_info)
    save_data(db)

    log("backend", "info", "redirect", f"Redirected to {url_data['url']}")

    return redirect(url_data["url"], code=302)

@app.route("/shorturls/<shortcode>", methods=["GET"])
def get_statistics(shortcode):
    db = load_data()

    if shortcode not in db:
        log("backend", "error", "stats", "Shortcode not found for stats")
        return jsonify({"error": "Shortcode not found"}), 404

    data = db[shortcode]

    stats = {
        "original_url": data["url"],
        "created_at": data["created_at"],
        "expiry": data["expiry"],
        "total_clicks": len(data["clicks"]),
        "click_details": data["clicks"]
    }

    log("backend", "info", "stats", f"Stats retrieved for {shortcode}")
    return jsonify(stats), 200

if __name__ == "__main__":
    app.run(debug=True)
