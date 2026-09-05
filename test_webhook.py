import os
import json
import hmac
import hashlib
import requests

from dotenv import load_dotenv


# ============================================================
# LOAD WEBHOOK SECRET
# ============================================================

load_dotenv(
    "E:/recovery_ai/backend/.env"
)

WEBHOOK_SECRET = os.getenv(
    "RAZORPAY_WEBHOOK_SECRET"
)

if not WEBHOOK_SECRET:
    raise RuntimeError(
        "RAZORPAY_WEBHOOK_SECRET not found"
    )


# ============================================================
# USE ONE PAYMENT LINK CREATED EARLIER
# ============================================================

PAYMENT_LINK_ID = "plink_TSS0oOseOCPB9h"

PAYMENT_ID = "pay_test_recovery_001"

AMOUNT_PAISE = 10000


# ============================================================
# CREATE REALISTIC RAZORPAY WEBHOOK PAYLOAD
# ============================================================

payload = {
    "event": "payment_link.paid",

    "payload": {

        "payment_link": {
            "entity": {
                "id": PAYMENT_LINK_ID,
                "amount": AMOUNT_PAISE,
                "amount_paid": AMOUNT_PAISE,
                "currency": "INR",
                "reference_id": "recovery_test_001"
            }
        },

        "payment": {
            "entity": {
                "id": PAYMENT_ID,
                "amount": AMOUNT_PAISE,
                "currency": "INR",
                "status": "captured"
            }
        }
    }
}


# ============================================================
# CONVERT TO RAW JSON
# ============================================================

body = json.dumps(
    payload,
    separators=(",", ":")
).encode("utf-8")


# ============================================================
# CREATE RAZORPAY-STYLE HMAC SIGNATURE
# ============================================================

signature = hmac.new(
    WEBHOOK_SECRET.encode("utf-8"),
    body,
    hashlib.sha256
).hexdigest()


# ============================================================
# SEND WEBHOOK TO FASTAPI
# ============================================================

headers = {

    "Content-Type": "application/json",

    "X-Razorpay-Signature": signature,

    "x-razorpay-event-id":
        "test-event-recovery-001"
}


print()
print("=" * 60)
print("SENDING TEST RAZORPAY WEBHOOK")
print("=" * 60)

response = requests.post(
    "http://127.0.0.1:8000/webhooks/razorpay",
    data=body,
    headers=headers
)


print()
print("Status:", response.status_code)

print("Response:")
print(response.text)

print("=" * 60)