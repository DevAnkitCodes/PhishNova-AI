import re

def clean_email_for_ml(text):
    """
    Minimal cleaning for the ML model.
    Only normalizes whitespace – no truncation (preserves full email).
    """
    if not text or not isinstance(text, str):
        return ""
    # Remove excessive whitespace but keep the original length
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_email_for_gpt(text, max_length=800):
    """
    Cleaning for Gemini/GPT.
    Normalizes whitespace and truncates to avoid token limits.
    """
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_length]

# Backward‑compatible alias (if your existing code calls `clean_email`)
def clean_email(text):
    """Legacy function – uses GPT cleaning (truncates)."""
    return clean_email_for_gpt(text)

# Quick test
if __name__ == "__main__":
    sample = "Subject: Urgent! Please verify your account at http://paypa1-secure.com"
    print(f"ML cleaned (full): {clean_email_for_ml(sample)}")
    print(f"GPT cleaned (truncated): {clean_email_for_gpt(sample)}")