import os
import razorpay
from dotenv import load_dotenv
from flask import session

# Load environment variables
load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise Exception("Razorpay keys not configured in .env file")

# Razorpay client
razorpay_client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)


def get_razorpay_key():
    return RAZORPAY_KEY_ID


# ---------------- CREATE ORDER ----------------
def create_razorpay_order():

    # ⚠️ user must be logged in before calling
    user_id = session.get("user_id")

    if not user_id:
        raise Exception("No user in session for Razorpay order")

    order = razorpay_client.order.create({
        "amount": 9900,   # ₹99 in paise
        "currency": "INR",
        "payment_capture": 1,

        # 🔥 THIS IS WHAT WEBHOOK WILL READ
        "notes": {
            "user_id": str(user_id)
        }
    })

    return order


# ---------------- VERIFY SIGNATURE ----------------
def verify_payment(payment_id, order_id, signature):
    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_payment_id": payment_id,
            "razorpay_order_id": order_id,
            "razorpay_signature": signature
        })
        return True
    except Exception as e:
        print("Payment verification failed:", str(e))
        return False
