from flask import Blueprint, request, flash, redirect, url_for, jsonify

from flask_login import login_required, current_user

from ..extensions import db

import stripe
import json
import os

payments = Blueprint("payments", __name__)


# Stripe payment route for subscription
@payments.route("/create-checkout-session", methods=["POST"])
@login_required
def create_checkout_session():
    plan = request.form.get("plan")  # Get the selected plan (basic, standard, premium)

    # Define the Stripe price IDs
    plan_prices = {
        "basic": "price_1Qk1QX2M7cCdaKqq3Ck5Smy2",
        "standard": "price_1Qk1gV2M7cCdaKqqh1g2AZNq",
        "premium": "price_1Qk1gy2M7cCdaKqqNC4SnWPM",
    }

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
        current_user.subscription_plan = plan
        db.session.commit()
        current_user.stripe_customer_id = checkout_session.customer
        db.session.commit()
        current_user.stripe_subscription_id = checkout_session.subscription

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
    # Replace this endpoint secret with your endpoint's unique secret
    # If you are testing with the CLI, find the secret by running 'stripe listen'
    # If you are using an endpoint defined with the API or dashboard, look in your webhook settings
    # at https://dashboard.stripe.com/webhooks
    webhook_secret = os.environ.get("STRIPE_ENDPOINT_SECRET")
    request_data = json.loads(request.data)

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = request.headers.get("stripe-signature")
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=webhook_secret
            )
            data = event["data"]
        except Exception as e:
            return e
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event["type"]
    else:
        data = request_data["data"]
        event_type = request_data["type"]
    data_object = data["object"]

    print("event " + event_type)

    if event_type == "checkout.session.completed":
        print("🔔 Payment succeeded!")
    elif event_type == "customer.subscription.trial_will_end":
        print("Subscription trial will end")
    elif event_type == "customer.subscription.created":
        print("Subscription created %s", event.id)
        print(f"Customer ID: {data_object.customer}")
    elif event_type == "customer.subscription.updated":
        print("Subscription created %s", event.id)
    elif event_type == "customer.subscription.deleted":
        # handle subscription canceled automatically based
        # upon your subscription settings. Or if the user cancels it.
        print("Subscription canceled: %s", event.id)
    elif event_type == "entitlements.active_entitlement_summary.updated":
        # handle active entitlement summary updated
        print("Active entitlement summary updated: %s", event.id)

    return jsonify({"status": "success"})
