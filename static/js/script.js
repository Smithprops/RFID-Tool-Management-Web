document.addEventListener("DOMContentLoaded", function () {
    const rfidInput = document.getElementById("rfid-input");

    if (rfidInput) {
        rfidInput.addEventListener("input", function () {
            if (this.value.length === 6) {
                document.getElementById("rfid-form").submit();
            }
        });
    }

    let countdown = document.getElementById("timer");
    if (countdown) {
        let timeLeft = parseInt(countdown.textContent);
        let interval = setInterval(() => {
            timeLeft--;
            countdown.textContent = timeLeft;
            if (timeLeft <= 0) {
                window.location.href = "/logout";
                clearInterval(interval);
            }
        }, 1000);
    }
});
