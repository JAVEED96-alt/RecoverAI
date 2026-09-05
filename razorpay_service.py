import os
import razorpay
from dotenv import load_dotenv


# Load .env from project root
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

load_dotenv(ENV_PATH)


# Razorpay credentials
key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")


print("Razorpay Key ID loaded:", bool(key_id))
print("Razorpay Key Secret loaded:", bool(key_secret))


if not key_id or not key_secret:
    raise RuntimeError(
        "Razorpay credentials not found in .env"
    )


# Razorpay client
client = razorpay.Client(
    auth=(key_id, key_secret)
)


# Get payments
def get_payments():

    response = client.payment.all()

    return response