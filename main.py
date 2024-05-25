import discord
from discord.ext import commands, tasks
import datetime
import yaml
import asyncio
import locale
import sys
import traceback

from functions.kc import get_today_events

with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

token = cfg.get("token",False)
if not token:
    print("plz fill config.yaml file from config_template.yaml")
    exit()

# Définir la localisation en français
locale.setlocale(locale.LC_TIME, cfg["local"])

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    datetime_lancement = datetime.datetime.now()
    print(f'We have logged in as {bot.user}')
    target_time = datetime.time(4, 00)
    bot.loop.create_task(check_today_matches(target_time))
    
    if datetime_lancement.hour >= 4:
        heure = datetime_lancement.hour
        minute = datetime_lancement.minute + 5
        if datetime_lancement.minute >= 50:
            heure = heure + 1
            minute = 5
        print(f"Prochaine verification à {heure}h{minute}")
        await check_today_matches(datetime.time(heure, minute))
        

@bot.on_error
async def on_error(event, *args, **kwargs):
    # Handle all unhandled exceptions globally
    channel = bot.get_channel(int(cfg['discord']['channels']['error']))
    date = datetime.datetime.now().strftime('%A %d %B %Hh%M').capitalize()
    embed=discord.Embed(title="ERROR HANDLER", description=date, color=0xFF0000)
    embed.add_field(name="", value="", inline=True)
    embed.add_field(name="An unexpected error occurred", value=f"{sys.exc_info()}", inline=True)
    await channel.send(embed=embed)
    traceback.print_exc()



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
        print(f"Annonce kc programmé à {target_time_message_event.hour}h{target_time_message_event.minute}")
        bot.loop.create_task(send_kc_event_embed_message(event, datetime.time(target_time_message_event.hour,target_time_message_event.minute)))

async def send_kc_event_embed_message(event, target_time):
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    now = datetime.datetime.now()
    future = datetime.datetime.combine(now.date(), target_time)
    if now.time() > target_time:
        future = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), target_time)
    await asyncio.sleep((future - now).total_seconds())
    print("C'est l'heure de l'annonce !")
    # Fonction start
    embed, attachement = event.get_embed_message()
    channel = bot.get_channel(int(cfg['discord']['channels']['kc']))
    await channel.send(embed=embed,file=attachement)
     
    # remove embed message 
    # new message début game
    # afficher les résultats 

bot.run(token)
