import discord
from discord.ext import commands, tasks
import datetime
import yaml
import asyncio
import locale
import sys
import traceback
import logging
import logging.handlers

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='log/discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Configuration du handler de flux pour le terminal
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

from functions.kc import get_today_events

with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

with open("version.yaml") as f:
    version = yaml.load(f, Loader=yaml.FullLoader)["version"]

token = cfg.get("token",False)
if not token:
    logger.error("plz fill config.yaml file from config_template.yaml")
    exit()

# Définir la localisation en français
locale.setlocale(locale.LC_TIME, cfg["local"])

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    datetime_lancement = datetime.datetime.now()
    logger.info(f"Version of this bot {version}")
    logger.info(f'We have logged in as {bot.user}')
    target_time = datetime.time(4, 00)
    bot.loop.create_task(check_today_matches(target_time))
    
    if datetime_lancement.hour >= 4:
        heure = datetime_lancement.hour
        minute = datetime_lancement.minute + 5
        if datetime_lancement.minute >= 50:
            heure = heure + 1
            minute = 5
        logger.info(f"Prochaine verification à {heure}h{minute}")
        await check_today_matches(datetime.time(heure, minute))
        

@bot.event
async def on_error(event, *args, **kwargs):
    # Handle all unhandled exceptions globally
    logging.warning(traceback.format_exc())
    traceback.print_exc()
    await send_error_message(sys.exc_info())

@bot.command(name='test', help='test de commande :)')
async def test(ctx):
    events = get_today_events()
    for event in events:
        logger.info(event.event_name)
        try:
            embed, attachements = event.get_embed_message()
            channel = bot.get_channel(int(cfg['discord']['channels']['kc']))
            await channel.send(embed=embed,files=attachements)
        except Exception as e:
            logging.warning(e)
            await send_error_message(e)
    
@bot.command(name='delete', help='Supprime les X messages précédents dans le canal.')
@commands.has_permissions(manage_messages=True)
async def delete(ctx, number_of_messages: int):
    if number_of_messages < 1:
        await ctx.send("Le nombre de messages à supprimer doit être supérieur à 0.")
        return

    # +1 pour inclure le message de commande
    deleted = await ctx.channel.purge(limit=number_of_messages + 1)
    await ctx.send(f'{len(deleted) - 1} messages supprimés.', delete_after=5)

async def check_today_matches(target_time):
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    now = datetime.datetime.now()
    future = datetime.datetime.combine(now.date(), target_time)
    if now.time() > target_time:
        future = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), target_time)
    await asyncio.sleep((future - now).total_seconds())

    # Fonction start:
    events = get_today_events()
    for event in events:
        # ajout d'une loop pour chaque event.
        target_time_message_event = event.date - datetime.timedelta(hours=2)
        logger.info(f"Annonce kc programmé à {target_time_message_event.hour}h{target_time_message_event.minute}")
        bot.loop.create_task(send_kc_event_embed_message(event, datetime.time(target_time_message_event.hour,target_time_message_event.minute)))

async def send_kc_event_embed_message(event, target_time):
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    now = datetime.datetime.now()
    future = datetime.datetime.combine(now.date(), target_time)
    if now.time() > target_time:
        future = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), target_time)
    await asyncio.sleep((future - now).total_seconds())
    logger.info("C'est l'heure de l'annonce !")
    # Fonction start
    try:
        embed, attachements = event.get_embed_message()
        channel = bot.get_channel(int(cfg['discord']['channels']['kc']))
        await channel.send(embed=embed,files=attachements)
    except Exception as e:
        logging.warning(e)
        await send_error_message(e)

    # remove embed message 
    # new message début game
    # afficher les résultats 


async def send_error_message(error_message):
    channel = bot.get_channel(int(cfg['discord']['channels']['error']))
    date = datetime.datetime.now().strftime('%A %d %B %Hh%M').capitalize()
    embed=discord.Embed(title="ERROR HANDLER", description=date, color=0xFF0000)
    embed.add_field(name="", value="", inline=True)
    embed.add_field(name="An unexpected error occurred", value=f"{error_message}", inline=True)
    await channel.send(embed=embed)

bot.run(token, log_handler=None)
