# PyTeslaPowerSet
Check current power prices and set a Tesla charge state accordingly:
- If the Tesla is in Trip Mode™ (charge target above 90%) then do nothing
- If the power price tonight is low, then set the Tesla to charge full
- If the power price tonight is high, then set the Tesla to charge minimum

## Thanks!
Relies on Greg Glockner's [Tesla Json](https://github.com/gglockner/teslajson) and Kimmo Huoman's [Nordpool](https://github.com/kipe/nordpool)  

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
```
If you already have an access token that can be used to avoid storing the credentials locally

There are also a couple of behaviour toggles early in the script, set them according to your need:  
- `base_currency` - the currency you want to use
- `areas` - the Nordpool area to check for, NB *currently only supports 1 area*
- `cheap_threshold` - the decision threshold for whether to charge min or max (e.g. 280), NB *multiply by 1000 (conversion of cost/MWh to cost/kWh)*
- `min_percent` - the charge percent to use when price is above cheap_threshold (e.g. 60)
- `max_percent` - the charge percent to use when price is below cheap_threshold (e.g. 90)