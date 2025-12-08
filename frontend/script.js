async function uploadImage() {
    const fileInput = document.getElementById("fileInput");
    const tokenInput = document.getElementById("tokenInput");
    const statusEl = document.getElementById("status");
    const resultEl = document.getElementById("result");

    // Show loading indicator
    document.getElementById("loading").style.display = "block";

    statusEl.textContent = "";
    resultEl.textContent = "";

    // Validate file
    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please choose an image.");
        document.getElementById("loading").style.display = "none";
        return;
    }

    // Validate token
    const token = tokenInput.value.trim();
    if (!token) {
        alert("Please paste your Firebase ID token.");
        document.getElementById("loading").style.display = "none";
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
            document.getElementById("loading").style.display = "none";
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

    // ALWAYS hide loading indicator at the end
    document.getElementById("loading").style.display = "none";
}


// Preview the selected image
document.getElementById("fileInput").addEventListener("change", function () {
    const preview = document.getElementById("preview");
    const file = this.files[0];

    if (!file) {
        preview.style.display = "none";
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.style.display = "block";
    };
    reader.readAsDataURL(file);
});


