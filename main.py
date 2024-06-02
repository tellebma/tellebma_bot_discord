import discord
import datetime
import yaml
import asyncio
import locale
import sys
import traceback
import logging
import pytz

from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import List, Dict, Any, Optional

from functions import kc
from functions.log import logger

# ~~~~~~~~
#  CONFIG
# ~~~~~~~~
with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

with open("version.yaml") as f:
    version = yaml.load(f, Loader=yaml.FullLoader)["version"]

token = cfg.get("token",False)
if not token:
    logger.error("plz fill config.yaml file from config_template.yaml")
    exit()

MESSAGE_DEBUT_GAME = cfg["debut_game"]
LIST_ANNONCE_TO_BE_PUBLISHED = []

# Définir la localisation en français
locale.setlocale(locale.LC_TIME, cfg["local"])

# ~~~~~~~~~
#  Discord
# ~~~~~~~~~
intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    datetime_lancement = datetime.datetime.now()
    logger.info(f"Version of this bot {version}")
    logger.info(f'We have logged in as {bot.user}')  
    if bot.get_channel(int(cfg['discord']['channels']['kc'])):
        logger.info("✅ - Alert KC active")
        # notification
        scheduler = AsyncIOScheduler()
        # scheduler.add_job(check_today_matches, CronTrigger(hour=4, minute=0))
        scheduler.add_job(check_today_matches, 'cron', hour='2,8,12,16,20,23')
        if bot.get_channel(int(cfg['discord']['channels']['kc_id'])):
            logger.info("✅ - Alert KC result active")
            # verification resultat
            scheduler.add_job(check_kc_result_embed_message, 'cron', hour='9,12,15,18,22')
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
        await ctx.send("❌ Le nombre de messages à supprimer doit être supérieur à 0.")
        logger.info(f'❌ Le nombre de messages à supprimer doit être supérieur à 0. - {ctx.author}')
        return

    # +1 pour inclure le message de commande
    deleted = await ctx.channel.purge(limit=number_of_messages + 1)
    await ctx.send(f'✅ {len(deleted) - 1} messages supprimés.', delete_after=5)
    logger.info(f'✅ {len(deleted) - 1} messages supprimés - {ctx.author}')


async def check_today_matches():
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    # Fonction start:
    events = kc.get_today_events()
    logger.info(f"{len(events)} a traiter auj.")
    messages_list = await kc_list_annonce_publie()
    events_id_published = [m.get("id_event") for m in messages_list]
    for event in events:
        if event.id in events_id_published or event.id in LIST_ANNONCE_TO_BE_PUBLISHED:
            # Si l'annonce est déjà prévu ou déjà envoyé skip
            continue
        # ajout d'une loop pour chaque event.
        logger.info(f"Annonce: {event.id} - {event.title}")
        target_time_message_event = event.start - datetime.timedelta(hours=2)
        now = kc.update_timezone(datetime.datetime.now(),pytz.timezone(cfg.get("timezone","Europe/Paris")),timezone_dest_str=cfg.get("timezone","Europe/Paris"))
        
        if target_time_message_event > now:
            # on publi l'annonce dans 2h
            logger.info(f"   ↳  Annonce kc programmé à {str(target_time_message_event.hour).zfill(2)}h{str(target_time_message_event.minute).zfill(2)}")
        else:
            # On a loupé les 2heures de com
            target_time_message_event = now
            logger.info(f"   ↳  Annonce kc à envoyer dès mnt {str(target_time_message_event.hour).zfill(2)}h{str(target_time_message_event.minute).zfill(2)}")

        bot.loop.create_task(
            send_kc_event_embed_message(event,
                                        datetime.time(target_time_message_event.hour,
                                                      target_time_message_event.minute)))
        LIST_ANNONCE_TO_BE_PUBLISHED.append(event.id)

        target_time_message_stream = event.start - datetime.timedelta(minutes=5)
        bot.loop.create_task(
            send_kc_twitch_link_message(event,
                                        datetime.time(target_time_message_stream.hour,
                                                      target_time_message_stream.minute)))
        logger.info(f"       ↳  Message stream sera envoyé à {str(target_time_message_stream.hour).zfill(2)}h{str(target_time_message_stream.minute).zfill(2)}")


