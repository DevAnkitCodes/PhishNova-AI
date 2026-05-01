document.addEventListener('DOMContentLoaded', function() {
    console.log("PhishNova AI Popup Initialized");

    // [RENDER UPDATE] Replace with your actual Render URL
    // Keep the local URL commented out so you can switch back for testing
    const BASE_URL = 'https://yoururl-add-here'; 
    // const BASE_URL = 'http://127.0.0.1:5000';

    // 1. Backend Status Check
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-box span:nth-child(2)');

    // Fetching the root endpoint to check if the Hybrid Engine is online
    fetch(`${BASE_URL}/`)
        .then(response => {
            if (response.ok) {
                statusDot.style.backgroundColor = "#22c55e"; // Green
                statusDot.style.boxShadow = "0 0 8px #22c55e";
                statusText.innerText = "Hybrid Engine: Online";
            } else {
                throw new Error("Server response not OK");
            }
        })
        .catch(error => {
            statusDot.style.backgroundColor = "#ef4444"; // Red
            statusDot.style.boxShadow = "0 0 8px #ef4444";
            statusText.innerText = "Hybrid Engine: Offline";
            console.log("PhishNova AI backend not reachable. Ensure Render service is active!");
        });

    // 2. Dashboard Button Click Handler
    const dashBtn = document.querySelector('.btn-dash');
    if (dashBtn) {
        dashBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Opens your persistent audit logs in a new tab
            chrome.tabs.create({ url: `${BASE_URL}/dashboard` });
        });
    }
});