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
    webhook_secret = os.environ.get("STRIPE_ENDPOINT_SECRET")
    request_data = json.loads(request.data)

    event = None
    if webhook_secret:
        # Verify the signature using the raw body and secret
        signature = request.headers.get("stripe-signature")
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=webhook_secret
            )
        except Exception as e:
            logging.error(f"Webhook signature verification failed: {e} {signature}")
            return jsonify({"status": "error", "message": "Invalid signature"}), 400
    else:
        event = request_data

    # Get event type and event data
    event_type = event["type"]
    data_object = event["data"]["object"]

    # Log the received event type
    logging.info(f"Received event: {event_type}")

    # Handle different event types
    if event_type == "checkout.session.completed":
        # A new subscription was created via checkout
        customer_id = data_object.get("customer")
        subscription_id = data_object.get("subscription")

        # Fetch user by Stripe customer ID
        customer_email = data_object.get("customer_email")
        user = User.query.filter_by(email=customer_email).first()
        print(f"User: {user}")

        if user:
            # Update the user's subscription details
            logging.info(f"Updated subscription for user {user.email}")
        else:
            logging.warning(f"No user found for customer ID: {customer_id}")

    elif event_type == "customer.subscription.updated":
        # A subscription was updated
        customer_id = data_object.get("customer")
        subscription_id = data_object.get("id")

        customer_id = data_object.get("customer")  # Get the Stripe Customer ID
        customer = stripe.Customer.retrieve(customer_id)  # Fetch customer details
        customer_email = customer.get("email")  # Access the customer's email
        plan_nickname = data_object.get("plan").get("nickname")

        user = User.query.filter_by(email=customer_email).first()

        if user:
            logging.info(f"User: {user}")
            logging.info(f"Customer ID: {customer_id}")
            logging.info(f"Subscription ID: {subscription_id}")
            logging.info(f"Plan: {plan_nickname}")

            # Update the user's subscription details
            if not user.stripe_customer_id:
                user.stripe_customer_id = customer_id
            user.stripe_subscription_id = subscription_id
            user.subscription_plan = plan_nickname
            db.session.commit()

        logging.info(f"Updated subscription for user {user.email}")
    elif event_type == "customer.subscription.deleted":
        # Subscription was canceled
        customer_id = data_object.get("customer")
        user = User.query.filter_by(stripe_customer_id=customer_id).first()

        if user:
            # Clear the user's subscription details
            user.stripe_subscription_id = None
            user.subscription_plan = None
            db.session.commit()
            logging.info(f"Canceled subscription for user {user.email}")
        else:
            logging.warning(f"No user found for customer ID: {customer_id}")
    elif event_type == "customer.deleted":
        # Customer was deleted
        customer_id = data_object.get("id")
        user = User.query.filter_by(stripe_customer_id=customer_id).first()

        if user:
            # Clear the user's subscription details
            user.stripe_customer_id = None
            user.stripe_subscription_id = None
            user.subscription_plan = None
            db.session.commit()
            logging.info(
                f"Deleted customer {customer_id} and subscription for user {user.email}"
            )
        else:
            logging.warning(f"No user found for customer ID: {customer_id}")
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
