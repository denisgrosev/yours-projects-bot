# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import logging

from balance_utils import (
    add_user_balance,
    add_ref_balance,
    get_ref_balance,
    process_referral_bonus,
    get_referrer_id,  # если используешь где-то отдельно
    set_user_balance,  # если потребуется
    set_ref_balance,   # если потребуется
)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/yookassa-callback", methods=["POST"])
def yookassa_callback():
    data = request.get_json()
    logging.info("Получен callback от ЮKassa: %s", data)

    try:
        if data:
            if data.get("event") == "payment.succeeded":
                user_id = int(data["object"]["metadata"]["user_id"])
                amount = float(data["object"]["amount"]["value"])
                add_user_balance(user_id, amount)
                
                # Вот здесь начисляем реферальный бонус
                bonus, referrer_id = process_referral_bonus(user_id, amount)
                if bonus and referrer_id:
                    logging.info(
                        f"Реферал: user_id={user_id} пополнил баланс, пригласившему {referrer_id} начислено {bonus}₽ (ref_balance={get_ref_balance(referrer_id)})"
                    )
                logging.info(f"Пополнение баланса: user_id={user_id}, amount={amount}")
                return jsonify({"status": "ok"})

            if data.get("object", {}).get("status") == "succeeded":
                user_id = int(data["object"]["metadata"]["user_id"])
                amount = float(data["object"]["amount"]["value"])
                add_user_balance(user_id, amount)
                # Аналогично начисляем бонус
                bonus, referrer_id = process_referral_bonus(user_id, amount)
                if bonus and referrer_id:
                    logging.info(
                        f"Реферал: user_id={user_id} пополнил баланс, пригласившему {referrer_id} начислено {bonus}₽ (ref_balance={get_ref_balance(referrer_id)})"
                    )
                logging.info(f"Зачислено {amount}₽ на баланс пользователя {user_id}")
                return jsonify({"status": "ok"})

        logging.warning("Некорректный callback ЮKassa или неуспешный платёж: %s", data)
        return jsonify({"status": "ignored"}), 400
    except Exception as e:
        logging.error("Ошибка обработки webhook от ЮKassa: %s", e)
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    # 0.0.0.0 чтобы принимать запросы извне, порт можно указать любой открытый
    app.run(host="0.0.0.0", port=8080)