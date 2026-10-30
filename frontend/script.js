
// =========================================
// DEEP-FAKE GUARD - API CONFIGURATION
// =========================================

const API_BASE_URL = "http://localhost:5000/api";


// =========================================
// PAGE INITIALIZATION
// =========================================

document.addEventListener("DOMContentLoaded", () => {

    // Highlight active navigation
    const currentPath = window.location.pathname.split("/").pop();

    document.querySelectorAll("nav a").forEach(link => {

        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        }

    });


    // IMAGE AND VIDEO DETECTION
    const dropzone = document.getElementById("dropzone");

    const fileInput = document.getElementById("fileInput");

    if (dropzone && fileInput) {

        dropzone.addEventListener("click", () => {
            fileInput.click();
        });


        dropzone.addEventListener("dragover", (event) => {

            event.preventDefault();

            dropzone.style.borderColor = "#10b981";

        });


        dropzone.addEventListener("dragleave", () => {

            dropzone.style.borderColor = "#475569";

        });


        dropzone.addEventListener("drop", (event) => {

            event.preventDefault();

            dropzone.style.borderColor = "#475569";

            if (event.dataTransfer.files.length > 0) {

                fileInput.files = event.dataTransfer.files;

                handleFileSelection(fileInput.files[0]);

            }

        });


        fileInput.addEventListener("change", () => {

            if (fileInput.files.length > 0) {

                handleFileSelection(fileInput.files[0]);

            }

        });


        const analyzeBtn = document.getElementById("analyzeBtn");

        if (analyzeBtn) {

            analyzeBtn.addEventListener(
                "click",
                submitMediaForAnalysis
            );

        }

    }


    // HISTORY PAGE
    const historyTableBody = document.getElementById(
        "historyTableBody"
    );

    if (historyTableBody) {
        fetchHistoryRecords();
    }


    // AUDIO DETECTION
    setupAudioDetection();


    // EMAIL DETECTION
    setupEmailDetection();

});


// =========================================
// IMAGE AND VIDEO PREVIEW
// =========================================

function handleFileSelection(file) {

    const previewContainer = document.getElementById(
        "previewContainer"
    );

    if (!previewContainer) return;

    previewContainer.innerHTML = "";

    const reader = new FileReader();

    if (file.type.startsWith("image/")) {

        reader.onload = (event) => {

            previewContainer.innerHTML = `
                <img
                    src="${event.target.result}"
                    alt="Uploaded Preview"
                >
            `;

        };

        reader.readAsDataURL(file);

    }

    else if (file.type.startsWith("video/")) {

        const videoURL = URL.createObjectURL(file);

        previewContainer.innerHTML = `
            <video
                controls
                src="${videoURL}">
            </video>
        `;

    }

}


// =========================================
// IMAGE AND VIDEO ANALYSIS
// =========================================

