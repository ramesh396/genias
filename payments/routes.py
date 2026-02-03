from flask import Blueprint, request, session, redirect, jsonify, current_app

from models_pg import db, User, Payment
from payments.utils import create_razorpay_order, verify_payment, get_razorpay_key
from utils.security import verify_csrf

payments_bp = Blueprint("payments", __name__)


# ---------------- CREATE ORDER ----------------
@payments_bp.route("/create_order", methods=["POST"])
def create_order():

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    verify_csrf()

    try:
        order = create_razorpay_order()
    except Exception:
        current_app.logger.exception("Razorpay order creation failed")
        return jsonify({"error": "Payment service unavailable"}), 500

    if not order:
        current_app.logger.error("Razorpay returned empty order")
        return jsonify({"error": "Failed to create order"}), 500

    return jsonify({
        "order_id": order["id"],
        "amount": order.get("amount"),
        "currency": order.get("currency"),
        "key": get_razorpay_key()
    })


# ---------------- PAYMENT SUCCESS ----------------
@payments_bp.route("/payment_success", methods=["POST"])
def payment_success():

    if "user_id" not in session:
        return redirect("/")

    verify_csrf()

    payment_id = request.form.get("razorpay_payment_id")
    order_id = request.form.get("razorpay_order_id")
    signature = request.form.get("razorpay_signature")

    if not payment_id or not order_id or not signature:
        current_app.logger.warning("Payment callback missing parameters")
        return "Payment failed: Missing parameters", 400

    # ---------- VERIFY PAYMENT ----------
    try:
        verified = verify_payment(payment_id, order_id, signature)
    except Exception:
        current_app.logger.exception("Razorpay signature verification error")
        return "Payment verification error", 500

    if not verified:
        current_app.logger.warning(f"Payment verification failed for order {order_id}")
        return "Payment verification failed", 400

    # ---------- USER CHECK ----------
    user = User.query.get(session["user_id"])
    if not user:
        current_app.logger.error("Payment success but user not found")
        return "User not found", 404

    # ---------- DUPLICATE PAYMENT PROTECTION ----------
    existing_payment = Payment.query.filter_by(order_id=order_id).first()
    if existing_payment:
        current_app.logger.info(f"Duplicate payment callback ignored: {order_id}")
        return redirect("/dashboard")

    # ---------- SAVE PAYMENT ----------
    try:
        user.plan = "pro"

        payment = Payment(
            user_id=user.id,
            payment_id=payment_id,
            order_id=order_id,
            amount=99,
            currency="INR",
            status="success"
        )

        db.session.add(payment)
        db.session.commit()

        session["plan"] = "pro"

        current_app.logger.info(
            f"Payment success | user={user.id} | order={order_id}"
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            f"Database error while saving payment | order={order_id}"
        )
        return "Failed to save payment details", 500

    return redirect("/dashboard")


# Handle direct GET access (e.g., user refreshes or pastes URL)
@payments_bp.route("/payment_success", methods=["GET"])
def payment_success_get():
    return redirect("/dashboard")
