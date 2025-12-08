async function uploadImage() {
    const fileInput = document.getElementById("fileInput");
    const tokenInput = document.getElementById("tokenInput");
    const statusEl = document.getElementById("status");
    const resultEl = document.getElementById("result");

    statusEl.textContent = "";
    resultEl.textContent = "";

    // 1) Проверка файла
    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please choose an image file first.");
        return;
    }

    // 2) Проверка токена
    const token = tokenInput.value.trim();
    if (!token) {
        alert("Please paste your Firebase ID token.");
        return;
    }

    const file = fileInput.files[0];

    const formData = new FormData();
    formData.append("file", file);

    statusEl.textContent = "Uploading image to ArtiFy...";
    try {
        const response = await fetch("http://localhost:8080/process-art", {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + token
                // НЕ указываем Content-Type вручную, FormData сделает это сама
            },
            body: formData
        });

        let data;
        try {
            data = await response.json();
        } catch (e) {
            data = null;
        }

        if (!response.ok) {
            statusEl.textContent = "Error: " + (data?.detail || response.statusText);
            console.error("Response error:", data);
            return;
        }

        // У нас API возвращает: { id, status, message }
        statusEl.textContent = `Status: ${data.status}. Request ID: ${data.id}`;
        if (data.message) {
            resultEl.textContent = data.message;
        } else {
            resultEl.textContent = "Your artwork is queued. Check Firestore for the final interpretation.";
        }
    } catch (err) {
        console.error(err);
        statusEl.textContent = "Network error: " + err.message;
    }
}
