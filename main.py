from dotenv import load_dotenv
import os
from datetime import datetime, timezone, timedelta
import logging
import teslajson
from nordpool import elspot

logging.basicConfig(filename='teslapower.log',
                    filemode='a',
                    #format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logging.info('*** TeslaPowerSetting starting ***')

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

base_currency = 'DKK'
areas = ['DK2']  # currently only supports 1 area
# Nordpool prices are per currency/MWh where household expenses are normally currency/kWh - so set threshold as 1000x
cheap_threshold = 280
# Thresholds for desired minimum/maximum when in normal usage (not in Trip Mode)
min_percent = 60
max_percent = 90

# Nordpool module returns times as UTC, generate a 'now' to compare with
# If this runs too early in the day, the prices may not be set for tomorrow yet (will be 'inf' as float) -- seems the price is announced around 1pm CET
now = datetime.now(tz=timezone.utc)
today = now.date()
tomorrow = now.date() + timedelta(days=1)
yesterday = now.date() - timedelta(days=1)

# Then get the power price in desired currency - both for today and tomorrow
price_ext = base_currency + '/MWh'
logging.info('Grabbing the updated prices...')
prices_spot = elspot.Prices(currency=base_currency)
prices_today = prices_spot.hourly(end_date=today, areas=areas)[
    'areas'][areas[0]]['values']
prices_tomorrow = prices_spot.hourly(end_date=tomorrow, areas=areas)[
    'areas'][areas[0]]['values']


# Thoughts
# - ideally, we want tomorrow's prices because it will have both the price of tonight (midnight) and tomorrow night (11pm)
# - as a backup, we can use today's prices, because it will have the price tonight (11pm) and the useless one: yesterday night (midnight between yesterday and today)
# -- Conclusion: So there are two interesting prices and one back up price:
# --- #1: The price tonight -- which is prices_tomorrow[0]
# --- #2: The price tomorrow night -- which is prices_tomorrow[-1]
# --- #3: The price tonight (1 hr earlier) -- which is prices_today[-1]

# So the logic should be as follows:
# 1) If the car is set >90% charge limit -> do nothing, we're in Trip Mode™
# 2) If the car is set to <= 90% charge limit -> decide whether to charge much (max_percent) or little (min_percent)
# 2a) If the price is below threshold tonight -> set charge to max_percent

if prices_tomorrow[0]['value'] == float('inf'):
    # tomorrow's prices are not available yet, use the latest price of today instead
    price_tonight = prices_today[-1]['value']
    logging.info(
        'Tomorow\'s prices are not available yet, so using today\'s list instead.')
else:
    # tomorrow's prices are available yet, so use the earliest price
    price_tonight = prices_tomorrow[0]['value']
    logging.info('Tomorow\'s prices are available and will be used.')


# get the car's current charge limit to determine whether it is in Trip Mode™
if tesla_token:
    c = teslajson.Connection(access_token=tesla_token)
else:
    c = teslajson.Connection(email=tesla_user, password=tesla_password)
v = c.vehicles[0]
current_charge_limit = v.data_request('charge_state')['charge_limit_soc']
logging.info('The Tesla\'s current charge limit is set to: ' +
             str(current_charge_limit) + " %")

if price_tonight < cheap_threshold and current_charge_limit <= 90:
    command = {"percent": max_percent}
    logging.info('Wow, cheap price tonight! ' +
                 str(price_tonight) + " " + str(price_ext))
    logging.info(
        'We are not in Trip Mode, so adjusting the charge limit. Sending command with payload: ' + str(command))
    v.command('set_charge_limit', data=command)
elif current_charge_limit <= 90:
    command = {"percent": min_percent}
    logging.info('Okay, not that cheap tonight: ' +
                 str(price_tonight) + " " + str(price_ext))
    logging.info(
        'We are not in Trip Mode, so adjusting the charge limit. Sending command with payload: ' + str(command))
    v.command('set_charge_limit', data=command)
else:
    logging.info(
        'The car is in Trip Mode, so not adjusting anything. The price tonight is: ' + str(price_tonight))

# TODO: Do I need these?
if not any(d['value'] == float('inf') for d in prices_today):
    # Todays prices has real values
    pass

if not any(d['value'] == float('inf') for d in prices_tomorrow):
    # Tomorrows prices has real values
    pass

# v.wake_up()
# v.data_request('charge_state')
# v.command('charge_start')

# TODO: Do I want to do something with location?
# If so need to figure out how to handling rounding of the GPS coordinates

w = v.data_request('drive_state')
# w = {'gps_as_of': 1577524888, 'heading': 4, 'latitude': 55.721638, 'longitude': 12.360973, 'native_latitude': 55.721638, 'native_location_supported': 1, 'native_longitude': 12.360973,
#     'native_type': 'wgs', 'power': 0, 'shift_state': None, 'speed': None, 'timestamp': 1577524889351}

# Seems 3 decimals is imprecise enough that it works for both work locations -- they're far enough apart to not confuse them
current_latitude = str(round(w["latitude"], 3))
current_longitude = str(round(w["longitude"], 3))

if current_latitude == home_lat and current_longitude == home_long:
    print("Car is at home.")
elif current_latitude == work1_lat and current_longitude == work1_long:
    print("Car is at location: Work1.")
elif current_latitude == work2_lat and current_longitude == work2_long:
    print("Car is at location: Work2.")
else:
    print("I don't know where the car is.")

logging.info('*** TeslaPowerSetting ended gracefully ***')
