import discord
import datetime
import yaml
import asyncio
import locale
import traceback
import logging
import pytz
import traceback
import json

from discord.ext import commands
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from typing import List, Dict, Any, Optional

from functions import kc
from functions.log import logger

# ~~~~~~~~
#  CONFIG
# ~~~~~~~~
with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

with open("version.yaml") as f:
    version_number = yaml.load(f, Loader=yaml.FullLoader)["version"]

token = cfg.get("token", False)
dev = cfg.get("dev", False)
scheduler = BackgroundScheduler(timezone='Europe/Paris')

if not token:
    logger.error("plz fill config.yaml file from config_template.yaml")
    exit()

MESSAGE_DEBUT_GAME = cfg["debut_game"]

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
    logger.info(f"Version of this bot {version_number}")
    logger.info(f'We have logged in as {bot.user}')  
    await send_error_message(error="",function="On READY", title="♻️ BOT RESTARTED")
    if bot.get_channel(int(cfg['discord']['channels']['kc'])):
        logger.info("✅ - Alert KC active")
        # notification
        
        scheduler.add_job(check_kc_result_embed_message, 'cron', id="check_results", hour='12,22', max_instances=1)
        scheduler.add_job(check_today_matches, 'cron', id="check_matchs", hour='8,12,20', max_instances=1)
        logger.info("✅ - Scheduler set up")
        l_jobs = scheduler.get_jobs()
        logger.info(f"Listes des jobs lancé: {l_jobs}")
        scheduler.start()
    
    if dev:
        logger.info("Dev mode active, launching process")
        await check_today_matches()
        await check_kc_result_embed_message()        


@bot.event
async def on_error(event, *args, **kwargs):
    # Handle all unhandled exceptions globally
    logging.error(traceback.format_exc())
    traceback.print_exc()
    
    await send_error_message(traceback.format_exc(), function="on_error")

# ~~~~~~~~~
#  Commandes
# ~~~~~~~~~

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


@bot.command(name='version', help='Affiche la version actuel du bot.')
async def version(ctx):
    await ctx.message.delete()
    await ctx.send(f'Le bot est en version {version_number}\nhttps://github.com/tellebma/tellebma_bot_discord/releases', delete_after=120)

@bot.command(name='liste_kc', help='Retourne la liste des éléments dans le fichier kc_id_match.json.')
@commands.has_role(int(cfg['discord']['roles']['kc']))
async def liste_kc(ctx):
    await ctx.message.delete()
    try:
        with open("kc_id_match.json", "r") as file:
            data = json.load(file)
        
        if not data:
            await ctx.send("La liste des éléments est vide.", delete_after=120)
            return
        
        message = "Liste des éléments dans kc_id_match.json:\n"
        table_header = "| ID Événement | ID Embed Message | Titre |\n"
        table_header += "|--------------|------------------|-------|\n"
        
        table_rows = ""
        for item in data:
            table_rows += f"| {item['id_event']} | {item['id_embed_message']} | {item['title']} |\n"
        
        message += table_header + table_rows
        
        # Discord has a message limit of 2000 characters, so we may need to split the message
        if len(message) > 2000:
            await ctx.send("Le message est trop long pour être affiché en une seule fois. Veuillez vérifier le fichier kc_id_match.json.", delete_after=120)
        else:
            await ctx.send(f"```\n{message}\n```", delete_after=120)
        
    except FileNotFoundError:
        await ctx.send("Le fichier kc_id_match.json n'a pas été trouvé.", delete_after=120)
    except Exception as e:
        logging.error("Error in liste_kc command", exc_info=e)
        await ctx.send("Une erreur s'est produite lors de la lecture du fichier.", delete_after=120)


@bot.command(name='remove_match_id', help='Supprime un id de la liste kc')
@commands.has_role(int(cfg['discord']['roles']['kc']))
async def remove_match_id(ctx, id_match: int):
    await ctx.message.delete()
    remove_kc_id_match_json(id_match)

# ~~~~~~~~~
#  Fonctions
# ~~~~~~~~~

