import yaml

with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

try:
    BASE_URL = cfg["kc"]["api_url"]
    TIMEZONE_STR = cfg["timezone"]
except KeyError:
    exit("Vous devez mettre à jour votre configuration")