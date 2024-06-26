# netbox-st-napalm

## Install the correct Python version to get PyATS to run:
```st-netbox$ pyenv install 3.10.13```

### Use this version in the local folder:
```st-netbox$ pyenv local 3.10.13```

### create an venv
```st-netbox$ python -m venv .venv```

### Activate the venv
```st-netbox$ source .venv/bin/activate```

## Install all requirements
```
st-netbox$ pip install -r requirements.txt 
st-netbox$ pip install pyats[full]
```

## Create environment variables for autofill
```
cat src/.env
NB_URL="https://demo.netbox.dev"
NB_TOKEN="longlongapikey"
CLI_USERNAME="username"
CLI_PASSWORD="mypassword"
```

## Start streamlit
```st-netbox$ streamlit run src/Login.py```