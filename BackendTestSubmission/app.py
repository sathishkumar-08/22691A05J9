# app.py
from flask import Flask, request, redirect, jsonify, abort
import sqlite3
import random
import string
import datetime
from urllib.parse import urlparse
import json

# --- START FIX ---
# Import sys and os to manipulate the Python path
import sys
import os

# Get the directory of the current file (app.py)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (22691A05J9_CSE)
parent_dir = os.path.join(current_dir, '..')
# Get the path to the LoggingMiddleware directory
logging_middleware_dir = os.path.join(parent_dir, 'LoggingMiddleware')

# Add the LoggingMiddleware directory to the Python path
sys.path.append(logging_middleware_dir)

# Now, import the 'middleware' module
from middleware import log_event

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # This allows access to columns by name
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                shortcode TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shortcode TEXT NOT NULL,
                clicked_at TEXT NOT NULL,
                referrer TEXT,
                ip_address TEXT,
                FOREIGN KEY (shortcode) REFERENCES urls(shortcode)
            )
        ''')
        conn.commit()
    log_event("backend", "info", "db", "Database initialized successfully.")

# Function to generate a unique shortcode
def generate_unique_shortcode(length=6):
    characters = string.ascii_letters + string.digits # A-Z, a-z, 0-9
    while True:
        shortcode = ''.join(random.choice(characters) for i in range(length))
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM urls WHERE shortcode = ?", (shortcode,))
            if not cursor.fetchone():
                return shortcode
        # If collision, try a slightly longer code or retry (basic retry logic)
        length += 1
        log_event("backend", "warn", "handler", f"Shortcode collision detected, trying longer code: {shortcode}")

# --- API Endpoints ---

@app.route('/shorturls', methods=['POST'])
def create_short_url():
    """
    Creates a new shortened URL.
    Request Body: { "url": "...", "validity": N (optional), "shortcode": "xyz" (optional) }
    """
    log_event("backend", "info", "controller", "Received request to create short URL.")

    data = request.get_json()
    if not data or 'url' not in data:
        log_event("backend", "error", "handler", "Invalid request: URL is missing in request body.")
        abort(400, description="URL is required.")

    original_url = data['url']
    if not urlparse(original_url).scheme: # Check if URL has a scheme (http/https)
        original_url = "http://" + original_url # Prepend http:// if missing (basic fix)
        log_event("backend", "warn", "handler", f"URL missing scheme, prepending http://: {original_url}")
    if not (urlparse(original_url).netloc and urlparse(original_url).scheme in ['http', 'https']):
        log_event("backend", "error", "handler", f"Invalid URL format: {original_url}")
        abort(400, description="Invalid URL format.")

    custom_shortcode = data.get('shortcode')
    validity = data.get('validity', DEFAULT_VALIDITY_MINUTES)

    if not isinstance(validity, int) or validity <= 0:
        log_event("backend", "error", "handler", f"Invalid validity provided: {validity}")
        abort(400, description="Validity must be a positive integer.")

    generated_shortcode = None
    if custom_shortcode:
        # Validate custom shortcode format (alphanumeric, reasonable length)
        if not custom_shortcode.isalnum() or not (3 <= len(custom_shortcode) <= 15):
            log_event("backend", "error", "handler", f"Invalid custom shortcode format: {custom_shortcode}")
            abort(400, description="Custom shortcode must be alphanumeric and between 3-15 characters.")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO urls (original_url, shortcode, created_at, expires_at) VALUES (?, ?, ?, ?)",
                               (original_url, custom_shortcode,
                                datetime.datetime.now().isoformat(),
                                (datetime.datetime.now() + datetime.timedelta(minutes=validity)).isoformat()))
                conn.commit()
                generated_shortcode = custom_shortcode
                log_event("backend", "info", "db", f"Custom shortcode '{custom_shortcode}' inserted.")
            except sqlite3.IntegrityError:
                # Shortcode collision
                log_event("backend", "warn", "db", f"Custom shortcode collision for: {custom_shortcode}. Generating new one.")
                # Fall through to generate a unique one if custom one fails
    
    if generated_shortcode is None: # Either no custom shortcode or custom one failed
        generated_shortcode = generate_unique_shortcode()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO urls (original_url, shortcode, created_at, expires_at) VALUES (?, ?, ?, ?)",
                           (original_url, generated_shortcode,
                            datetime.datetime.now().isoformat(),
                            (datetime.datetime.now() + datetime.timedelta(minutes=validity)).isoformat()))
            conn.commit()
            log_event("backend", "info", "db", f"Generated unique shortcode '{generated_shortcode}' and inserted.")

    short_link = f"http://{request.host}/{generated_shortcode}"
    expiry_time = (datetime.datetime.now() + datetime.timedelta(minutes=validity)).isoformat(timespec='seconds') + 'Z'

    log_event("backend", "info", "api", f"Short URL created: {short_link}")
    return jsonify({
        "shortLink": short_link,
        "expiry": expiry_time
    }), 201


@app.route('/<shortcode>', methods=['GET'])
def redirect_to_original_url(shortcode):
    """
    Redirects to the original URL and logs click statistics.
    """
    log_event("backend", "info", "controller", f"Redirect request for shortcode: {shortcode}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT original_url, expires_at FROM urls WHERE shortcode = ?", (shortcode,))
        url_data = cursor.fetchone()

        if not url_data:
            log_event("backend", "error", "handler", f"Shortcode not found: {shortcode}")
            abort(404, description="Short link not found.")

        expires_at_str = url_data['expires_at']
        expires_at = datetime.datetime.fromisoformat(expires_at_str)

        if datetime.datetime.now() > expires_at:
            log_event("backend", "warn", "handler", f"Expired short link accessed: {shortcode}")
            abort(410, description="Short link has expired.") # 410 Gone

        original_url = url_data['original_url']

        # Log click statistics
        clicked_at = datetime.datetime.now().isoformat()
        referrer = request.referrer # May be None
        ip_address = request.remote_addr # Get client IP

        cursor.execute("INSERT INTO clicks (shortcode, clicked_at, referrer, ip_address) VALUES (?, ?, ?, ?)",
                       (shortcode, clicked_at, referrer, ip_address))
        conn.commit()
        log_event("backend", "info", "db", f"Click recorded for shortcode: {shortcode}")

        log_event("backend", "info", "route", f"Redirecting '{shortcode}' to '{original_url}'")
        return redirect(original_url, code=302) # 302 Found for temporary redirect


@app.route('/shorturls/<shortcode>', methods=['GET'])
def get_short_url_stats(shortcode):
    """
    Retrieves usage statistics for a specific shortened URL.
    """
    log_event("backend", "info", "controller", f"Request for short URL statistics: {shortcode}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT original_url, created_at, expires_at FROM urls WHERE shortcode = ?", (shortcode,))
        url_data = cursor.fetchone()

        if not url_data:
            log_event("backend", "error", "handler", f"Statistics requested for non-existent shortcode: {shortcode}")
            abort(404, description="Short link not found.")

        # Get total clicks
        cursor.execute("SELECT COUNT(*) FROM clicks WHERE shortcode = ?", (shortcode,))
        total_clicks = cursor.fetchone()[0]

        # Get detailed click data
        cursor.execute("SELECT clicked_at, referrer, ip_address FROM clicks WHERE shortcode = ?", (shortcode,))
        detailed_clicks = []
        for row in cursor.fetchall():
            # For "coarse-grained geographical location", we'll just return the IP for this example.
            # A real implementation might use an IP-to-Geo service here.
            detailed_clicks.append({
                "timestamp": row['clicked_at'],
                "referrer": row['referrer'],
                "ip_address": row['ip_address'] # Represents coarse-grained location
            })
        log_event("backend", "info", "db", f"Retrieved click data for shortcode: {shortcode}")

    stats = {
        "shortcode": shortcode,
        "originalUrl": url_data['original_url'],
        "createdAt": url_data['created_at'],
        "expiresAt": url_data['expires_at'],
        "totalClicks": total_clicks,
        "clickData": detailed_clicks
    }
    log_event("backend", "info", "api", f"Returning statistics for shortcode: {shortcode}")
    return jsonify(stats)

@app.errorhandler(400)
def bad_request(error):
    log_event("backend", "error", "handler", f"Bad Request: {error.description}")
    return jsonify({"error": error.description}), 400

@app.errorhandler(404)
def not_found(error):
    log_event("backend", "error", "handler", f"Not Found: {error.description}")
    return jsonify({"error": error.description}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    log_event("backend", "error", "handler", f"Method Not Allowed: {request.method} on {request.path}")
    return jsonify({"error": "Method Not Allowed"}), 405

@app.errorhandler(410)
def gone(error):
    log_event("backend", "error", "handler", f"Resource Gone: {error.description}")
    return jsonify({"error": error.description}), 410

@app.errorhandler(500)
def internal_server_error(error):
    log_event("backend", "fatal", "service", f"Internal Server Error: {str(error)}")
    return jsonify({"error": "Internal Server Error"}), 500


if __name__ == '__main__':
    init_db() # Initialize the database when the app starts
    log_event("backend", "info", "service", "URL Shortener Microservice starting.")
    app.run(debug=True, port=8000) # Run on port 8000 (or any available port)

