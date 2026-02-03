import json
import os
import hmac
import hashlib

from flask import Blueprint, request, current_app

from models_pg import db, User, Payment


payments_webhook_bp = Blueprint("payments_webhook", __name__)


def _amount_to_rupees(amount):
    if amount is None:
        return None
    # Razorpay sends amount in paise; normalize to rupees for consistency.
    if isinstance(amount, (int, float)) and amount >= 100:
        return int(amount / 100)
    return int(amount)


def _verify_signature(raw_body, signature, secret):
    if not signature or not secret:
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@payments_webhook_bp.route("/payments/webhook", methods=["POST"])
def razorpay_webhook():
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    signature = request.headers.get("X-Razorpay-Signature", "")
    raw_body = request.get_data()

    if not _verify_signature(raw_body, signature, secret):
        current_app.logger.warning("Razorpay webhook signature invalid or missing")
        return "invalid signature", 400

    try:
        data = json.loads(raw_body.decode("utf-8"))
    except Exception:
        current_app.logger.exception("Razorpay webhook JSON parse failed")
        return "invalid payload", 400

    event = data.get("event", "")
    payload = data.get("payload", {})

    payment_entity = (payload.get("payment") or {}).get("entity", {}) or {}
    order_entity = (payload.get("order") or {}).get("entity", {}) or {}

    order_id = payment_entity.get("order_id") or order_entity.get("id")
    payment_id = payment_entity.get("id")
    amount = payment_entity.get("amount") or order_entity.get("amount")
    currency = payment_entity.get("currency") or order_entity.get("currency")

    notes = {}
    if isinstance(order_entity.get("notes"), dict):
        notes.update(order_entity.get("notes"))
    if isinstance(payment_entity.get("notes"), dict):
        notes.update(payment_entity.get("notes"))

    user_id_raw = notes.get("user_id")
    user = None
    if user_id_raw:
        try:
            user = db.session.get(User, int(user_id_raw))
        except Exception:
            current_app.logger.warning(
                "Razorpay webhook user_id not int: %s",
                user_id_raw
            )

    payment = None
    if order_id:
        payment = Payment.query.filter_by(order_id=order_id).first()
    if not payment and payment_id:
        payment = Payment.query.filter_by(payment_id=payment_id).first()

    if not user and payment:
        user = db.session.get(User, payment.user_id)

    if not user:
        current_app.logger.error(
            "Razorpay webhook missing user for event=%s order=%s payment=%s",
            event,
            order_id,
            payment_id
        )
        return "ok", 200

    amount_rupees = _amount_to_rupees(amount)

    if event == "payment.captured":
        if payment and payment.status == "success":
            return "ok", 200

        if not payment:
            payment = Payment(
                user_id=user.id,
                payment_id=payment_id,
                order_id=order_id,
                amount=amount_rupees,
                currency=currency,
                status="success"
            )
            db.session.add(payment)
        else:
            payment.payment_id = payment.payment_id or payment_id
            payment.order_id = payment.order_id or order_id
            payment.amount = payment.amount or amount_rupees
            payment.currency = payment.currency or currency
            payment.status = "success"

        user.plan = "pro"
        db.session.commit()

        current_app.logger.info(
            "Razorpay captured | user=%s | order=%s | payment=%s",
            user.id,
            order_id,
            payment_id
        )

        return "ok", 200

    if event == "payment.failed":
        if not payment:
            payment = Payment(
                user_id=user.id,
                payment_id=payment_id,
                order_id=order_id,
                amount=amount_rupees,
                currency=currency,
                status="failed"
            )
            db.session.add(payment)
        else:
            payment.payment_id = payment.payment_id or payment_id
            payment.order_id = payment.order_id or order_id
            payment.amount = payment.amount or amount_rupees
            payment.currency = payment.currency or currency
            payment.status = "failed"

        db.session.commit()

        current_app.logger.info(
            "Razorpay failed | user=%s | order=%s | payment=%s",
            user.id,
            order_id,
            payment_id
        )

        return "ok", 200

    current_app.logger.info(
        "Razorpay webhook ignored event=%s order=%s payment=%s",
        event,
        order_id,
        payment_id
    )
    return "ok", 200