async def check_today_matches():
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    # Fonction start:
    events = kc.get_today_events()
    logger.info(f"{len(events)} a traiter auj.")
    messages_list = kc_list_annonce_publie()
    events_id_published = [m.get("id_event") for m in messages_list]
    
    logger.debug(f"check_today_matches, {events_id_published=}")
    for event in events:
        if event.id in events_id_published:
            # Si l'annonce est déjà prévu ou déjà envoyé skip
            continue
        # ajout d'une loop pour chaque event.
        logger.info(f"Annonce: {event.id=} - {event.title=}")
        target_time_message_event = event.start - datetime.timedelta(hours=2)
        now = kc.update_timezone(datetime.datetime.now(), pytz.timezone(cfg.get("timezone", "Europe/Paris")), timezone_dest_str=cfg.get("timezone", "Europe/Paris"))
        
        if target_time_message_event > now:
            # on publi l'annonce dans 2h
            logger.info(f"   ↳  Annonce kc programmé à {str(target_time_message_event.hour).zfill(2)}h{str(target_time_message_event.minute).zfill(2)}")
        else:
            # On a loupé les 2heures de com
            target_time_message_event = now
            logger.info(f"   ↳  Annonce kc à envoyer dès mnt {str(target_time_message_event.hour).zfill(2)}h{str(target_time_message_event.minute).zfill(2)}")
        
        trigger = DateTrigger(run_date=target_time_message_event, timezone=pytz.timezone(cfg['timezone']))
        scheduler.add_job(send_kc_event_embed_message, trigger, args=[event,])
        
        target_time_message_stream = event.start - datetime.timedelta(minutes=5)
        trigger = DateTrigger(run_date=target_time_message_stream, timezone=pytz.timezone(cfg['timezone']))
        scheduler.add_job(send_kc_twitch_link_message, trigger, args=[event,])

        logger.info(f"       ↳  Message stream sera envoyé à {str(target_time_message_stream.hour).zfill(2)}h{str(target_time_message_stream.minute).zfill(2)}")


async def send_kc_twitch_link_message(event):
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    logger.info(f"⇒ Message stream twitch ! {event.id=} - {event.title=}")
    
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

    messages_list = kc_list_annonce_publie()
    logger.info(f"⇒ Annonce avec le lien du stream  ! {event.id=} - {event.title=}")
    for message_el in messages_list:
        id_event = message_el.get("id_event")
        id_embed_message =  message_el.get("id_embed_message")

        if not id_event or not id_embed_message:
            continue

        logger.info(f"   ↳  ✅ Message stream envoyé !")
        return
    
    logger.error("❌ Message stream erreur (message not found)")
    
    
async def send_kc_event_embed_message(event):
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    # Fonction start
    logger.info(f"⇒ C'est l'heure de l'annonce ! {event.id=} - {event.title=}")
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
        if not channel:
            logger.error("❌ Channel KC not found")
            return
        embed_message = await channel.send(embed=embed, files=attachements)
        
        # Update the JSON file with the new event
        update_kc_id_match_json(event.id, embed_message.id, title=event.title)
        logger.info("   ↳  ✅ Message sur channel kc envoyé et mis à jour dans le fichier JSON")
 
    except Exception as e:
        logging.error("❌ error (send_kc_event_embed_message)", exc_info=e)
        await send_error_message(traceback.format_exc(), function="send_kc_event_embed_message")

    logger.info("⇐ Fonction annonce ")
    # remove embed message
    # new message début game
    # afficher les résultats


