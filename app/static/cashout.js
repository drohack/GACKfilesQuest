// GACKcoin Cashout QR Code functionality

let expiryTimer = null;

async function showCashoutQR() {
    try {
        const response = await fetch('/cashout-generate', {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            document.getElementById('qr-code-image').src = result.qr_code;
            document.getElementById('qr-expiry-time').textContent = result.expires_in;
            document.getElementById('qr-modal').classList.add('active');

            // Start countdown timer
            startExpiryTimer(result.expires_in);
        } else {
            alert('Failed to generate QR code. Please try again.');
        }
    } catch (error) {
        alert('An error occurred. Please try again.');
        console.error('Error generating QR code:', error);
    }
}

function startExpiryTimer(minutes) {
    // Clear any existing timer
    if (expiryTimer) {
        clearTimeout(expiryTimer);
    }

    // Set timer to close modal after expiry time
    expiryTimer = setTimeout(() => {
        closeQRModal();
        alert('QR code has expired. Please generate a new one if needed.');
    }, minutes * 60 * 1000); // Convert minutes to milliseconds
}

function closeQRModal() {
    document.getElementById('qr-modal').classList.remove('active');

    // Clear timer when manually closing
    if (expiryTimer) {
        clearTimeout(expiryTimer);
        expiryTimer = null;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const cashOutBtn = document.querySelector('.btn-cash-out');
    if (cashOutBtn) {
        cashOutBtn.addEventListener('click', showCashoutQR);
    }

    const modal = document.getElementById('qr-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeQRModal();
            }
        });
    }
});
