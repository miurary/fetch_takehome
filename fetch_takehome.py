import json
import math
import re

from datetime import datetime, time
from flask import Flask, request
from uuid import uuid4
from waitress import serve

REQUIRED_FIELDS = ["retailer", "purchaseDate", "purchaseTime", "items", "total"]
STRING_PATTERN = r"^[\w\s\.\-&]+$"
MONEY_PATTERN = r"^\d+\.\d{2}$"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"

app = Flask(__name__)

receipts = {}

class InvalidReceiptException(Exception):
    pass

def validate_receipt(receipt):
    validate_receipt_required_fields_exist(receipt)
    validate_receipt_required_fields_format(receipt)
    validate_items(receipt["items"])


def validate_receipt_required_fields_exist(receipt):
    for field in REQUIRED_FIELDS:
        if field not in receipt.keys():
            raise InvalidReceiptException("Required field missing in receipt")


def validate_receipt_required_fields_format(receipt):
    if re.match(STRING_PATTERN, receipt["retailer"]) is None:
        raise InvalidReceiptException("Bad formatting in retailer field")

    try:
        datetime.strptime(receipt["purchaseDate"], DATE_FORMAT)
        datetime.strptime(receipt["purchaseTime"], TIME_FORMAT)
    except ValueError:
        raise InvalidReceiptException("Bad formatting in date or time field")


    if re.match(MONEY_PATTERN, receipt["total"]) is None:
        raise InvalidReceiptException("Bad formatting in total field")

    if len(receipt["items"]) < 1:
        raise InvalidReceiptException("Items list is empty")


def validate_items(items):
    for receipt_item in items:
        if (
            "shortDescription" not in receipt_item.keys()
            or "price" not in receipt_item.keys()
            or re.match(STRING_PATTERN, receipt_item["shortDescription"]) is None
            or re.match(MONEY_PATTERN, receipt_item["price"]) is None
        ):
            raise InvalidReceiptException(f"Error with item description: {receipt_item}")
    

def score_receipt(receipt, receipt_id):
    score = (
        score_retailer_name(receipt["retailer"])
        + score_total(receipt["total"])
        + score_items(receipt["items"])
        + score_date(receipt["purchaseDate"])
        + score_time(receipt["purchaseTime"])
    )


    receipts[receipt_id] = score


def score_retailer_name(name):
    alnum_count = sum(1 for c in name if c.isalnum())

    return alnum_count


def score_total(total):
    score = 0
    converted_total = float(total)
    
    if converted_total % 0.25 == 0:
        score += 25

    if converted_total % 1.00 == 0:
        score += 50

    return score


def score_items(items):
    score = (len(items) // 2) * 5

    for item in items:
        if len(item["shortDescription"].strip()) % 3 == 0:
            score += math.ceil(float(item["price"]) * 0.2)

    return score


def score_date(purchase_date):
    formated_purchase_date = datetime.strptime(purchase_date, DATE_FORMAT).day
    if formated_purchase_date % 2 == 1:
        return 6
    else:
        return 0


def score_time(purchase_time):
    formatted_purchase_time = datetime.strptime(purchase_time, TIME_FORMAT).time()
    start = time(14)
    end = time(16)
    if start < formatted_purchase_time < end:
        return 10
    else:
        return 0
    

@app.route("/receipts/process", methods=['POST'])
def process_receipt():
    receipt = request.json

    try:
        validate_receipt(receipt)
    except InvalidReceiptException as e:
        return f"The receipt is invalid: {e}", 400

    receipt_id = str(uuid4())
    score_receipt(receipt, receipt_id)

    resp = {"id": receipt_id}

    return json.dumps(resp)


@app.route("/receipts/<receipt_id>/points")
def get_receipt_points(receipt_id):
    if receipt_id in receipts.keys():
        score = receipts[receipt_id]
        resp = {"points": score}
        return json.dumps(resp)
    else:
        return "No receipt found for that id", 404

serve(app, host="0.0.0.0", port=5000)