async def check_kc_result_embed_message():
    """Envoyer un message à une heure précise"""
    await bot.wait_until_ready()
    try:
        logger.info("⇒ Verification des résultats des match KC")
        messages_list = kc_list_annonce_publie()
        if messages_list:
            result_json = kc.get_result()
        for message_el in messages_list:
            id_event = message_el.get("id_event")
            id_embed_message = message_el.get("id_embed_message")

            if not id_event or not id_embed_message:
                continue

            result = kc.filtre_result(result_json, id_event)
            logger.info(f"Resultats: {id_event=} {id_embed_message=}")
            if not result:
                logger.info("   ↳  ⏳ pas encore les résultats")
                continue

            event = kc.Event(result, ended=True)
            logger.info(f"   ↳  ✅ Annonce terminé: {event.title}")
            channel = bot.get_channel(int(cfg['discord']['channels']['kc']))
            logger.info(f"{id_embed_message=}")
            message_embed = False
            try:
                message_embed = await channel.fetch_message(int(id_embed_message))
            except discord.errors.NotFound as e: 
                logger.warning("   ↳  🟠 Le message n'a pas été trouvé")

            if not message_embed:
                logger.warning("       ↳  ❌ Le message n'a pas été trouvé")
                remove_kc_id_match_json(id_event)
                continue
            
            logger.info("   ↳  ✅ Le message a bien été trouvé, génération du message")
            embed, attachements = event.get_embed_result_message()
            await message_embed.reply(embed=embed, files=attachements)
            logger.info("   ↳  ✅ Message résultat envoyé, suppression de l'entrée dans le fichier JSON.")
            
            # Remove the entry from the JSON file
            remove_kc_id_match_json(id_event)
            
        logger.info("⇐ Traitement des résultats est terminé")

    except Exception as e:
        logging.error("error (check_kc_result_embed_message, {e})", exc_info=e)
        await send_error_message(traceback.format_exc(), function="check_kc_result_embed_message")
    # remove embed message
    # new message début game
    # afficher les résultats


async def send_error_message(error ,function="", title="❌ ERROR HANDLER"):
    
    channel = bot.get_channel(int(cfg['discord']['channels']['error']))
    date = datetime.datetime.now().strftime('%A %d %B %Hh%M').capitalize()
    embed = discord.Embed(title=f"{title} {function}",
                          description=date,
                          color=0xFF0000)
    embed.add_field(name="",
                    value="",
                    inline=True)
    if error:
        embed.add_field(name=f"An unexpected error occurred ",
                    value=f"{error}", inline=True)
    await channel.send(embed=embed)


def kc_list_annonce_publie() -> Optional[List[Dict[str, Any]]]:
    """Retourne une liste avec des dictionnaire des élément publié dans le fichier JSON 
    returns [{
     "id_event": 1234,
     "id_embed_message": 123456789
    },..]
    """
    try:
        with open(cfg["kc"]["file_id_temp"], "r") as file:
            list_message = json.loads(file.read())
        
        logging.info(f"Messages in kc_list_annonce_publie => {list_message}")
        return list_message

    except FileNotFoundError:
        logging.warning("kc_id_match.json not found. Returning empty list.")
        return []
    except Exception as e:
        logging.error("Error in kc_list_annonce_publie", exc_info=e)
        return []


def update_kc_id_match_json(id_event: int, id_embed_message: int, title: str = "Null"):
    """Mise à jour du fichier JSON avec un nouvel événement."""
    try:
        messages_list = kc_list_annonce_publie()
        messages_list.append({"id_event": id_event, "id_embed_message": id_embed_message, "title": title})
        
        with open(cfg["kc"]["file_id_temp"], "w") as file:
            json.dump(messages_list, file)
        
        logger.info(f"Updated kc_id_match.json with event {id_event} and embed message {id_embed_message}")

    except Exception as e:
        logging.error("Error in update_kc_id_match_json", exc_info=e)


def remove_kc_id_match_json(id_event: int):
    """Suppression d'un événement du fichier JSON."""
    try:
        messages_list = kc_list_annonce_publie()
        messages_list = [m for m in messages_list if m["id_event"] != id_event]
        
        with open(cfg["kc"]["file_id_temp"], "w") as file:
            json.dump(messages_list, file)
        
        logger.info(f"Removed event {id_event} from kc_id_match.json")

    except Exception as e:
        logging.error("Error in remove_kc_id_match_json", exc_info=e)


if __name__ == '__main__':
    bot.run(token, log_handler=None)