async def send_kc_twitch_link_message(event, target_time):
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    now = datetime.datetime.now()
    future = datetime.datetime.combine(now.date(), target_time)
    if now.time() > target_time:
        future = datetime.datetime.combine(now.date() +
                                           datetime.timedelta(days=1),
                                           target_time)
    await asyncio.sleep((future - now).total_seconds())

    channel = bot.get_channel(int(cfg['discord']['channels']['kc_id']))
    if not channel:
        return
    messages_list = await kc_list_annonce_publie()
    logger.info(f"⇒ Annonce avec le lien du stream  ! {event.id} - {event.title}")
    for message_el in messages_list:
        id_event = message_el.get("id_event")
        id_embed_message =  message_el.get("id_embed_message")

        if not id_event or not id_embed_message:
            continue

        if id_event != event.id:
            continue

        message_embed = await channel.fetch_message(int(id_embed_message))
        message_embed.reply(f"{event.title}\n{MESSAGE_DEBUT_GAME}\n{event.stream}")
        logger.info("   ↳  ✅ Message stream envoyé !")
        return
    logger.error("❌ Message stream erreur (message not found)")
    
    
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
    logger.info(f"⇒ C'est l'heure de l'annonce ! {event.id} - {event.title}")
    try:
        # renew info on this event
        old_event = event
        event_json = kc.get_id_event(event.id)
        if event_json:
            event = kc.Event(event_json)
            logger.info("   ↳  Données Mise à jour !")
        
    except:
        logger.warning("   ↳  ❌ La mise a jour des info de l'event n'a pas réussi.")
        event = old_event
    
    try:
        
        embed, attachements = event.get_embed_message()
        channel = bot.get_channel(int(cfg['discord']['channels']['kc']))
        embed_message = await channel.send(embed=embed, files=attachements)
        channel = bot.get_channel(int(cfg['discord']['channels']['kc_id']))
        await channel.send(f"[{event.id}] - {embed_message.id}")
        logger.info("   ↳  ✅ Message sur channel kc_id envoyé")
        # send : [{event.id}] - {embed_message.id}
        LIST_ANNONCE_TO_BE_PUBLISHED.remove(event.id)
 
    except Exception as e:
        logging.error("❌ error (send_kc_event_embed_message)",exc_info=e)
        await send_error_message(e, function="send_kc_event_embed_message")

    logger.info("⇐ Fonction annonce ")
    # remove embed message
    # new message début game
    # afficher les résultats


async def check_kc_result_embed_message():
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    try:
        logger.info("⇒ Verification des résultats des match KC")
        messages_list = await kc_list_annonce_publie()
        if messages_list:
            result_json = kc.get_result()
        for message_el in messages_list:
            message = message_el["message"] # Discord Message 

            if message.reactions:
                logger.info(f"❌ des reactions sont présentes sur le message {message.content}, il est alors ignoré")
                continue

            id_event = message_el.get("id_event")
            id_embed_message = message_el.get("id_embed_message")

            if not id_event or not id_embed_message:
                logger.warning("Ajout de la reaction '❌' a ce message car non conforme")
                await message.add_reaction('❌')
                continue

            result = kc.filtre_result(result_json, id_event)
            logger.info(f"Resultats: {id_event}")
            if not result:
                logger.info("   ↳  ⏳ pas encore les résultats")
                # await message.add_reaction('⏳')
                continue

            event = kc.Event(result, ended=True)
            logger.info(f"   ↳  ✅ Annonce terminé: {event.title}")
            channel = bot.get_channel(int(cfg['discord']['channels']['kc']))
            message_embed = await channel.fetch_message(int(id_embed_message))
            if not message_embed:
                logger.warning("   ↳  ❌ Le message n'a pas été trouvé")
                await message.add_reaction('❌')
            
            logger.info("   ↳  ✅ Le message a bien été trouvé, génération du message")
            embed, attachements = event.get_embed_result_message()
            await message_embed.reply(embed=embed, files=attachements)
            logger.info("   ↳  ✅ Message résultat envoyé, suppression du message sur 'kc_id'.")
            await message.delete()
            
        logger.info("⇐ Traitement des résultats est terminé")

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


async def kc_list_annonce_publie()-> Optional[List[Dict[str, Any]]]:
    """Retourne une liste avec des dictionnaire des élément publié dans le channel kc_id 
    returns [{
     "id_event": 1234,
     "id_embed_message": 123456789
     "message": discord.Message
    },..]
    """
    channel = bot.get_channel(int(cfg['discord']['channels']['kc_id']))
    limit_message = int(cfg['discord'].get('limit_message',10))
    if not channel:
        return
    messages = [message async for message in channel.history(limit=limit_message)]
    list_message = []
    for message in messages:
        id_event, id_embed_message = kc.get_message_info(message.content)
        m = {"id_event":id_event,"id_embed_message":id_embed_message,"message":message}
        list_message.append(m)
    return list_message


bot.run(token, log_handler=None)
