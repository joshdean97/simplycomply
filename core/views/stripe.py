from flask import Blueprint, request, flash, redirect, url_for, jsonify

from flask_login import login_required, current_user

from ..extensions import db
from ..models import User
from ..const import plan_prices

import stripe
import json
import os
import logging

logging.basicConfig(level=logging.INFO)

payments = Blueprint("payments", __name__)


# Stripe payment route for subscription
@payments.route("/create-checkout-session", methods=["POST"])
@login_required
def create_checkout_session():
    plan = request.form.get("plan")  # Get the selected plan (basic, standard, premium)

    # Cancel the user's existing subscription if it exists
    if current_user.stripe_subscription_id:
        try:
            stripe.Subscription.delete(current_user.stripe_subscription_id)
        except Exception as e:
            flash("Error canceling existing subscription. Please try again.", "danger")
            return redirect(url_for("views.choose_plan", user_id=current_user.id))

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": plan_prices[plan],
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=url_for("payments.payment_success", _external=True),
            cancel_url=url_for("payments.payment_cancel", _external=True),
            customer_email=current_user.email,
        )
        return redirect(checkout_session.url)
    except Exception as e:
        flash(f"Error creating checkout session: {e}", "danger")
        return redirect(url_for("views.choose_plan", user_id=current_user.id))


@payments.route("/payment-success")
@login_required
def payment_success():
    # Update user subscription in the database if needed
    flash("Payment successful! Your subscription has been activated.", "success")
    return redirect(url_for("views.profile"))


@payments.route("/payment-cancel")
@login_required
def payment_cancel():
    flash("Payment was cancelled. Please try again.", "warning")
    return redirect(url_for("views.choose_plan", user_id=current_user.id))


@payments.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        logging.error("Missing STRIPE_WEBHOOK_SECRET environment variable")
        return jsonify({"status": "error", "message": "Webhook secret not found"}), 400

    signature = request.headers.get("stripe-signature")
    try:
        # Verify the signature using the raw body and secret
        event = stripe.Webhook.construct_event(
            payload=request.data, sig_header=signature, secret=webhook_secret
        )
    except stripe.error.SignatureVerificationError as e:
        logging.error(f"Signature verification failed: {e}")
        return jsonify({"status": "error", "message": "Invalid signature"}), 400
    except Exception as e:
        logging.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

    # Handle different event types
    event_type = event["type"]
    data_object = event["data"]["object"]

    logging.info(f"Received event: {event_type}")
    logging.info(f"Event data: {data_object}")

    if event_type == "checkout.session.completed":
        # Handle checkout.session.completed event
        pass
    elif event_type == "customer.subscription.updated":
        # Handle customer.subscription.updated event
        pass
    elif event_type == "customer.subscription.deleted":
        # Handle customer.subscription.deleted event
        pass
    elif event_type == "customer.deleted":
        # Handle customer.deleted event
        pass
    else:
        logging.info(f"Unhandled event type: {event_type}")

    return jsonify({"status": "success"})


@payments.route("/update-plan", methods=["POST"])
@login_required
def update_plan():
    plan = request.form.get(
        "plan"
    )  # Get the selected plan (e.g., basic, standard, premium)

    # Define the Stripe price IDs (replace with your actual price IDs)
    plan_prices = {
        "basic": "price_1Qk1QX2M7cCdaKqq3Ck5Smy2",
        "standard": "price_1Qk1gV2M7cCdaKqqh1g2AZNq",
        "premium": "price_1Qk1gy2M7cCdaKqqNC4SnWPM",
    }

    if current_user.stripe_subscription_id:
        try:
            # Retrieve the current subscription
            subscription = stripe.Subscription.retrieve(
                current_user.stripe_subscription_id
            )

            # Retrieve the subscription item's ID
            subscription_item_id = subscription["items"]["data"][0]["id"]

            # Update the subscription on Stripe
            stripe.Subscription.modify(
                current_user.stripe_subscription_id,
                items=[
                    {
                        "id": subscription_item_id,  # Use the correct subscription item ID
                        "price": plan_prices[plan],
                    }
                ],
                proration_behavior="create_prorations",  # Ensure no extra charge for overlapping periods
            )

            # Update the user's subscription in the database
            current_user.subscription_plan = plan
            db.session.commit()

            flash("Your subscription has been updated successfully!", "success")
            return redirect(url_for("views.profile"))

        except Exception as e:
            flash(f"Error updating your subscription: {e}", "danger")
            return redirect(url_for("views.profile"))
    else:
        flash("You don't have an active subscription to update.", "danger")
        return redirect(url_for("views.profile"))
