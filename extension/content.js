// ============================================================
//  PHISHNOVA AI - GMAIL CONTENT SCRIPT (Final Render Version)
// ============================================================

// 🔁 REPLACE with your actual Render instance URL
const BASE_URL = "https://yoururl-add-here"; 
const API_URL = `${BASE_URL}/analyze`;

/**
 * Injects the PhishNova button into the Gmail toolbar.
 */
function injectButton() {
    // Targets the standard Gmail toolbar areas
    const navContainer = document.querySelector('.amH, .nk, .adC, .G-atb');
    if (!navContainer) return;

    const existingBtn = document.querySelector('.phishguard-btn');
    if (existingBtn) {
        if (existingBtn.parentElement !== navContainer.parentNode) {
            existingBtn.remove();
        } else {
            return;
        }
    }

    const btn = document.createElement('button');
    btn.className = "phishguard-btn";
    btn.innerHTML = `
        <svg style="margin-right: 6px;" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
        </svg>
        <span>Analyze It</span>
    `;

    // Professional Styling
    Object.assign(btn.style, {
        backgroundColor: "#2563eb",
        color: "white",
        border: "none",
        borderRadius: "6px",
        padding: "5px 14px",
        marginRight: "15px",
        cursor: "pointer",
        fontWeight: "600",
        fontSize: "12px",
        fontFamily: "Google Sans, Roboto, sans-serif",
        display: "inline-flex",
        alignItems: "center",
        boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
        zIndex: "9999",
        height: "32px",
        alignSelf: "center",
        transition: "background-color 0.2s"
    });

    btn.onmouseover = () => btn.style.backgroundColor = "#1d4ed8";
    btn.onmouseout = () => btn.style.backgroundColor = "#2563eb";

    navContainer.parentNode.insertBefore(btn, navContainer);
}

/**
 * Extracts the sender's email address using a multi-step fallback strategy.
 */
function getSenderEmail() {
    // 1. Look for the sender element in the currently open email
    const senderElem = document.querySelector('.gD');
    if (senderElem) {
        const emailAttr = senderElem.getAttribute('email');
        if (emailAttr) return emailAttr;

        // Fallback: Use Regex to extract email from text like "Name <email@domain.com>"
        const text = senderElem.innerText;
        const match = text.match(/[^\s<]+@[^\s>]+/);
        return match ? match[0] : text;
    }

    // 2. Fallback: Check for any element with an 'email' attribute in the active view
    const fallbackElem = document.querySelector('[email]');
    return fallbackElem ? fallbackElem.getAttribute('email') : "Unknown Sender";
}

/**
 * Click handler for the PhishNova button.
 */
document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.phishguard-btn');
    if (!btn) return;

    e.preventDefault();
    e.stopPropagation();

    const btnText = btn.querySelector('span');
    const originalText = btnText.innerText;
    
    btnText.innerText = "Analyzing...";
    btn.disabled = true;
    btn.style.opacity = "0.8";

    try {
        const senderEmail = getSenderEmail();
        const emailBody = document.querySelector('.a3s, .adn, .ii.gt');

        if (!emailBody) {
            alert("❌ Analysis Failed: Please make sure the email is fully open and visible.");
            return;
        }

        const payload = {
            content: emailBody.innerText.trim(),
            sender: senderEmail
        };

        // Send to Render Backend
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error("Server communication failed");

        const data = await response.json();
        
        const isPhishing = data.status.toLowerCase().includes('phishing') || 
                           data.status.toLowerCase().includes('threat');
        
        const verdict = isPhishing ? '⚠️ PHISHING DETECTED' : '✅ SECURE';
        
        // Final Pop-up Report
        alert(`🛡️ PHISHNOVA AI REPORT\n\nSender: ${data.sender}\nScore: ${data.score}%\nVerdict: ${verdict}\n\nReason: ${data.explanation}`);

    } catch (error) {
        console.error("PhishNova AI Error:", error);
        alert("❌ Connection Error: PhishNova AI cloud engine unreachable. If this is the first run, the server may be 'waking up'—please try again in 30s.");
    } finally {
        btnText.innerText = originalText;
        btn.disabled = false;
        btn.style.opacity = "1";
    }
});

// Watch for navigation changes in Gmail
const observer = new MutationObserver(injectButton);
observer.observe(document.body, { childList: true, subtree: true });

// Initial injection
injectButton();
setInterval(injectButton, 2000);