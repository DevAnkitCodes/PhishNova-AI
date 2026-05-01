import os
import joblib
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# Import custom utilities
from utils.preprocessor import clean_email_for_ml, clean_email_for_gpt
from utils.gpt_logic import get_gpt_explanation

# 1. Load environment variables
load_dotenv()
app = Flask(__name__)

# [RENDER UPDATE] CORS is mandatory for the Chrome extension
CORS(app) 

# 2. Database setup
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "phishnova_secure_key")  # renamed key

# [RENDER UPDATE] Simplified pathing for SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'blacklist.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 3. Database model
class FlaggedEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(150))
    score = db.Column(db.Integer)
    explanation = db.Column(db.Text) 
    status = db.Column(db.String(100))
    confidence = db.Column(db.String(50), default="High")
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# 4. Load ML model
MODEL_PATH = os.path.join(basedir, 'models', 'email_spam.pkl')
model_spam = None

def load_models():
    global model_spam
    try:
        print(f"🔍 Searching for model at: {MODEL_PATH}")
        if os.path.exists(MODEL_PATH):
            model_spam = joblib.load(MODEL_PATH)
            print("✅ ML Model (email_spam.pkl) loaded successfully.")
        else:
            print(f"❌ Model not found. Files in /models: {os.listdir(os.path.join(basedir, 'models')) if os.path.exists(os.path.join(basedir, 'models')) else 'Folder missing'}")
    except Exception as e:
        print(f"❌ Model load error: {e}")

# Initialize database and model loading automatically
with app.app_context():
    db.create_all() 
    load_models()

# 5. Routes

@app.route('/')
def home():
    """Redirects base URL to the Dashboard."""
    return render_template('dashboard.html', logs=FlaggedEmail.query.order_by(FlaggedEmail.timestamp.desc()).limit(50).all())

@app.route('/status')
def status():
    """API Status endpoint for monitoring."""
    return jsonify({
        "status": "PhishNova AI Hybrid Engine Online",
        "xai_engine": "Groq Llama-3",
        "deployment": "Render Cloud"
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    """Main endpoint called by the Chrome extension."""
    if model_spam is None:
        return jsonify({"error": "ML Model not initialized"}), 500

    data = request.json
    raw_content = data.get("content", "")
    sender_id = data.get("sender", "Unknown Sender")

    if not raw_content:
        return jsonify({"error": "No content provided"}), 400

    # ---- Preprocessing ----
    ml_input = clean_email_for_ml(raw_content)
    gpt_input = clean_email_for_gpt(raw_content)

    # ---- ML inference ----
    try:
        prob_spam = model_spam.predict_proba([ml_input])[0][1]
        score = int(prob_spam * 100)
    except Exception as e:
        print(f"ML error: {e}")
        score = 50 

    # ---- Groq AI (Llama-3) explanation ----
    explanation = get_gpt_explanation(gpt_input)

    # ---- Hybrid decision logic ----
    if "appears safe" in explanation.lower():
        status_text = "AI Verified Safe"
        final_score = min(score, 15)
        confidence = "AI Verified"
    elif score > 80:
        status_text = "Phishing Detected (High Match)"
        final_score = score
        confidence = "High"
    else:
        threat_keywords = ["suspicious", "phishing", "malicious", "mismatch", "fake", "unsafe"]
        if any(kw in explanation.lower() for kw in threat_keywords):
            status_text = "AI Verified Threat"
            final_score = max(score, 85)
            confidence = "AI Verified"
        else:
            status_text = "AI Verified Safe"
            final_score = min(score, 15)
            confidence = "AI Verified"

    # Save to Database
    try:
        new_entry = FlaggedEmail(
            sender=sender_id,
            score=final_score,
            explanation=explanation,
            status=status_text,
            confidence=confidence
        )
        db.session.add(new_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")

    return jsonify({
        "sender": sender_id,
        "score": final_score,
        "explanation": explanation,
        "status": status_text,
        "confidence": confidence
    })

@app.route('/dashboard')
def dashboard():
    """Legacy route for the dashboard."""
    db_logs = FlaggedEmail.query.order_by(FlaggedEmail.timestamp.desc()).limit(50).all()
    return render_template('dashboard.html', logs=db_logs)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)