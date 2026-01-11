// QR Code Scanner functionality
let html5QrCode;

// Initialize the QR code scanner
function initScanner() {
    html5QrCode = new Html5Qrcode("qr-reader");

    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0
    };

    // Start scanning
    html5QrCode.start(
        { facingMode: "environment" }, // Use back camera
        config,
        onScanSuccess,
        onScanError
    ).catch(err => {
        // If back camera fails, try front camera
        html5QrCode.start(
            { facingMode: "user" },
            config,
            onScanSuccess,
            onScanError
        ).catch(err => {
            showError("Unable to access camera. Please grant camera permissions.");
            console.error("Camera error:", err);
        });
    });
}

// Handle successful QR code scan
function onScanSuccess(decodedText, decodedResult) {
    console.log("QR Code scanned:", decodedText);

    // Stop scanning
    html5QrCode.stop().then(() => {
        // Parse the QR code content
        processQRCode(decodedText);
    }).catch(err => {
        console.error("Error stopping scanner:", err);
        processQRCode(decodedText);
    });
}

// Handle scan errors (can be ignored, happens frequently during scanning)
function onScanError(errorMessage) {
    // Ignore - this fires constantly while scanning
}

// Process the scanned QR code
async function processQRCode(qrContent) {
    // QR code can contain:
    // 1. Evidence URL: https://gackfiles.saltychart.net/qr/GACK_HEAD_7X9K2
    // 2. Cashout URL: https://gackfiles.saltychart.net/admin/cashout/TOKEN
    // 3. Plain code: GACK_HEAD_7X9K2

    let scanCode = qrContent.trim();

    // Check if this is a cashout URL
    const cashoutMatch = qrContent.match(/\/admin\/cashout\/([A-Za-z0-9_-]+)/);
    if (cashoutMatch) {
        // This is a cashout QR code - redirect to the cashout page
        showSuccess("Cashout QR detected! Redirecting to cashout page...");
        setTimeout(() => {
            window.location.href = qrContent;
        }, 1000);
        return;
    }

    // Extract evidence scan code from URL if present
    const urlMatch = qrContent.match(/\/qr\/([A-Z0-9_]+)/i);
    if (urlMatch) {
        scanCode = urlMatch[1];
    }

    showSuccess("Verifying evidence code...");

    try {
        const response = await fetch('/verify-scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code: scanCode })
        });

        const result = await response.json();

        if (result.success) {
            // Code verified, video marked as found
            showSuccess("Evidence discovered! Accessing file...");

            // Check for bonus coin award
            if (result.bonus_awarded && result.bonus_message) {
                alert('🎉 ' + result.bonus_message);
            }

            setTimeout(() => {
                window.location.href = `/video?id=${result.video_id}`;
            }, 1000);
        } else {
            // Invalid code
            showError("Invalid evidence code. Scan a valid GACKfiles marker.");
            // Restart scanner after 3 seconds
            setTimeout(() => {
                hideMessages();
                initScanner();
            }, 3000);
        }
    } catch (error) {
        showError("Error verifying code. Please try again.");
        console.error("Verification error:", error);
        // Restart scanner after 3 seconds
        setTimeout(() => {
            hideMessages();
            initScanner();
        }, 3000);
    }
}

// Show success message
function showSuccess(message) {
    const resultDiv = document.getElementById('scan-result');
    const resultText = document.getElementById('result-text');
    const errorDiv = document.getElementById('error-message');

    errorDiv.style.display = 'none';
    resultText.textContent = message;
    resultDiv.style.display = 'block';
}

// Show error message
function showError(message) {
    const resultDiv = document.getElementById('scan-result');
    const errorDiv = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');

    resultDiv.style.display = 'none';
    errorText.textContent = message;
    errorDiv.style.display = 'block';
}

// Hide all messages
function hideMessages() {
    document.getElementById('scan-result').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';
}

// Initialize scanner when page loads
window.addEventListener('load', () => {
    initScanner();
});

// Clean up when page unloads
window.addEventListener('beforeunload', () => {
    if (html5QrCode) {
        html5QrCode.stop().catch(err => {
            console.error("Error stopping scanner:", err);
        });
    }
});
