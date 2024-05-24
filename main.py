import discord
from discord.ext import commands, tasks

import datetime
import yaml
import asyncio

from functions.kc import get_today_events

with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

token = cfg.get("token",False)
if not token:
    print("plz fill config.yaml file from config_template.yaml")
    exit()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    target_time = datetime.time(4, 00)  # 15:30 (3:30 PM)
    bot.loop.create_task(check_today_matches(target_time))


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
        bot.loop.create_task(send_kc_event_embed_message(event, target_time_message_event))

async def send_kc_event_embed_message(event, target_time):
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    now = datetime.datetime.now()
    future = datetime.datetime.combine(now.date(), target_time)
    if now.time() > target_time:
        future = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), target_time)
    await asyncio.sleep((future - now).total_seconds())

    # Fonction start
    embed, attachement = event.get_embed_message()
    channel = bot.get_channel(int(cfg['discord']['channels']['kc']))
    await channel.send(embed=embed,file=attachement)
    
    
    # remove embed message 
    # new message début game
    # afficher les résultats 



bot.run(token)