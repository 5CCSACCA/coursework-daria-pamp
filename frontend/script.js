const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const fileName = document.getElementById("fileName");
const result = document.getElementById("result");
const resultTitle = document.getElementById("resultTitle");
const errorBox = document.getElementById("error");

let lastRequestId = null;   // <— запоминаем ID заявки
let pollingInterval = null; // <— таймер авто-обновления

// ---------------------------------------
// IMAGE PREVIEW
// ---------------------------------------
fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file) return;

    fileName.textContent = "Selected: " + file.name;

    const reader = new FileReader();
    reader.onload = e => {
        preview.src = e.target.result;
        preview.style.display = "block";
    };
    reader.readAsDataURL(file);
});


// ---------------------------------------
// UPLOAD IMAGE
// ---------------------------------------
async function uploadImage() {
    errorBox.textContent = "";
    resultTitle.style.display = "none";
    result.textContent = "";

    const token = document.getElementById("tokenInput").value.trim();
    const file = fileInput.files[0];

    if (!token) {
        errorBox.textContent = "Error: token missing";
        return;
    }
    if (!file) {
        errorBox.textContent = "Error: no image selected";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("http://localhost:8080/process-art", {
            method: "POST",
            headers: { "Authorization": "Bearer " + token },
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            errorBox.textContent = "Error: " + (data.detail || "Upload failed");
            return;
        }

        // save request ID for polling
        lastRequestId = data.id;
        startPollingStatus(token);

        resultTitle.style.display = "block";
        result.innerHTML =
            `Uploaded ✔ Interpretation will appear in Firestore.<br><br>` +
            `Status: ${data.status}<br>` +
            `Request ID: ${data.id}`;

    } catch (err) {
        errorBox.textContent = "Network error: " + err.message;
    }
}


// ---------------------------------------
// AUTO CHECK STATUS IN FIRESTORE
// ---------------------------------------
function startPollingStatus(token) {
    if (!lastRequestId) return;

    // stop previous polling if exists
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }

    pollingInterval = setInterval(() => checkStatus(token), 2000);
}

async function checkStatus(token) {
    if (!lastRequestId) return;

    try {
        const response = await fetch("http://localhost:8080/history", {
            headers: { "Authorization": "Bearer " + token }
        });

        const history = await response.json();
        const item = history.find(h => h.id === lastRequestId);

        if (!item) return;

        // Update status instantly
        result.innerHTML =
            `Uploaded ✔ Interpretation will appear in Firestore.<br><br>` +
            `Status: ${item.status}<br>` +
            `Request ID: ${item.id}<br><br>`;

        // If completed — show meaning + objects
        if (item.status === "completed") {
            clearInterval(pollingInterval);

            result.innerHTML += `<b>Objects:</b> ${item.objects?.join(", ") || "None"}<br><br>`;
            result.innerHTML += `<b>Interpretation:</b><br>${item.interpretation}`;

        }

    } catch (err) {
        console.log("Polling error:", err.message);
    }
}


// ---------------------------------------
// CLEAR FORM
// ---------------------------------------
function clearForm() {
    document.getElementById("tokenInput").value = "";
    fileInput.value = "";
    fileName.textContent = "";
    preview.style.display = "none";
    errorBox.textContent = "";
    result.textContent = "";
    resultTitle.style.display = "none";

    lastRequestId = null;
    if (pollingInterval) clearInterval(pollingInterval);
}
