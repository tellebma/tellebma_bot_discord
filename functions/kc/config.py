import yaml

with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

BASE_URL = cfg["kc_api_url"]
TIMEZONE_STR = cfg["timezone"]