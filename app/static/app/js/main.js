function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        return parts.pop().split(";").shift();
    }
    return "";
}

document.addEventListener("DOMContentLoaded", () => {
    const patientId = document.body.dataset.patientId;
    if (!patientId) {
        return;
    }

    const summaryBtn = document.getElementById("summaryBtn");
    const summaryOutput = document.getElementById("summaryOutput");
    const loadSummary = async () => {
        if (!summaryOutput) {
            return;
        }

        summaryOutput.textContent = "AI xulosa tayyorlanmoqda...";
        try {
            const response = await fetch(`/ai/summary/${patientId}/`);
            const data = await response.json();
            summaryOutput.textContent = data.summary || "Xulosa olinmadi.";
        } catch (error) {
            summaryOutput.textContent = "AI xulosa vaqtincha mavjud emas.";
        }
    };

    if (summaryBtn && summaryOutput) {
        summaryBtn.addEventListener("click", loadSummary);
    }

    void loadSummary();

    const chatForm = document.getElementById("chatForm");
    const chatOutput = document.getElementById("chatOutput");
    if (chatForm && chatOutput) {
        chatForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            chatOutput.textContent = "AI javob tayyorlanmoqda...";
            const formData = new FormData(chatForm);

            try {
                const response = await fetch(`/ai/chat/${patientId}/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                    },
                    body: new URLSearchParams(formData),
                });
                const data = await response.json();
                chatOutput.textContent = data.reply || "Javob olinmadi.";
            } catch (error) {
                chatOutput.textContent = "AI chat vaqtincha ishlamayapti.";
            }
        });
    }
});
