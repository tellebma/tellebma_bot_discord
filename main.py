import discord
import datetime
import yaml
import asyncio
import locale
import sys
import traceback
import logging
import logging.handlers
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


from functions import kc

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
    if bot.get_channel(int(cfg['discord']['channels']['kc'])):
        logger.info("Alert KC active")
        # notification
        scheduler = AsyncIOScheduler()
        scheduler.add_job(check_today_matches, CronTrigger(hour=4, minute=0))
        if bot.get_channel(int(cfg['discord']['channels']['kc_id'])):
            logger.info("ALert KC result active")
            # verification resultat
            scheduler.add_job(check_kc_result_embed_message, 'cron', hour='9,12,15,18,20,22')
        scheduler.start()

    if datetime_lancement.hour >= 4:
        await check_today_matches()
        await check_kc_result_embed_message()        


@bot.event
async def on_error(event, *args, **kwargs):
    # Handle all unhandled exceptions globally
    logging.error(traceback.format_exc())
    traceback.print_exc()
    await send_error_message(sys.exc_info())


@bot.command(name='delete', help='Supprime les X messages précédents dans le canal.')
@commands.has_permissions(manage_messages=True)
async def delete(ctx, number_of_messages: int):
    if number_of_messages < 1:
        await ctx.send("Le nombre de messages à supprimer doit être supérieur à 0.")
        return

    # +1 pour inclure le message de commande
    deleted = await ctx.channel.purge(limit=number_of_messages + 1)
    await ctx.send(f'{len(deleted) - 1} messages supprimés.', delete_after=5)


async def check_today_matches():
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    # Fonction start:
    events = kc.get_today_events()
    logger.info(f"{len(events)} a traiter auj.")
    for event in events:
        # ajout d'une loop pour chaque event.
        target_time_message_event = event.start - datetime.timedelta(hours=2)
        logger.info(f"Annonce kc programmé à {str(target_time_message_event.hour).zfill(2)}h{str(target_time_message_event.minute).zfill(2)}")
        bot.loop.create_task(
            send_kc_event_embed_message(event,
                                        datetime.time(target_time_message_event.hour,
                                                      target_time_message_event.minute)))


async def send_kc_event_embed_message(event, target_time):
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    now = datetime.datetime.now()
    future = datetime.datetime.combine(now.date(), target_time)
    if now.time() > target_time:
        future = datetime.datetime.combine(now.date() +
                                           datetime.timedelta(days=1),
                                           target_time)
    await asyncio.sleep((future - now).total_seconds())
 
    # Fonction start
    try:
        logger.info("C'est l'heure de l'annonce !")
        embed, attachements = event.get_embed_message()
        channel = bot.get_channel(int(cfg['discord']['channels']['kc']))
        embed_message = await channel.send(embed=embed, files=attachements)
        channel = bot.get_channel(int(cfg['discord']['channels']['kc_id']))
        if channel:
            await channel.send(f"[{event.id}] - {embed_message.id}")
            logger.info("Message sur channel kc_id envoyé")
            # send : [{event.id}] - {embed_message.id}
 
    except Exception as e:
        logging.error("error (send_kc_event_embed_message)",exc_info=e)
        await send_error_message(e, function="send_kc_event_embed_message")

    # remove embed message
    # new message début game
    # afficher les résultats


async def check_kc_result_embed_message():
    """Envoyer un message à une heure précise"""
    try:
        logger.info("Verification des résultats")
        channel = bot.get_channel(int(cfg['discord']['channels']['kc_id']))
        if not channel:
            return
        messages = [message async for message in channel.history(limit=10)]
        if messages:
            result_json = kc.get_result()
        for message in messages:
            if message.reactions:
                logger.info(f"❌ des reactions sont présentes sur le message {message.content}, il est alors ignoré")
                continue

            id_event, id_embed_message = kc.get_message_info(message.content)
            if not id_event or not id_embed_message:
                logger.warning("Ajout de la reaction '❌' a ce message car non conforme")
                await message.add_reaction('❌')
                continue
            result = kc.filtre_result(result_json, id_event)
            if not result:
                logger.info(id_event)
                logger.info("⏳ pas encore les résultats")
                # await message.add_reaction('⏳')
                continue

            event = kc.Event(result, ended=True)

            channel = bot.get_channel(int(cfg['discord']['channels']['kc']))
            message_embed = await channel.fetch_message(int(id_embed_message))
            if not message_embed:
                logger.warning("❌ Le message n'a pas été trouvé")
                await message.add_reaction('❌')
            
            logger.info("✅ Le message a bien été trouvé, génération du message")
            embed, attachements = event.get_embed_result_message()
            await message_embed.reply(embed=embed, files=attachements)
            logger.info("✅ Message résultat envoyé, suppression du message sur 'kc_id'.")
            await message.delete()
            
        logger.info("Traitement des résultats est terminé")

    except Exception as e:
        logging.error("error (check_kc_result_embed_message)",exc_info=e)
        await send_error_message(e, function="check_kc_result_embed_message")
        await send_error_message(sys.exc_info(), function="check_kc_result_embed_message")
    # remove embed message
    # new message début game
    # afficher les résultats


async def send_error_message(error_message, function=""):
    channel = bot.get_channel(int(cfg['discord']['channels']['error']))
    date = datetime.datetime.now().strftime('%A %d %B %Hh%M').capitalize()
    embed = discord.Embed(title=f"❌ ERROR HANDLER {function}",
                          description=date,
                          color=0xFF0000)
    embed.add_field(name="",
                    value="",
                    inline=True)
    embed.add_field(name="An unexpected error occurred",
                    value=f"{error_message}", inline=True)
    await channel.send(embed=embed)

bot.run(token, log_handler=None)
