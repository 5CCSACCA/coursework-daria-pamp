async function uploadImage() {
    const fileInput = document.getElementById("fileInput");
    const tokenInput = document.getElementById("tokenInput");
    const statusEl = document.getElementById("status");
    const resultEl = document.getElementById("result");
    const resultTitle = document.getElementById("resultTitle");

    // Reset UI
    statusEl.textContent = "";
    statusEl.className = "status";
    resultEl.textContent = "";
    resultTitle.style.display = "none";

    // Show loading indicator
    document.getElementById("loading").style.display = "block";

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

        let data = null;
        try { data = await response.json(); } catch {}

        if (!response.ok) {
            statusEl.textContent = "Error: " + (data?.detail || response.statusText);
            statusEl.classList.add("error");
            document.getElementById("loading").style.display = "none";
            return;
        }

        // SUCCESS
        statusEl.textContent = "Status: " + data.status + ". Request ID: " + data.id;
        statusEl.classList.add("success");

        resultTitle.style.display = "block";

        if (data.message) {
            resultEl.textContent = data.message;
        } else {
            resultEl.textContent = "Your artwork is queued. Check Firestore for the final result.";
        }

    } catch (err) {
        statusEl.textContent = "Network error: " + err.message;
        statusEl.classList.add("error");
    }

    // Always hide loading indicator
    document.getElementById("loading").style.display = "none";
}


// =======================
// IMAGE PREVIEW + FILENAME
// =======================

document.getElementById("fileInput").addEventListener("change", function () {
    const preview = document.getElementById("preview");
    const fileNameEl = document.getElementById("fileName");
    const file = this.files[0];

    if (!file) {
        preview.style.display = "none";
        fileNameEl.textContent = "";
        return;
    }

    fileNameEl.textContent = "Selected: " + file.name;

    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.style.display = "block";
    };
    reader.readAsDataURL(file);
});


// =======================
// CLEAR FORM (student-level realistic)
// =======================


function clearForm() {
    document.getElementById("tokenInput").value = "";
    document.getElementById("fileInput").value = "";
    document.getElementById("fileName").textContent = "";
    document.getElementById("preview").style.display = "none";

    document.getElementById("status").textContent = "";
    document.getElementById("result").textContent = "";
    document.getElementById("loading").style.display = "none";
}