async function submitMediaForAnalysis() {

    const fileInput = document.getElementById("fileInput");

    const resultsCard = document.getElementById("resultsCard");

    const analyzeBtn = document.getElementById("analyzeBtn");


    if (!fileInput || !fileInput.files.length) {

        alert("Please select an image or video first.");

        return;

    }


    const formData = new FormData();

    formData.append("file", fileInput.files[0]);


    analyzeBtn.disabled = true;

    analyzeBtn.innerHTML = `
        <span class="spinner"></span>
        Analyzing...
    `;

    if (resultsCard) {
        resultsCard.style.display = "none";
    }


    try {

        const response = await fetch(
            `${API_BASE_URL}/analyze`,
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();


        if (!response.ok || !data.success) {

            throw new Error(data.error || "Analysis failed.");

        }


        // Filename
        document.getElementById("resFilename").textContent =
            data.filename;


        // Prediction
        const badge = document.getElementById("resPrediction");

        badge.textContent = data.prediction.toUpperCase();

        badge.className =
            data.prediction.toLowerCase() === "real"
                ? "badge-real"
                : "badge-fake";


        // Confidence
        document.getElementById("resConfidence").textContent =
            `${data.confidence}%`;


        // Hash
        const hashElement = document.getElementById("resHash");

        if (hashElement) {
            hashElement.textContent = data.sha256 || data.hash || "N/A";
        }


        // Processing time
        const timeElement = document.getElementById("resTime");

        if (timeElement) {
            timeElement.textContent =
                `${data.latency ?? data.processing_time ?? "N/A"} seconds`;
        }


        resultsCard.style.display = "block";

    }

    catch (error) {

        alert("Error: " + error.message);

    }

    finally {

        analyzeBtn.disabled = false;

        analyzeBtn.textContent = "Run AI Analysis";

    }

}


// =========================================
// AUDIO DEEPFAKE DETECTION
// =========================================

function setupAudioDetection() {

    const audioForm = document.getElementById("audioForm");

    if (!audioForm) return;


    const audioFile = document.getElementById("audioFile");

    const audioFileName = document.getElementById("audioFileName");

    const audioPreview = document.getElementById("audioPreview");


    // File selection
    audioFile.addEventListener("change", () => {

        const file = audioFile.files[0];

        if (!file) {

            audioFileName.textContent = "No audio file selected";

            audioPreview.hidden = true;

            return;

        }


        audioFileName.textContent = file.name;


        // Preview audio
        const audioURL = URL.createObjectURL(file);

        audioPreview.src = audioURL;

        audioPreview.hidden = false;

    });


    // Audio form submission
    audioForm.addEventListener("submit", async (event) => {

        event.preventDefault();


        if (!audioFile.files.length) {

            alert("Please select an audio recording.");

            return;

        }


        const button = document.getElementById("audioAnalyzeBtn");

        const results = document.getElementById("audioResults");


        const formData = new FormData();

        formData.append("file", audioFile.files[0]);


        button.disabled = true;

        button.textContent = "Analyzing Audio...";

        results.style.display = "none";


        try {

            const response = await fetch(
                `${API_BASE_URL}/analyze/audio`,
                {
                    method: "POST",
                    body: formData
                }
            );


            const data = await response.json();


            if (!response.ok || !data.success) {

                throw new Error(
                    data.error || "Audio analysis failed."
                );

            }


            // Filename
            document.getElementById(
                "audioResultFilename"
            ).textContent = data.filename;


            // Prediction
            const prediction = document.getElementById(
                "audioPrediction"
            );

            prediction.textContent = data.prediction;

            prediction.className =
                data.prediction.toLowerCase() === "real"
                    ? "audio-prediction-real"
                    : "audio-prediction-fake";


            // Confidence
            document.getElementById(
                "audioConfidence"
            ).textContent = data.confidence;


            // Message
            document.getElementById(
                "audioMessage"
            ).textContent = data.message;


            results.style.display = "block";

        }

        catch (error) {

            alert("Audio Error: " + error.message);

        }

        finally {

            button.disabled = false;

            button.textContent = "Analyze Audio";

        }

    });

}


// =========================================
// EMAIL FRAUD DETECTION
// =========================================

function setupEmailDetection() {

    const emailForm = document.getElementById("emailForm");

    if (!emailForm) return;


    emailForm.addEventListener("submit", async (event) => {

        event.preventDefault();


        const sender = document.getElementById(
            "emailSender"
        ).value.trim();


        const subject = document.getElementById(
            "emailSubject"
        ).value.trim();


        const body = document.getElementById(
            "emailBody"
        ).value.trim();


        const button = document.getElementById(
            "emailAnalyzeBtn"
        );


        const results = document.getElementById(
            "emailResults"
        );


        button.disabled = true;

        button.textContent = "Analyzing Email...";

        results.style.display = "none";


        try {

            const response = await fetch(
                `${API_BASE_URL}/analyze/email`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        sender: sender,
                        subject: subject,
                        body: body
                    })

                }
            );


            const data = await response.json();


            if (!response.ok || !data.success) {

                throw new Error(
                    data.error || "Email analysis failed."
                );

            }


            const analysis = data.analysis;


            // Status
            const status = document.getElementById(
                "emailStatus"
            );

            status.textContent = analysis.status;


            status.className = "";

            if (analysis.status === "High Risk") {

                status.classList.add("email-high-risk");

            }

            else if (analysis.status === "Medium Risk") {

                status.classList.add("email-medium-risk");

            }

            else {

                status.classList.add("email-low-risk");

            }


            // Risk score
            document.getElementById(
                "emailRiskScore"
            ).textContent = analysis.risk_score;


            // Indicators
            const indicatorList = document.getElementById(
                "emailIndicators"
            );

            indicatorList.innerHTML = "";


            if (analysis.indicators.length > 0) {

                analysis.indicators.forEach(indicator => {

                    const li = document.createElement("li");

                    li.textContent = indicator;

                    indicatorList.appendChild(li);

                });

            }

            else {

                const li = document.createElement("li");

                li.textContent = "No suspicious indicators detected.";

                indicatorList.appendChild(li);

            }


            // URLs
            const urlList = document.getElementById(
                "emailUrls"
            );

            urlList.innerHTML = "";


            if (analysis.urls_found && analysis.urls_found.length > 0) {

                analysis.urls_found.forEach(url => {

                    const li = document.createElement("li");

                    li.textContent = url;

                    urlList.appendChild(li);

                });

            }

            else {

                const li = document.createElement("li");

                li.textContent = "No URLs found.";

                urlList.appendChild(li);

            }


            results.style.display = "block";

        }

        catch (error) {

            alert("Email Error: " + error.message);

        }

        finally {

            button.disabled = false;

            button.textContent = "Analyze Email";

        }

    });

}


// =========================================
// HISTORY PAGE
// =========================================

async function fetchHistoryRecords() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/history`
        );


        if (!response.ok) {

            throw new Error("Unable to fetch history.");

        }


        const records = await response.json();


        const tbody = document.getElementById(
            "historyTableBody"
        );

        tbody.innerHTML = "";


        if (records.length === 0) {

            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align:center;">
                        No analysis history recorded yet.
                    </td>
                </tr>
            `;

            return;

        }


        records.forEach(record => {

            const badgeClass =
                record.prediction.toLowerCase() === "real"
                    ? "badge-real"
                    : "badge-fake";


            const tr = document.createElement("tr");


            // Create cells safely
            const values = [
                record.timestamp,
                record.filename,
                record.prediction,
                `${record.confidence}%`,
                (record.sha256 || "").substring(0, 16) + "...",
                `${record.latency ?? record.processing_time ?? "N/A"}s`
            ];


            values.forEach((value, index) => {

                const td = document.createElement("td");

                td.textContent = value;


                if (index === 2) {

                    const badge = document.createElement("span");

                    badge.className = badgeClass;

                    badge.textContent = value;

                    td.textContent = "";

                    td.appendChild(badge);

                }


                tr.appendChild(td);

            });


            tbody.appendChild(tr);

        });

    }

    catch (error) {

        console.error("Failed to load history:", error);

    }

}
