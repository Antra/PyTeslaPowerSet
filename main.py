from dotenv import load_dotenv
import os
from datetime import datetime, timezone, timedelta
import logging
from logging.handlers import RotatingFileHandler
import asyncio
from tesla_api import TeslaApiClient
from nordpool import elspot
import time

# Get the basic logging set up
logger = logging.getLogger(__name__)
log_folder = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_folder, 'teslapower.log')
logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler(log_file, maxBytes=102400, backupCount=2)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info('*** TeslaPowerSetting starting ***')

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
base_currency = os.getenv("BASE_CURRENCY")
min_percent = os.getenv("MIN_PERCENT")
max_percent = os.getenv("MAX_PERCENT")
# Nordpool prices are per currency/MWh where household expenses are normally currency/kWh - so set threshold as 1000x
cheap_threshold = float(os.getenv("CHEAP_THRESHOLD", "0"))


# Handle non-defined values
if not min_percent:
    min_percent = 60
if not max_percent:
    max_percent = 90
if not base_currency:
    base_currency = 'DKK'

areas = ['DK2']  # currently only supports 1 area
price_ext = base_currency + '/MWh'


def get_prices():
    '''Function to get the prices from the Nordpool module'''
    # Nordpool module returns times as UTC, generate a 'now' to compare with
    # If this runs too early in the day, the prices may not be set for tomorrow yet (will be 'inf' as float) -- seems the price is announced around 1pm CET
    now = datetime.now(tz=timezone.utc)
    today = now.date()
    tomorrow = now.date() + timedelta(days=1)
    # Then get the power price in desired currency - both for today and tomorrow
    logger.info('Grabbing the updated prices...')
    prices_spot = elspot.Prices(currency=base_currency)
    prices_today = prices_spot.hourly(end_date=today, areas=areas)[
        'areas'][areas[0]]['values']
    prices_tomorrow = prices_spot.hourly(end_date=tomorrow, areas=areas)[
        'areas'][areas[0]]['values']
    logger.debug(f'prices_today: {prices_today}')
    logger.debug(f'prices_tomorrow: {prices_tomorrow}')
    return prices_today, prices_tomorrow


def determine_better_price(tonight, tomorrow=None):
    '''Function to determine the best charge time and charge level base on the available prices.'''
    better_price_tomorrow = False
    if tomorrow[0]['value'] == float('inf') or tomorrow is None:
        price_tonight = tonight[-1]['value']
        logger.info(
            f'Only today\'s price is available ({price_tonight} {price_ext}).')
    else:
        price_tonight = tomorrow[0]['value']
        price_tomorrow = tomorrow[-1]['value']
        logger.info(
            f'Tomorow\'s prices ({price_tomorrow} {price_ext}) are available and will be used to compare against today\'s prices ({price_tonight} {price_ext}).')
        if price_tomorrow < price_tonight:
            # If the price for tomorrow night is better, then let's utilise that instead!
            better_price_tomorrow = True
            logger.info(
                f'The best price is tomorrow night: {price_tomorrow} {price_ext}.')
        else:
            logger.info(
                f'The best price is tonight: {price_tonight} {price_ext}.')
    return better_price_tomorrow, price_tonight

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
# 2a*) unless it's even lower tomorrow?


def get_charge_target():
    '''Function to determine desired charge target - doesnt look at Trip Mode'''
    prices_today, prices_tomorrow = get_prices()
    better_price_tomorrow, price_tonight = determine_better_price(
        prices_today, prices_tomorrow)
    if price_tonight < cheap_threshold and better_price_tomorrow == False:
        # If power is cheap, we're not in trip mode and the price is not even better tomorrow
        logger.info('Wow, cheap price tonight! ' +
                    str(price_tonight) + " " + str(price_ext))
        return max_percent
    else:
        # Otherwise return the min percentage
        return min_percent


async def main():
    '''Call the Tesla API, get the car, get the charge limit, and set the desired charge taget if not in Trip Mode'''
    charge_target = int(get_charge_target())
    client = TeslaApiClient(email=tesla_user,
                            password=tesla_password, token=tesla_token)
    vehicles = await client.list_vehicles()

    # TODO: I only have Tesla so far, so being lazy. :) -- fix if/when relevant
    car = vehicles[0]

    # Let's set a timeout of 10 mins, then we give up
    timeout = time.time() + 60*10
    while not car.state.lower() == 'online':
        if time.time() > timeout:
            logger.info(f'Timeout of {timeout} seconds reached, giving up...')
            break
        logger.info(f'The car is not currently awake  wake-up signal sent.')
        await car.wake_up()
        vehicles = await client.list_vehicles()
        car = vehicles[0]

    current_charge_limit = (await car.charge.get_state())['charge_limit_soc']
    # If charge limit is 90 or less, we're not in Trip Mode™
    if current_charge_limit <= 90:
        logger.info(
            f'The current charge limit was {current_charge_limit} %, setting it to {charge_target} % (no Trip Mode detected).')
        await car.charge.set_charge_limit(charge_target)
    else:
        logger.info(
            f'Trip Mode detected, so leaving the car with {current_charge_limit} % charge limit.')

    await client.close()


if __name__ == '__main__':
    asyncio.run(main())
    logger.info('*** TeslaPowerSetting ended gracefully ***')
