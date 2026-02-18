/**
 * Groq Gate - Frontend protection script
 * Ensures user has a Groq API key before allowing access to features.
 */

(function () {
    const GROQ_STATUS_URL = "/api/v1/groq/status";
    const GROQ_KEY_URL = "/api/v1/groq/key";

    // For testing/development, we'll use a fixed user ID if not provided
    // In production, this would come from an auth context.
    // Get ID from URL (e.g., ?user=new_user) OR localStorage OR default
    const urlParams = new URLSearchParams(window.location.search);
    const urlUser = urlParams.get("user");

    const USER_ID = urlUser || localStorage.getItem("x_user_id") || "test_user_123";

    // Always update localStorage if we have a new ID
    if (USER_ID) localStorage.setItem("x_user_id", USER_ID);

    console.log("Groq Gate Loaded. Checking status for user:", USER_ID);

    async function checkGroqStatus() {
        try {
            console.log("Fetching Groq status...");
            const response = await fetch(GROQ_STATUS_URL, {
                headers: { "X-User-Id": USER_ID }
            });
            console.log("Groq status response:", response.status);

            if (!response.ok) {
                console.error("Groq status check failed:", response.statusText);
                return;
            }

            const data = await response.json();
            console.log("Groq status data:", data);

            if (!data.has_key) {
                console.log("❌ No key found for user [" + USER_ID + "]. Showing popup...");
                showGroqModal();
            } else {
                console.log("✅ Groq key ALREADY EXISTS for user [" + USER_ID + "]. Popup will NOT show.");
                console.log("ℹ️ To test the popup, change the user in the URL: ?user=brand_new_user");
            }
        } catch (error) {
            console.error("Error checking Groq status:", error);
        }
    }

    function showGroqModal() {
        const modalHtml = `
            <div id="groqModalOverlay" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:9999; display:flex; align-items:center; justify-content:center; backdrop-filter: blur(5px);">
                <div style="background:white; padding:40px; border-radius:16px; width:100%; max-width:500px; box-shadow:0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04); text-align:center;">
                    <h2 style="margin-top:0; color:#111; font-size:24px;">Setup Required</h2>
                    <p style="color:#666; margin-bottom:24px;">To use our document AI features, please provide your Groq API key. This will be securely stored and used only for your requests.</p>
                    
                    <div style="text-align:left; margin-bottom:20px;">
                        <label for="groqKeyInput" style="display:block; font-size:14px; font-weight:600; color:#374151; margin-bottom:8px;">Groq API Key</label>
                        <input type="password" id="groqKeyInput" placeholder="gsk_..." style="width:100%; padding:12px; border:1px solid #d1d5db; border-radius:8px; font-size:16px; box-sizing:border-box; outline:none; transition:border-color 0.2s;" onfocus="this.style.borderColor='#10b981'">
                        <p style="font-size:12px; color:#9ca3af; margin-top:8px;">Keys start with <code style="background:#f3f4f6; padding:2px 4px; border-radius:4px;">gsk_</code>. You can get yours from <a href="https://console.groq.com/keys" target="_blank" style="color:#10b981; text-decoration:none; font-weight:500;">Groq Console</a>.</p>
                    </div>
                    
                    <div id="modalError" style="color:#ef4444; font-size:14px; margin-bottom:16px; display:none;"></div>
                    
                    <button id="saveGroqKeyBtn" style="width:100%; padding:14px; background:#10b981; color:white; border:none; border-radius:8px; font-size:16px; font-weight:600; cursor:pointer; transition:background 0.2s;" onmouseover="this.style.background='#059669'" onmouseout="this.style.background='#10b981'">
                        Verify and Continue
                    </button>
                    
                    <div id="modalLoading" style="display:none; margin-top:16px;">
                        <div style="display:inline-block; width:20px; height:20px; border:3px solid #f3f4f6; border-radius:50%; border-top-color:#10b981; animation:spin 1s linear infinite;"></div>
                        <span style="font-size:14px; color:#666; margin-left:8px;">Verifying key...</span>
                    </div>
                </div>
            </div>
            <style>
                @keyframes spin { to { transform: rotate(360deg); } }
            </style>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const saveBtn = document.getElementById("saveGroqKeyBtn");
        const keyInput = document.getElementById("groqKeyInput");
        const errorDiv = document.getElementById("modalError");
        const loadingDiv = document.getElementById("modalLoading");

        saveBtn.addEventListener("click", async () => {
            const key = keyInput.value.trim();
            if (!key) {
                errorDiv.textContent = "Please enter a key.";
                errorDiv.style.display = "block";
                return;
            }

            errorDiv.style.display = "none";
            loadingDiv.style.display = "block";
            saveBtn.disabled = true;
            saveBtn.style.opacity = "0.7";

            try {
                const response = await fetch(GROQ_KEY_URL, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-User-Id": USER_ID
                    },
                    body: JSON.stringify({ groq_api_key: key })
                });

                const data = await response.json();

                if (response.ok) {
                    document.getElementById("groqModalOverlay").remove();
                    // Optional: Refresh connection status on upload page if needed
                    if (window.checkSheetsConnection) window.checkSheetsConnection();
                } else {
                    errorDiv.textContent = data.detail || "Invalid key. Please try again.";
                    errorDiv.style.display = "block";
                }
            } catch (error) {
                errorDiv.textContent = "Connection error. Please try again.";
                errorDiv.style.display = "block";
            } finally {
                loadingDiv.style.display = "none";
                saveBtn.disabled = false;
                saveBtn.style.opacity = "1";
            }
        });
    }

    // Run check on load
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", checkGroqStatus);
    } else {
        checkGroqStatus();
    }
})();
