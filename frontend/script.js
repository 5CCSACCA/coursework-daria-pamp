const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const fileName = document.getElementById("fileName");
const result = document.getElementById("result");
const resultTitle = document.getElementById("resultTitle");
const errorBox = document.getElementById("error");

// PREVIEW IMAGE
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

// UPLOAD IMAGE
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

    const response = await fetch("http://localhost:8080/upload", {
        method: "POST",
        headers: { "Authorization": token },
        body: formData
    });

    const data = await response.json();

    if (!response.ok) {
        errorBox.textContent = "Error: " + (data.detail || "Upload failed");
        return;
    }

    // Success
    resultTitle.style.display = "block";
    result.textContent = "Uploaded ✔ Waiting for interpretation…";
}

// CLEAR FORM
function clearForm() {
    document.getElementById("tokenInput").value = "";
    fileInput.value = "";
    fileName.textContent = "";
    preview.style.display = "none";
    errorBox.textContent = "";
    result.textContent = "";
    resultTitle.style.display = "none";
}
