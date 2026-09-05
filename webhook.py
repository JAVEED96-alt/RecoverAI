import os
import csv
import hmac
import hashlib
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException

from dotenv import load_dotenv

from backend.razorpay_service import get_payments


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

ENV_PATH = os.path.join(
    BASE_DIR,
    "backend",
    ".env"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)

EXECUTION_LOG = os.path.join(
    OUTPUT_DIR,
    "execution_log.csv"
)

RECOVERY_LOG = os.path.join(
    OUTPUT_DIR,
    "recovery_log.csv"
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(ENV_PATH)

WEBHOOK_SECRET = os.getenv(
    "RAZORPAY_WEBHOOK_SECRET"
)

if not WEBHOOK_SECRET:

    raise RuntimeError(
        "RAZORPAY_WEBHOOK_SECRET not found "
        "in backend/.env"
    )


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="RecoverAI API",
    description="AI Revenue Recovery Agent",
    version="1.0.0"
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "RecoverAI API is running"
    }


# ============================================================
# PAYMENTS
# ============================================================

@app.get("/payments")
def payments():

    return get_payments()


# ============================================================
# VERIFY RAZORPAY WEBHOOK SIGNATURE
# ============================================================

def verify_webhook_signature(
    body: bytes,
    received_signature: str
):

    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        received_signature
    )


# ============================================================
# CHECK DUPLICATE EVENT
# ============================================================

def event_already_processed(event_id):

    if not os.path.exists(
        RECOVERY_LOG
    ):

        return False

    try:

        with open(
            RECOVERY_LOG,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row.get(
                    "event_id"
                ) == event_id:

                    return True

    except Exception:

        return False

    return False


# ============================================================
# FIND PAYMENT LINK IN EXECUTION LOG
# ============================================================

def find_recovery_record(
    payment_link_id
):

    if not os.path.exists(
        EXECUTION_LOG
    ):

        return None

    try:

        with open(
            EXECUTION_LOG,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                notes = str(
                    row.get(
                        "notes",
                        ""
                    )
                )

                if payment_link_id in notes:

                    return row

    except Exception as e:

        print(
            f"Error reading execution log: {e}"
        )

    return None


# ============================================================
# SAVE RECOVERY
# ============================================================

def save_recovery(
    event_id,
    payment_link_id,
    payment_id,
    amount,
    currency,
    reference_id
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    file_exists = os.path.exists(
        RECOVERY_LOG
    )

    with open(
        RECOVERY_LOG,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        fieldnames = [
            "event_id",
            "payment_link_id",
            "payment_id",
            "amount",
            "currency",
            "reference_id",
            "status",
            "recovered_at"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        if not file_exists:

            writer.writeheader()

        writer.writerow({

            "event_id": event_id,

            "payment_link_id": payment_link_id,

            "payment_id": payment_id,

            "amount": amount,

            "currency": currency,

            "reference_id": reference_id,

            "status": "recovered",

            "recovered_at":
                datetime.now().isoformat()
        })


# ============================================================
# RAZORPAY WEBHOOK
# ============================================================

@app.post(
    "/webhooks/razorpay"
)
async def razorpay_webhook(
    request: Request
):

    # ========================================================
    # 1. READ RAW BODY
    # ========================================================

    body = await request.body()

    if not body:

        raise HTTPException(
            status_code=400,
            detail="Webhook body is empty"
        )


    # ========================================================
    # 2. GET SIGNATURE
    # ========================================================

    signature = request.headers.get(
        "X-Razorpay-Signature"
    )

    if not signature:

        raise HTTPException(
            status_code=400,
            detail="Missing X-Razorpay-Signature"
        )


    # ========================================================
    # 3. VERIFY SIGNATURE
    # ========================================================

    if not verify_webhook_signature(
        body,
        signature
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid webhook signature"
        )


    # ========================================================
    # 4. PARSE JSON
    # ========================================================

    try:

        payload = await request.json()

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload"
        )


    # ========================================================
    # 5. EVENT ID
    # ========================================================

    event_id = request.headers.get(
        "x-razorpay-event-id"
    )

    if not event_id:

        event_id = (
            f"local_{datetime.now().timestamp()}"
        )


    # ========================================================
    # 6. PREVENT DUPLICATE WEBHOOK
    # ========================================================

    if event_already_processed(
        event_id
    ):

        return {

            "status": "already_processed",

            "event_id": event_id
        }


    # ========================================================
    # 7. GET EVENT TYPE
    # ========================================================

    event = payload.get(
        "event"
    )

    print()
    print("=" * 60)
    print("RAZORPAY WEBHOOK")
    print("=" * 60)
    print(
        f"Event: {event}"
    )
    print(
        f"Event ID: {event_id}"
    )


    # ========================================================
    # 8. ONLY PROCESS PAYMENT_LINK.PAID
    # ========================================================

    if event != "payment_link.paid":

        print(
            f"Ignoring event: {event}"
        )

        return {

            "status": "ignored",

            "event": event
        }


    # ========================================================
    # 9. GET PAYMENT LINK DATA
    # ========================================================

    try:

        payment_link = (
            payload
            ["payload"]
            ["payment_link"]
            ["entity"]
        )

    except KeyError:

        raise HTTPException(
            status_code=400,
            detail=(
                "payment_link entity missing "
                "from webhook payload"
            )
        )


    # ========================================================
    # 10. EXTRACT IMPORTANT VALUES
    # ========================================================

    payment_link_id = payment_link.get(
        "id"
    )

    amount_paid_paise = payment_link.get(
        "amount_paid",
        0
    )

    amount_paid = (
        float(amount_paid_paise)
        / 100
    )

    currency = payment_link.get(
        "currency",
        "INR"
    )

    reference_id = payment_link.get(
        "reference_id",
        ""
    )


    # ========================================================
    # 11. GET PAYMENT ID
    # ========================================================

    payment_id = ""

    try:

        payment_entity = (
            payload
            ["payload"]
            ["payment"]
            ["entity"]
        )

        payment_id = payment_entity.get(
            "id",
            ""
        )

    except KeyError:

        pass


    # ========================================================
    # 12. FIND OUR RECOVERY RECORD
    # ========================================================

    recovery_record = find_recovery_record(
        payment_link_id
    )

    if recovery_record:

        print(
            "Recovery record matched:"
        )

        print(
            recovery_record
        )

    else:

        print(
            "WARNING: Recovery record "
            "not found."
        )


    # ========================================================
    # 13. SAVE RECOVERY
    # ========================================================

    save_recovery(

        event_id=event_id,

        payment_link_id=payment_link_id,

        payment_id=payment_id,

        amount=amount_paid,

        currency=currency,

        reference_id=reference_id
    )


    # ========================================================
    # 14. RESULT
    # ========================================================

    print()
    print(
        "REVENUE RECOVERED!"
    )

    print(
        f"Payment Link: {payment_link_id}"
    )

    print(
        f"Payment ID: {payment_id}"
    )

    print(
        f"Recovered: {currency} {amount_paid:.2f}"
    )

    print("=" * 60)


    return {

        "status": "recovered",

        "event": event,

        "payment_link_id":
            payment_link_id,

        "payment_id":
            payment_id,

        "amount_recovered":
            amount_paid,

        "currency":
            currency
    }