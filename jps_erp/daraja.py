# jps_erp/utils.py
import requests
import json
import datetime
import os
from flask import current_app, flash

def get_mpesa_access_token():
    try:
        consumer_key = current_app.config['MPESA_CONSUMER_KEY']
        consumer_secret = current_app.config['MPESA_CONSUMER_SECRET']
        api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(api_url, auth=(consumer_key, consumer_secret))
        response.raise_for_status()  # Check if the request was successful
        json_response = response.json()
        return json_response['access_token']
    except requests.exceptions.RequestException as e:
        flash("Failed to obtain access token. Please try again later.", "danger")
        return None
    except KeyError:
        flash("Failed to obtain access token. Invalid response from server.", "danger")
        return None

def check_transaction_status(transaction_id):
    access_token = get_mpesa_access_token()
    if not access_token:
        return None
    
    api_url = "https://sandbox.safaricom.co.ke/mpesa/transactionstatus/v1/query"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "Initiator": current_app.config['MPESA_INITIATOR_NAME'],
        "SecurityCredential": current_app.config['MPESA_SECURITY_CREDENTIAL'],
        "CommandID": "TransactionStatusQuery",
        "TransactionID": transaction_id,
        "PartyA": current_app.config['MPESA_SHORTCODE'],
        "IdentifierType": "4",
        "ResultURL": current_app.config['MPESA_RESULT_URL'],
        "QueueTimeOutURL": current_app.config['MPESA_QUEUE_TIMEOUT_URL'],
        "Remarks": "Checking transaction status",
        "Occasion": "School Payment"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()  # Check if the request was successful
        return response.json()
    except requests.exceptions.RequestException as e:
        flash("Failed to check transaction status. Please try again later.", "danger")
        return None
    except KeyError:
        flash("Failed to check transaction status. Invalid response from server.", "danger")
        return None
