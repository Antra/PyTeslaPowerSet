# PyTeslaPowerSet
Check current power prices and set a Tesla charge state accordingly

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