# PyTeslaPowerSet
Check current power prices and set a Tesla charge state accordingly:
- If the Tesla is in Trip Mode™ (charge target above 90%) then do nothing
- If the power price tonight is low, then set the Tesla to charge full
- If the power price tonight is high, then set the Tesla to charge minimum

## Thanks!
Relies on Michiel Lowijs's [Tesla-Api](https://github.com/mlowijs/tesla_api) and Kimmo Huoman's [Nordpool](https://github.com/kipe/nordpool)  

Without their work, this wouldn't have been possible -- thanks guys!

# Setup
## Installation
Because of the external dependencies, this requires setuptools to be installed before the other requirements, so:
```
python -m venv venv
python -m pip install setuptools
python -m pip install -r requirements.txt
```
## Configuration
Uses environmental variables for things like username/password.  
Add a .env file in the root with:
```
TESLA_USER=your_email
TESLA_PASS=your_password
TESLA_TOKEN=your_access_token
MIN_PERCENT=desired_minimum_charge_limit (e.g. 50%)
MAX_PERCENT=desired_maximum_charge_limit (e.g. 90%)
BASE_CURRENCY=desired_currency_to_use
```
If you already have an access token that can be used to avoid storing the credentials locally (remember the access tokens expire after 45 days)

There are also a couple of behaviour toggles early in the script, set them according to your need:  
- `areas` - the Nordpool area to check for, NB *currently only supports 1 area*
- `cheap_threshold` - the decision threshold for whether to charge min or max (e.g. 280), NB *multiply by 1000 (conversion of cost/MWh to cost/kWh)*


## Scheduling
Add it to crontab for scheduling, for example:  
`30 22   * * *   user      python3.7 ~/PyTeslaPowerSet/main.py > /dev/null 2>&1`

# Basic logic
My original thoughts for the logic
- ideally, we want tomorrow's prices because it will have both the price of tonight (midnight) and tomorrow night (11pm)
- as a backup, we can use today's prices, because it will have the price tonight (11pm) and the useless one: yesterday night (midnight between yesterday and today)
  - Conclusion: So there are two interesting prices and one back up price:
  - #1: The price tonight -- which is prices_tomorrow[0]
  - #2: The price tomorrow night -- which is prices_tomorrow[-1]
  - #3: The price tonight (1 hr earlier) -- which is prices_today[-1]

So the logic should be as follows:
- If the car is set >90% charge limit -> do nothing, we're in Trip Mode™
- If the car is set to <= 90% charge limit -> decide whether to charge much (max_percent) or little (min_percent)
   - If the price is below threshold tonight -> set charge to max_percent
      - unless it's even lower tomorrow?