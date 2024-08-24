import requests

class SMSService:
    BASE_URL = "https://quicksms.advantasms.com/api/services"

    def __init__(self, api_key, partner_id):
        self.api_key = api_key
        self.partner_id = partner_id

    def send_single_sms(self, mobile, message, shortcode):
        url = f"{self.BASE_URL}/sendsms/"
        payload = {
            "apikey": self.api_key,
            "partnerID": self.partner_id,
            "message": message,
            "shortcode": shortcode,
            "mobile": mobile
        }
        response = requests.post(url, json=payload)
        return response.json()

    def send_bulk_sms(self, sms_list):
        url = f"{self.BASE_URL}/sendbulk/"
        payload = {
            "count": len(sms_list),
            "smslist": sms_list
        }
        response = requests.post(url, json=payload)
        return response.json()

    def get_delivery_report(self, message_id):
        url = f"{self.BASE_URL}/getdlr/"
        payload = {
            "apikey": self.api_key,
            "partnerID": self.partner_id,
            "messageID": message_id
        }
        response = requests.post(url, json=payload)
        return response.json()

    def get_account_balance(self):
        url = f"{self.BASE_URL}/getbalance/"
        payload = {
            "apikey": self.api_key,
            "partnerID": self.partner_id
        }
        response = requests.post(url, json=payload)
        return response.json()
