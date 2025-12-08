async function uploadImage() {
    const file = document.getElementById("fileInput").files[0];
    if (!file) {
        alert("Please select an image first.");
        return;
    }

    document.getElementById("status").innerText = "Uploading...";
    document.getElementById("result").innerText = "";

    // 1️⃣ Firebase — get ID token
    const user = await firebase.auth().signInWithEmailAndPassword(
        "testuser@gmail.com",
        "123456"
    );
    const idToken = await user.user.getIdToken();

    // 2️⃣ Prepare multipart data
    const formData = new FormData();
    formData.append("file", file);

    // 3️⃣ Send request to API Gateway
    const response = await fetch("http://localhost:8080/process-art", {
        method: "POST",
        headers: {
            "Authorization": "Bearer " + idToken
        },
        body: formData
    });

    const json = await response.json();

    document.getElementById("status").innerText =
        "Image uploaded. Processing...";

    pollResult(json.id); // start polling
}

async function pollResult(id) {
    document.getElementById("status").innerText =
        "Waiting for processing...";

    const interval = setInterval(async () => {
        const res = await fetch(`http://localhost:8080/result/${id}`);
        const data = await res.json();

        if (data.status === "completed") {
            clearInterval(interval);

            document.getElementById("status").innerText = "Done!";
            document.getElementById("result").innerText =
                "Objects: " + data.objects.join(", ") +
                "\n\nInterpretation:\n" + data.interpretation;
        }
    }, 2000);
}
