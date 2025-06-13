import requests
import uuid
import base64
import os

YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "1098242")  # Только число, без shopId и пробелов!
YOOKASSA_API_KEY = os.getenv("YOOKASSA_API_KEY", "live_moIQGf5lyFY1en13fpaINTpnMBKAAnqaZBSHfdFqD1M")  # Без пробелов и переносов!

def create_payment(amount, description, return_url, user_id, email):
    url = "https://api.yookassa.ru/v3/payments"
    idempotence_key = str(uuid.uuid4())
    auth = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_API_KEY}"
    value = "{:.2f}".format(float(amount))
    headers = {
        "Content-Type": "application/json",
        "Idempotence-Key": idempotence_key,
        "Authorization": "Basic " + base64.b64encode(auth.encode()).decode()
    }
    data = {
        "amount": {
            "value": value,
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": return_url
        },
        "capture": True,
        "description": description,
        "metadata": {
            "user_id": str(user_id)
        },
        "receipt": {
            "customer": {
                "email": email
            },
            "items": [
                {
                    "description": description,
                    "quantity": "1.00",
                    "amount": {
                        "value": value,
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }
            ]
        }
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()