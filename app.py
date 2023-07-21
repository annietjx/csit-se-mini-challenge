"""
CSIT Software Challenge
"""

import flask
from flask import Flask, request, Response, jsonify
from pymongo import MongoClient
import sys
from datetime import datetime, date, timezone
import json

mongo_client = MongoClient('mongodb+srv://userReadOnly:7ZT817O8ejDfhnBM@minichallenge.q4nve1r.mongodb.net/')
db = mongo_client.minichallenge
collection = db['flights']

app = Flask(__name__)


@app.route('/')
def index():
    """ Displays the index page accessible at '/'
    """
    return "Welcome to the CSIT mini software challenge."


def validateDate(date_str):
    """
    :param date_str: Date in a string format. E.g. "2023-12-10"
    :return: success, date_obj
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        success = True
    except ValueError:
        date_obj = None
        success = False
    return success, date_obj


def checkIfComingBackLessThanDeparture(departure, coming_back):
    """
    :param departure: Date in a string format. E.g. "2023-12-10"
    :param coming_back: Date in a string format. E.g. "2023-12-10"
    :return: success, message
    """
    try:
        departure_date = datetime.strptime(departure, "%Y-%m-%d").date()
        coming_back_date = datetime.strptime(coming_back, "%Y-%m-%d").date()

        if coming_back_date < departure_date:
            success = False
            message = "Coming back date cannot be earlier than the departure date."
        else:
            success = True
            message = "Coming back date is valid."

    except ValueError:
        success = False
        message = "Invalid date format."

    return success, message


@app.route('/flight')
def flight():
    """
    Get a list of return flights at the cheapest price,
    given the destination city, departure date, and arrival date.
    Returns an array containing the details of the cheapest return flights.
    There can be 0 or more items returned.
    """
    # Get query parameters
    departure_date = request.args.get('departureDate')
    return_date = request.args.get('returnDate')
    destination = request.args.get('destination')
    collection = db["flights"]

    # Check if query parameters are missing
    if not departure_date or not return_date or not destination:
        Response("Query parameters are incorrect or missing.", status=400)

    # Validate the dates
    success, dep_ans = validateDate(departure_date)
    if not success:
        return Response(f"departure date: {dep_ans}", status=400)

    success, ans = validateDate(return_date)
    if not success:
        return Response(f"return date: {ans}", status=400)

    if len(destination) == 0:
        return Response(f"No destination provided", status=400)

    success, message = checkIfComingBackLessThanDeparture(departure_date, return_date)
    if not success:
        return Response(f"{message}", status=400)

    # Query MongoDB for cheapest flights
    results = collection.find({
        "srccity": destination,
        "destcity": "Singapore",
        "date": ans
    })

    cheapest_price = sys.maxsize
    list_of_departing_flights = []

    for result in results:
        if (result["price"] < cheapest_price):
            cheapest_price = result["price"]
            list_of_departing_flights.clear()
            list_of_departing_flights.append(result)
            continue

        if (result["price"] == cheapest_price):
            list_of_departing_flights.append(result)
            continue

    results = collection.find({
        "srccity": "Singapore",
        "destcity": destination,
        "date": dep_ans
    })

    cheapest_price = sys.maxsize
    list_of_arriving_flights = []

    for result in results:
        if (result["price"] < cheapest_price):
            cheapest_price = result["price"]
            list_of_arriving_flights.clear()
            list_of_arriving_flights.append(result)
            continue

        if (result["price"] == cheapest_price):
            list_of_arriving_flights.append(result)
            continue

    answer = []
    for depart_flight in list_of_departing_flights:
        for arr_flight in list_of_arriving_flights:
            dict = {"City": depart_flight["destcity"],
                    "Departure Airline": depart_flight["airlinename"],
                    "Departure Date": date(dep_ans.year, dep_ans.month, dep_ans.day),
                    "Departure Price": arr_flight["price"],
                    "Return Airline": arr_flight["airlinename"],
                    "Return Date": date(ans.year, ans.month, ans.day),
                    "Return Price": depart_flight["price"]
                    }
            answer.append(dict)

    print(answer)

    print(f"Departure: {departure_date}, coming back: {return_date}, destination: {destination}")
    return Response(json.dumps(answer, indent=4, sort_keys=True, default=str), status=200)


@app.route('/hotel')
def hotel():
    """
    Get a list of hotels providing the cheapest price,
    given the destination city, check-in date, and check-out date.
    Returns an array containing the details of the cheapest hotels.
    There can be 0 or more items returned.
    """
    # Get query parameters
    checkin_date = request.args.get('checkInDate')
    checkout_date = request.args.get('checkOutDate')
    destination = request.args.get('destination')
    collection = db["hotels"]

    # Check if query parameters are missing
    if not checkin_date or not checkout_date or not destination:
        Response("Query parameters are incorrect or missing.", status=400)

    # Validate the dates
    success, dep_ans = validateDate(checkin_date)
    if not success:
        return Response(f"check in date: {dep_ans}", status=400)

    success, ans = validateDate(checkout_date)
    if not success:
        return Response(f"check out date: {ans}", status=400)

    if len(destination) == 0:
        return Response(f"No destination provided", status=400)

    success, message = checkIfComingBackLessThanDeparture(checkin_date, checkout_date)
    if not success:
        return Response(f"{message}", status=400)

    # Query MongoDB for cheapest hotels
    results = collection.aggregate([
        {
            '$match': {
                'city': destination,
                'date': {
                    # '$gte': datetime(2023, 12, 10, 0, 0, 0, tzinfo=timezone.utc),
                    # '$lte': datetime(2023, 12, 16, 0, 0, 0, tzinfo=timezone.utc)
                    '$gte': datetime(dep_ans.year, dep_ans.month, dep_ans.day, 0, 0, 0, tzinfo=timezone.utc),
                    '$lte': datetime(ans.year, ans.month, ans.day, 0, 0, 0, tzinfo=timezone.utc)
                }
            }
        }, {
            '$group': {
                '_id': '$hotelName',
                'total_price': {
                    '$sum': '$price'
                }
            }
        }, {
            '$sort': {
                'total_price': 1
            }
        }
    ])

    print(results)

    cheapest_hotels = []
    cheapest_price = sys.maxsize

    for result in results:
        if result["total_price"] < cheapest_price:
            cheapest_price = result["total_price"]
            cheapest_hotels.clear()
            cheapest_hotels.append(result)
            continue
        if result["total_price"] == cheapest_price:
            cheapest_hotels.append(result)
            continue

    answer = []
    for hotel in cheapest_hotels:
        dict = {"City": destination,
                "Check In Date": date(dep_ans.year, dep_ans.month, dep_ans.day),
                "Check Out Date": date(ans.year, ans.month, ans.day),
                "Hotel": hotel["_id"],
                "Price": hotel["total_price"]
                }
        answer.append(dict)

    print(answer)
    print(f"Departure: {checkin_date}, coming back: {checkout_date}, destination: {destination}")

    return Response(json.dumps(answer, indent=4, sort_keys=True, default=str), status=200)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
