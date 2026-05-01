import os
import re
from groq import Groq
from dotenv import load_dotenv

# Load local .env only if it exists (for local development)
load_dotenv()

def clean_groq_response(text):
    """Refined cleaning to ensure UI compatibility and app.py logic safety."""
    # 1. Remove Markdown symbols (important for Chrome Extension UI)
    text = re.sub(r'[*#_~`]', '', text)
    
    # 2. Fix missing space after "Link" (e.g., "Linkhttp://..." -> "Link http://...")
    text = re.sub(r'Link(https?://)', r'Link \1', text, flags=re.IGNORECASE)
    
    # 3. Fix spacing after punctuation (., !, ?) when followed by a letter
    text = re.sub(r'([.!?])(\w)', r'\1 \2', text)
    
    # 4. Standardize whitespace (handles multiple spaces, tabs, newlines)
    text = " ".join(text.split()).strip()
    
    return text

def get_gpt_explanation(email_content, api_key=None, is_deep_scan=False):
    # [RENDER UPDATE] Prioritize system environment variables for cloud deployment
    final_key = api_key or os.environ.get("GROQ_API_KEY")

    if not final_key:
        return "⚠️ AI analysis unavailable: API key not configured on server."

    try:
        client = Groq(api_key=final_key)

        # System prompt aligned with your app.py hybrid logic
        system_prompt = (
            "You are a professional Cybersecurity Analyst. Analyze email text for phishing. "
            "Follow these STRICT RULES:\n"
            "1. If no typos and no suspicious links are found, output exactly: 'No suspicious URLs or spelling errors found – appears safe.'\n"
            "2. If there are spelling mistakes, list them and say they indicate a phishing attempt.\n"
            "3. If there is a URL, check if it matches the context. If it looks fake (e.g., paypa1.com), say: 'Link [URL] is suspicious – domain mismatch.'\n"
            "4. Keep the answer under 20 words. No bolding. No extra text."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this email: {email_content[:800]}"},
            ],
            # Ensure this model matches your current Groq plan availability
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=150,
        )

        raw_text = chat_completion.choices[0].message.content.strip()
        
        # Apply the refined cleaning
        cleaned = clean_groq_response(raw_text)
        
        # [EXTENSION SAFETY] Prevent the popup from breaking if text is too long
        if len(cleaned) > 150:
            cleaned = cleaned[:147] + "..."

        return cleaned if cleaned else "Analysis: Content verified."

    except Exception as e:
        # Log the error for Render logs
        print(f"Groq API Error: {e}")
        return "🔍 AI analysis offline. Using ML score only."