from functions.enum import GameMode, Mode
from functions.image import generate_image_team, generate_image_team_vs_team

from datetime import datetime,timedelta
import discord
import requests
import pytz
import yaml
import re


with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

BASE_URL = cfg["kc_api_url"]
TIMEZONE_STR = cfg["timezone"]

API_EVENT = "{BASE_URL}/events"
API_RESULTS = "{BASE_URL}/events_results"
TIMEZONE_STR = "Europe/Paris"


def get_events():
    """
    Récupère la liste des matches
    """
    r = requests.get(API_EVENT)
    if r.status_code == 200:
        return r.json()
    return []

def get_result(id):
    r = requests.get(API_RESULTS)
    if r.status_code == 200:
        for i in r.json():
            if i.get("id") == id:
                return i
    return None

def extract_around_vs(text):
    # Définir le modèle regex pour capturer le texte autour de "vs"
    pattern = re.compile(r'\s(.*?)\s+vs\s+(.*)')
    
    # Chercher le modèle dans le texte donné
    match = pattern.search(text)
    
    if match:
        # Extraire les groupes capturés
        before_vs = match.group(1).strip()
        after_vs = match.group(2).strip()
        return before_vs, after_vs
    else:
        return None, None
    
def extract_teamname(logo_url, jeu):
    # Définir le modèle regex pour capturer le texte entre 'karmine/teams/' et le jeu spécifié
    pattern = re.compile(r'karmine/teams/(.*?)' + jeu)
    
    # Chercher le modèle dans l'URL donnée
    match = pattern.search(logo_url)
    
    if match:
        # Extraire le groupe capturé
        data = match.group(1).strip('-')
        return data
    else:
        if logo_url == "https://medias.kametotv.fr/karmine/teams_logo/KC.png":
            return "Karmine Corp"
        return None

def filtre_player(player_list_str:str)->list:
    return list(set(player_list_str.split(';')))
    
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

def get_game_color(gamemode: GameMode) -> str:
    default = 0x000000
    if gamemode == GameMode.LEAGUE_OF_LEGENDS_LEC:
        return 0x0064FF # Bleu Foncé
    elif gamemode == GameMode.LEAGUE_OF_LEGENDS_LFL:
        return 0x00FFF7 # Bleu claire
    elif gamemode == GameMode.LEAGUE_OF_LEGENDS:
        return 0xFFFFFF
    elif gamemode == GameMode.FORTNITE:
        return 0xBF00EE # rose
    elif gamemode == GameMode.VALORANT_VCT_GC:
        return 0x8500EE # violet
    elif gamemode == GameMode.VALORANT_VCT:
        return 0xEE5700 # rouge
    elif gamemode == GameMode.VALORANT:
        return 0xFFFFFF
    elif gamemode == GameMode.TFT:
        return 0xFFB200 # doré
    elif gamemode == GameMode.ROCKET_LEAGUE:
        return 0x00B226 # vert
    return default

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


class Team:
    def __init__(self, name, short, logo_url) -> None:
        self.name = name
        self.short = short
        self.logo = logo_url
    
    def __str__(self) -> str:
        if not self.name:
            return f"{self.short}"
        return f"[{self.short}] {self.name}"

