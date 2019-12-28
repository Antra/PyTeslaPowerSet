from dotenv import load_dotenv
import json
import os
from datetime import datetime, timezone, timedelta
import teslajson
from nordpool import elspot

# First set some basic config
load_dotenv()
tesla_token = os.getenv("TESLA_TOKEN")
tesla_user = os.getenv("TESLA_USER")
tesla_password = os.getenv("TESLA_PASS")
home_lat = os.getenv("HOME_LAT")
home_long = os.getenv("HOME_LONG")
work1_lat = os.getenv("WORK1_LAT")
work1_long = os.getenv("WORK1_LONG")
work2_lat = os.getenv("WORK2_LAT")
work2_long = os.getenv("WORK2_LONG")
cheap_power = 28.0

# Then get the power price
prices_spot = elspot.Prices()
# Get the most recent prices - and store the first and last values as tonight/tmorrow's prices
# If this runs too early in the day, the prices may not be set yet (will be 'inf') -- seems the price is announced around 1pm CET
# TODO: Add handling for prices being 'inf' and check for today instead?
price_latest24 = prices_spot.hourly(areas=['DK2'])['areas']['DK2']['values']
price_latest24_earliest, price_latest24_earliest_time = price_latest24[
    0]['value'], price_latest24[0]['start']
price_latest24_latest, price_latest24_latest_time = price_latest24[-1]['value'], price_latest24[-1]['start']

# The price returned is actually EUR/MWh - but that seems to coincide well with the actual electricity kWh-price in DKK (as øre value)
print("The price tonight", price_latest24_earliest_time,
      "is:", price_latest24_earliest)
print("The price tomorrow night", price_latest24_latest_time,
      "is:", price_latest24_latest)
# Nordpool module returns times as UTC, generate a 'now' to compare with
now = datetime.now(tz=timezone.utc)

timedelta_tonight = price_latest24_earliest_time - now
timedelta_tomorrow = price_latest24_latest_time - now

if timedelta_tomorrow.days > 0:
    print("price_latest24_latest_time is for tomorrow night")
    print("timestamp:", price_latest24_latest_time.time(),
          "and the price is:", price_latest24_latest)
elif timedelta_tomorrow.days == 0:
    print("price_latest24_latest_time is for tonight")
    print("timestamp:", price_latest24_latest_time.time(),
          "and the price is:", price_latest24_latest)
if timedelta_tonight.days > 0:
    print("price_latest24_earliest_time is for tomorrow night")
    print("timestamp:", price_latest24_earliest_time.time(),
          "and the price is:", price_latest24_earliest)
elif timedelta_tonight.days == 0:
    print("price_latest24_earliest_time is for tonight")
    print("timestamp:", price_latest24_earliest_time.time(),
          "and the price is:", price_latest24_earliest)

print(price_latest24_earliest_time.hour)
print(price_latest24_earliest_time.date())
print(price_latest24_latest_time.hour)
print(price_latest24_latest_time.date())
print(type(price_latest24_earliest_time))
print(type(price_latest24_latest_time))

# Is it cheap? If so, when?
if price_latest24_earliest < cheap_power and price_latest24_earliest < price_latest24_latest:
    # power is cheapest tonight!
    print("power is cheapest tonight (and below threshold!), so start charging at:",
          price_latest24_earliest_time)
    pass
elif price_latest24_latest < cheap_power and price_latest24_latest < price_latest24_earliest:
    # power is cheapest tomorrow!
    print("power is cheapest tomorrow (and below threshold!), so start charging at:",
          price_latest24_latest_time)
    pass
elif price_latest24_earliest < price_latest24_latest:
    # power is cheapest tonight, but it's now below the 'cheap' point
    print("power is cheapest tonight, but not below 'cheap' threshold!")
    pass
elif price_latest24_latest < price_latest24_earliest:
    # power is cheapest tomorrow, but it's now below the 'cheap' point
    print("power is cheapest tomorrow, but not below 'cheap' threshold!")
    pass
else:
    # it doesn't matter, the price is the same
    pass

# And let's set the charge limit accordingly
if tesla_token:
    c = teslajson.Connection(access_token=tesla_token)
else:
    c = teslajson.Connection(email=tesla_user, password=tesla_password)
v = c.vehicles[0]

# v.wake_up()
# v.data_request('charge_state')
# v.command('charge_start')

#w = v.data_request('drive_state')
w = {'gps_as_of': 1577524888, 'heading': 4, 'latitude': 55.721638, 'longitude': 12.360973, 'native_latitude': 55.721638, 'native_location_supported': 1, 'native_longitude': 12.360973,
     'native_type': 'wgs', 'power': 0, 'shift_state': None, 'speed': None, 'timestamp': 1577524889351}

current_latitude = str(w["latitude"])
current_longitude = str(w["longitude"])

if current_latitude == home_lat and current_longitude == home_long:
    print("Car is at home.")
elif current_latitude == work1_lat and current_longitude == work1_long:
    print("Car is at location: Work1.")
elif current_latitude == work2_lat and current_longitude == work2_long:
    print("Car is at location: Work2.")
else:
    print("I don't know where the car is.")
