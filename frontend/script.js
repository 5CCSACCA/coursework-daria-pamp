async function uploadImage() {
    const fileInput = document.getElementById("fileInput");
    const tokenInput = document.getElementById("tokenInput");
    const statusEl = document.getElementById("status");
    const resultEl = document.getElementById("result");

    statusEl.textContent = "";
    resultEl.textContent = "";

    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please choose an image.");
        return;
    }

    const token = tokenInput.value.trim();
    if (!token) {
        alert("Please paste your Firebase ID token.");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    statusEl.textContent = "Uploading...";

    try {
        const response = await fetch("http://localhost:8080/process-art", {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + token
            },
            body: formData
        });

        let data;
        try { data = await response.json(); } catch {}

        if (!response.ok) {
            statusEl.textContent = "Error: " + (data?.detail || response.statusText);
            return;
        }

        statusEl.textContent = "Status: " + data.status + ". Request ID: " + data.id;

        if (data.message) {
            resultEl.textContent = data.message;
        } else {
            resultEl.textContent = "Your artwork is queued. Check Firestore for result.";
        }

    } catch (err) {
        statusEl.textContent = "Network error: " + err.message;
    }
}