class Event:
    def __init__(self, json_object) -> None:
        self.id = json_object.get("id")
        self.json_object = json_object
        self.competition_name = json_object.get("competition_name")
        self.competition_name_enum = GameMode(self.competition_name)
        self.competition_name_initial = json_object.get("initial")
        self.stream = "https://twitch.tv/" + json_object.get("streamLink","chokolaolais")
        self.link_competition = json_object.get("link")        
        self.start = update_timezone(datetime.fromisoformat(json_object.get("start").replace("Z", "+00:00")) + timedelta(minutes=5),
                                    timezone_base=pytz.utc,
                                    timezone_dest_str=TIMEZONE_STR)
        self.end = update_timezone(datetime.fromisoformat(json_object.get("end").replace("Z", "+00:00")) + timedelta(minutes=5),
                                    timezone_base=pytz.utc,
                                    timezone_dest_str=TIMEZONE_STR)
        self.ended = False
        td = None if json_object.get("team_domicile") == "null" else json_object.get("team_domicile", None)
        te = None if json_object.get("team_exterieur") == "null" else json_object.get("team_exterieur", None)
        if not td:    
            # Cas TFT (P-e aussi Fortnite, a voir)
            # TFT, FTN ?
            self.mode = Mode("Player")
            self.player = filtre_player(json_object.get("player"))
            self.message = f"{', '.join(self.player)}"
            self.logo = "https://medias.kametotv.fr/karmine/teams_logo/KC.png"
            self.description = f"{self.message} {'jouera' if self.player > 2 else 'joueront'} à {self.start.hour}h !"


        elif not te:
            # alors ?
            self.mode = Mode("Team")
            short_teamA, dummy = self.get_short_team(json_object.get("title"))
            logoA = td
            self.team = Team(self.get_full_team(logoA),short_teamA,logoA)
            self.message = f"{self.team.full}"
            self.description = f"L'équipe {self.team.full} ({get_game_str(self.competition_name_enum)}) jouera à {self.start.hour}h !"
            
        else:
            # cas equipe contre équipe
            self.mode = Mode("Match")
            short_teamA, short_teamB = self.get_short_team(json_object.get("title"))
            logoA = td
            logoB = te
            self.team_domicile = Team(self.get_full_team(logoA),short_teamA,logoA)
            self.team_exterieur = Team(self.get_full_team(logoB),short_teamB,logoB)
            self.message = f"{self.team_domicile} vs {self.team_exterieur}"
            self.description = f"{self.team_domicile.full} vs {self.team_exterieur.full} ({get_game_str(self.competition_name_enum)}) ce sera à {self.start.hour}h !"
        format_date = self.start.strftime('%A %d %B %Hh%M').capitalize()
        self.title = f"[{self.competition_name_initial}] - {self.message} - {format_date}"
        

    def __str__(self) -> str:
        return f'[{self.id}] [{self.competition_name_initial}] - {self.message} - {self.start.strftime("%d/%m/%y")}'
    
    
    def get_short_team(self, title_string)->tuple[str, str]:
        teamA, teamB = extract_around_vs(title_string)
        return teamA, teamB
        
    def get_full_team(self, logo_url)->str:
        return extract_teamname(logo_url, self.competition_name)
        

    def today(self)->bool:
        now = datetime.now(pytz.timezone(TIMEZONE_STR))
        return self.start.date() == now.date()

    
    def outdated(self)->bool:
        now = datetime.now(pytz.timezone(TIMEZONE_STR))
        return self.start < now
    
    def get_embed_message(self)->tuple:
        attachments = []
        
        # basic info 
        #  gamemode
        #  date
        embed=discord.Embed(title=self.title, 
                            description=self.description, 
                            color=get_game_color(self.competition_name_enum),
                            timestamp=self.start)
        #  author 
        attachments.append(discord.File("media/KC_default.jpg", filename="KC_default.jpg"))
        embed.set_author(name=f"{self.event_name}", 
                         icon_url=f"attachment://KC_default.jpg")
        #  footer
        attachments.append(discord.File("media/bluewall.jpg", filename="bluewall.jpg"))
        embed.set_footer(text="Fin du match", icon_url=f"attachment://bluewall.jpg")
        
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
        if self.mode == Mode.MATCH:    
            logo_a = check_logo(self.team_domicile.get('logo'))
            logo_b = check_logo(self.team_exterieur.get('logo'))
            file_path = generate_image_team_vs_team(logo_a, logo_b, output_name=output_name)
            return file_path
        elif self.mode == Mode.PLAYER:
            return generate_image_team(self.logo, ', '.join(self.player), len(self.player), output_name=output_name)
        return generate_image_team(self.team.logo, self.team.name, 1, output_name=output_name)

    

def get_message_info(message):
    """
    Dans le channel KC_id on recup chaque message et cette fonction permet de dire si un message est conforme ou non.
    """
    pattern = re.compile(r'\[(.*?)\]\s(.*)')
    
    # Chercher le modèle dans le texte donné
    match = pattern.search(message)
    
    if match:
        # Extraire les groupes capturés
        id_event = match.group(1).strip()
        id_message = match.group(2).strip()
        return id_event, id_message
    return None, None