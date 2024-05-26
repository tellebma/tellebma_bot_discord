import requests
from datetime import datetime, timezone, timedelta
import discord
import pytz
import yaml

from functions.image import generate_image_team_vs_team
from functions.enum import GameMode

with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

API_URL = cfg["kc_api_url"]
TIMEZONE_STR = cfg["timezone"]

def get_events():
    """
    Récupère la liste des matches
    """
    r = requests.get(API_URL)
    if r.status_code == 200:
        return r.json()
    return []

def get_today_events()->list:
    """
    Récupère exclusivement la liste des matches du jours
    """
    events = get_events()
    today_events = []
    for event in events:
        e = Event(event)
        if e.isToday and not e.out_dated:
            today_events.append(e)
    return today_events

class Event:
    def __init__(self, json_object) -> None:
        self.all = json_object
        
        self.date = update_timezone(datetime.fromisoformat(json_object.get("date").replace("Z", "+00:00")) + timedelta(minutes=5),
                                    timezone_base=pytz.utc,
                                    timezone_dest_str=TIMEZONE_STR)
        
        self.competition_name = json_object.get("competition_name")
        self.gamemode = GameMode(self.competition_name)

        self.team_domicile = json_object.get("team_domicile")
        self.team_exterieur = json_object.get("team_exterieur")
                
        self.out_dated = self.outdated()
        self.isToday = self.today()
        
        self.event_name = f"{self.team_domicile.get('name')} vs {self.team_exterieur.get('name','unknown')}"
        self.gamemode_str = get_game_str(self.gamemode)
        self.__str__ = self.gamemode_str + "_" + self.event_name.relpace(" ","_")

    def today(self)->bool:
        now = datetime.now(pytz.timezone(TIMEZONE_STR))
        return self.date.date() == now.date()

    
    def outdated(self)->bool:
        now = datetime.now(pytz.timezone(TIMEZONE_STR))
        return self.date < now
    
    def get_embed_message(self)->tuple:
        attachments = []
        format_date = self.date.strftime('%A %d %B %Hh%M').capitalize()
        # basic info 
        #  gamemode
        #  date
        embed=discord.Embed(title=self.gamemode_str, 
                            description=format_date, 
                            color=0x009dff,
                            timestamp=datetime.now())
        #  author 
        attachments.append(discord.File("media/KC_default.jpg", filename="KC_default.jpg"))
        embed.set_author(name=f"{self.event_name}", 
                         icon_url=f"attachment://KC_default.jpg")
        #  footer
        attachments.append(discord.File("media/bluewall.jpg", filename="bluewall.jpg"))
        embed.set_footer(text="KC event", icon_url=f"attachment://bluewall.jpg")
        
        #  Gamemode image
        gamemode_file_image = get_game_img(self.gamemode)
        gamemode_filename_image = gamemode_file_image.replace("media/","")
        attachments.append(discord.File(gamemode_file_image, filename=gamemode_filename_image))
        embed.set_thumbnail(url=f"attachment://{gamemode_filename_image}")
        
        #  Image VS
        output_name = f"{self.competition_name}_{self.event_name.replace(' ','_')}.png".lower()
        file_path = f"media/created/{output_name}"
        file_path = self.generate_image(file_path)
        attachments.append(discord.File(file_path, filename=output_name))
        embed.set_image(url=f"attachment://{output_name}")

        return embed, attachments


    def generate_image(self, output_name:str)->str:
        logo_a = check_logo(self.team_domicile.get('logo'))
        logo_b = check_logo(self.team_exterieur.get('logo'))
        file_path = generate_image_team_vs_team(logo_a, logo_b, output_name=output_name)
        return file_path

def check_logo(logo_url:str)->str:
    if "http" not in logo_url:
        return "media/unknown.png"
    return logo_url

def update_timezone(datetime_object:datetime, timezone_base=pytz.utc, timezone_dest_str:str="Europe/Paris")->datetime:
    if datetime_object.tzinfo is None:
        # Si naïf, localisez-le au fuseau horaire de base
        datetime_object = timezone_base.localize(datetime_object)
    
    timezone_dest = pytz.timezone(timezone_dest_str)
    return datetime_object.astimezone(timezone_dest)

def get_game_img(gamemode: GameMode) -> str:
    default = "media/KC_default.jpg"
    if gamemode == GameMode.LEAGUE_OF_LEGENDS_LEC:
        return "media/LEC.png"
    elif gamemode == GameMode.LEAGUE_OF_LEGENDS_LFL:
        return "media/LFL.png"
    elif gamemode == GameMode.LEAGUE_OF_LEGENDS:
        return "media/LOL.png"
    elif gamemode == GameMode.FORTNITE:
        return "media/Fortnite.png"
    elif gamemode == GameMode.VALORANT_VCT_GC:
        return "media/Valorant_GC.png"
    elif gamemode == GameMode.VALORANT_VCT:
        return "media/ValorantVCT.png"
    elif gamemode == GameMode.VALORANT:
        return "media/Valorant.png"
    elif gamemode == GameMode.TFT:
        return "media/TFT.png"
    elif gamemode == GameMode.ROCKET_LEAGUE:
        return "media/RL.png"
    return default

def get_game_str(gamemode: GameMode) -> str:
    default = "C'est maintenant !"
    if gamemode == GameMode.LEAGUE_OF_LEGENDS_LEC:
        return "LEC"
    elif gamemode == GameMode.LEAGUE_OF_LEGENDS_LFL:
        return "LFL"
    elif gamemode == GameMode.LEAGUE_OF_LEGENDS:
        return "League Of Legends"
    elif gamemode == GameMode.FORTNITE:
        return "Fortnite"
    elif gamemode == GameMode.VALORANT_VCT_GC:
        return "Valorant VCT GC"
    elif gamemode == GameMode.VALORANT_VCT:
        return "Valorant VCT"
    elif gamemode == GameMode.VALORANT:
        return "Valorant"
    elif gamemode == GameMode.TFT:
        return "TFT"
    elif gamemode == GameMode.ROCKET_LEAGUE:
        return "RocketLeague"
    return default