document.addEventListener("DOMContentLoaded", function () {
    let barcodeInput = document.getElementById("barcode");
    let checkoutForm = document.getElementById("checkoutForm");

    // Automatically submit when barcode is scanned
    barcodeInput.addEventListener("input", function () {
        if (barcodeInput.value.trim().length >= 4) {  // Assuming barcode is at least 4 characters
            checkoutForm.requestSubmit(); // Auto-submit form
        }
    });

    checkoutForm.onsubmit = async function (event) {
        event.preventDefault();

        let barcode = barcodeInput.value.trim();

        if (barcode.length < 4) {
            alert("Invalid barcode. Please scan again.");
            barcodeInput.value = "";
            barcodeInput.focus();
            return;
        }

        let response = await fetch("/scan_tool", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ barcode })
        });

        let result = await response.json();

        if (response.ok) {
            alert(result.message);
        } else {
            alert("Error: " + (result.error || "Unknown error"));
        }

        // Clear barcode field after checkout
        barcodeInput.value = "";
        barcodeInput.focus();
    };
});
