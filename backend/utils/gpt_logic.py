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
        return "[VERDICT: THREAT] AI analysis unavailable: API key not configured on server."

    try:
        client = Groq(api_key=final_key)

        # UPDATED: Zero-Shot Deterministic System Prompt
        system_prompt = (
            "You are a Senior Cybersecurity Analyst. Analyze email text for phishing, social engineering, and scams. "
            "Follow these STRICT RULES:\n"
            "1. You MUST start your response with exactly one of these two tags: [VERDICT: SAFE] or [VERDICT: THREAT].\n"
            "2. Evaluate for sophisticated scams (e.g., fake investments, VIP impersonation, urgent credential requests) even if grammar is perfect.\n"
            "3. After the tag, provide a concise explanation (under 25 words).\n"
            "4. Do not use bolding or markdown."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this email: {email_content[:800]}"},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1, # Keep temperature low for deterministic formatting
            max_tokens=150,
        )

        raw_text = chat_completion.choices[0].message.content.strip()
        
        # Apply the refined cleaning
        cleaned = clean_groq_response(raw_text)
        
        # [EXTENSION SAFETY] Prevent the popup from breaking if text is too long
        if len(cleaned) > 150:
            cleaned = cleaned[:147] + "..."

        return cleaned if cleaned else "[VERDICT: SAFE] Analysis: Content verified."

    except Exception as e:
        # Log the error for Render logs
        print(f"Groq API Error: {e}")
        return "[VERDICT: THREAT] AI analysis offline. Treat with caution."
