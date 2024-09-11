import logging
import logging.handlers
import sys
import yaml

with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

try:
    log_file_name = cfg.get("log",{}).get("filename","/app/log/discord.log")
    backup_count = int(cfg.get("log",{}).get("backup_count",5))
    datetime_format = cfg.get("log",{}).get("datetime_format",'%Y-%m-%d %H:%M:%S')
    log_message_format = cfg.get("log",{}).get("log_message_format","[{asctime}] [{levelname:<8}] {name}: {message}")
except:
    exit("Merci de refaire le fichier config.yaml")

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename=log_file_name,
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 Mb 
    backupCount=backup_count,  # Rotate through 5 files
)

formatter = logging.Formatter(log_message_format, datetime_format, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Configuration du handler de flux pour le terminal
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)