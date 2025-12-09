// ---------------- FIREBASE INIT ----------------
const firebaseConfig = {
    apiKey: "AIzaSyCtZxDlIL2QfpU5X4Ib_7QfaBK4bTlKvls",
    authDomain: "arti-1b395.firebaseapp.com",
    projectId: "arti-1b395",
    storageBucket: "arti-1b395.firebasestorage.app",
    messagingSenderId: "820964903806",
    appId: "1:820964903806:web:231f55b979ee4a47d8812f"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// ---------------- LOGIN ----------------
async function login() {
    const email = document.getElementById("emailInput").value;
    const password = document.getElementById("passwordInput").value;
    const loginStatus = document.getElementById("loginStatus");

    loginStatus.textContent = "";

    try {
        const userCredential = await auth.signInWithEmailAndPassword(email, password);
        const idToken = await userCredential.user.getIdToken();

        document.getElementById("tokenInput").value = idToken;
        loginStatus.style.color = "green";
        loginStatus.textContent = "Logged in successfully!";
    } catch (err) {
        loginStatus.style.color = "red";
        loginStatus.textContent = "Login failed: " + err.message;
    }
}


// ---------------- UI ELEMENTS ----------------
const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const fileName = document.getElementById("fileName");
const result = document.getElementById("result");
const resultTitle = document.getElementById("resultTitle");
const errorBox = document.getElementById("error");

let lastRequestId = null;
let pollingInterval = null;


// ---------------- IMAGE PREVIEW ----------------
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


// ---------------- UPLOAD IMAGE ----------------
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


// ---------------- POLLING FIRESTORE ----------------
function startPollingStatus(token) {
    if (!lastRequestId) return;

    if (pollingInterval) clearInterval(pollingInterval);

    pollingInterval = setInterval(() => checkStatus(token), 2000);
}

async function checkStatus(token) {
    try {
        const response = await fetch("http://localhost:8080/history", {
            headers: { "Authorization": "Bearer " + token }
        });

        const history = await response.json();
        const item = history.find(h => h.id === lastRequestId);

        if (!item) return;

        result.innerHTML =
            `Uploaded ✔ Interpretation will appear in Firestore.<br><br>` +
            `Status: ${item.status}<br>` +
            `Request ID: ${item.id}<br><br>`;

        if (item.status === "completed") {
            clearInterval(pollingInterval);

            result.innerHTML += `<b>Objects:</b> ${item.objects?.join(", ") || "None"}<br><br>`;
            result.innerHTML += `<b>Interpretation:</b><br>${item.interpretation}`;
        }

    } catch (err) {
        console.log("Polling error:", err.message);
    }
}


// ---------------- CLEAR FORM ----------------
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
