from functions.enum import GameMode, Mode
from functions.image import generate_image_team, generate_image_team_vs_team, edit_image_add_score

from datetime import datetime, timedelta
import discord
import requests
import pytz
import yaml
import re
import random

with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

BASE_URL = cfg["kc_api_url"]
TIMEZONE_STR = cfg["timezone"]

API_EVENT = f"{BASE_URL}/events"
API_RESULTS = f"{BASE_URL}/events_results"
print(API_RESULTS)
TIMEZONE_STR = "Europe/Paris"


def get_events():
    """
    Récupère la liste des matches
    """
    r = requests.get(API_EVENT)
    if r.status_code == 200:
        return r.json()
    return []


def get_today_events() -> list:
    """
    Récupère exclusivement la liste des matches du jours
    """
    events = get_events()
    today_events = []
    for event in events:
        e = Event(event)
        if e.today() and not e.outdated():
            today_events.append(e)
    return today_events


def get_result():
    r = requests.get(API_RESULTS)
    if r.status_code == 200:
        return r.json()
    return []


def filtre_result(json: list, id: int):
    for i in json:
        if int(i.get("id", 0)) == int(id):
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
        pattern = re.compile(r'karmine/teams/(.*?).png')
        match = pattern.search(logo_url)
        if match:
            return match.group(1).strip('-')

        if logo_url == "https://medias.kametotv.fr/karmine/teams_logo/KC.png":
            return "Karmine Corp"
        return None


def filtre_player(player_list_str: str) -> list:
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
    elif gamemode == GameMode.TAKKENSTREETFIGHTER:
        return "media/" + random.choice("Takken.png", "Street_Fighter_6.png") 
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
    elif gamemode == GameMode.TAKKENSTREETFIGHTER:
        return "Takken & Street Fighter"
    return default


def get_game_color(gamemode: GameMode) -> str:
    default = 0x000000
    if gamemode == GameMode.LEAGUE_OF_LEGENDS_LEC:
        return 0x0064FF  # Bleu Foncé
    elif gamemode == GameMode.LEAGUE_OF_LEGENDS_LFL:
        return 0x00FFF7  # Bleu claire
    elif gamemode == GameMode.LEAGUE_OF_LEGENDS:
        return 0xFFFFFF
    elif gamemode == GameMode.FORTNITE:
        return 0xBF00EE  # rose
    elif gamemode == GameMode.VALORANT_VCT_GC:
        return 0x8500EE  # violet
    elif gamemode == GameMode.VALORANT_VCT:
        return 0xEE5700  # rouge
    elif gamemode == GameMode.VALORANT:
        return 0xFFFFFF
    elif gamemode == GameMode.TFT:
        return 0xFFB200  # doré
    elif gamemode == GameMode.ROCKET_LEAGUE:
        return 0x00B226  # vert
    elif gamemode == GameMode.TAKKENSTREETFIGHTER:
        return 0xED7F10  # orange
    return default


def check_logo(logo_url: str) -> str:
    if "http" not in logo_url:
        return "media/unknown.png"
    return logo_url


def update_timezone(datetime_object: datetime,
                    timezone_base=pytz.utc,
                    timezone_dest_str: str = "Europe/Paris") -> datetime:
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
    def __init__(self, json_object, ended=False) -> None:
        self.id = json_object.get("id")
        self.json_object = json_object
        self.competition_name = json_object.get("competition_name")
        self.competition_name_enum = GameMode(self.competition_name)
        self.competition_name_initial = json_object.get("initial")
        self.link_competition = json_object.get("link")
        date_string = json_object.get("start").replace("Z", "+00:00")
        self.start = update_timezone(datetime.fromisoformat(date_string) +
                                     timedelta(minutes=5),
                                     timezone_base=pytz.utc,
                                     timezone_dest_str=TIMEZONE_STR)
        self.ended = ended
        if not ended:
            self.stream = "https://twitch.tv/" + json_object.get("streamLink",
                                                                 "chokolaolais"
                                                                 )
            date_string = json_object.get("end").replace("Z", "+00:00")
            self.end = update_timezone(datetime.fromisoformat(date_string) +
                                       timedelta(minutes=5),
                                       timezone_base=pytz.utc,
                                       timezone_dest_str=TIMEZONE_STR)
        if self.ended:
            self.score_color = json_object.get("color")  # "#75c93d"
            self.score_domicile = json_object.get("score_domicile")
            self.score_exterieur = json_object.get("score_exterieur")   
            if "TOP" in self.score_domicile or \
               "WIN" in self.score_domicile or \
               "LOSE" in self.score_domicile:
                self.score = self.score_domicile
            else:
                self.score = f"{self.score_domicile} - {self.score_exterieur}"

        td = None if json_object.get("team_domicile") == "null" else json_object.get("team_domicile", None)
        te = None if json_object.get("team_exterieur") == "null" else json_object.get("team_exterieur", None)
        if not td:  
            # Cas TFT (P-e aussi Fortnite, a voir)
            # TFT, FTN ?
            self.mode = Mode("Player")
            self.player = filtre_player(json_object.get("player"))
            self.message = f"{', '.join(self.player)}"
            self.logo = "media/Karmine_Corp.png"
            if not self.ended:
                self.description = f"{self.message} {'jouera' if len(self.player) > 2 else 'joueront'} à {self.start.hour}h !"
            else:
                self.description = f"{self.message} à {self.score}"

        elif not te:
            # alors ?
            self.mode = Mode("Team")
            short_teamA, dummy = self.get_short_team(json_object.get("title"))
            logoA = td.replace('///medias', '//medias')
            self.team = Team(self.get_full_team(logoA), short_teamA, logoA)
            self.message = f"{self.team.name}"
            if not self.ended:
                self.description = f"L'équipe {self.team.name} ({get_game_str(self.competition_name_enum)}) jouera à {self.start.hour}h !"
            else:
                self.description = f"L'équipe {self.team.name} à {self.score}!"
        else:
            # cas equipe contre équipe
            self.mode = Mode("Match")
            short_teamA, short_teamB = self.get_short_team(json_object.get("title"))
            logoA = td.replace('///medias', '//medias')
            logoB = te.replace('///medias', '//medias')
            self.team_domicile = Team(self.get_full_team(logoA), short_teamA, logoA)
            self.team_exterieur = Team(self.get_full_team(logoB), short_teamB, logoB)
            self.message = f"{self.team_domicile} vs {self.team_exterieur}"
            if not self.ended:
                self.description = f"{self.team_domicile} vs {self.team_exterieur} ({get_game_str(self.competition_name_enum)}) ce sera à {self.start.hour}h !"
            else:
                if self.score == "WIN":
                    self.score_translate = "Gagné"
                elif self.score == "LOSE":
                    self.score_translate = "Perdu"
                elif int(self.score_domicile) > int(self.score_exterieur):
                    self.score_translate = "Gagné"
                elif int(self.score_domicile) < int(self.score_exterieur):
                    self.score_translate = "Perdu"
                elif int(self.score_domicile) == int(self.score_exterieur):
                    self.score_translate = "fait égalité"
                else:
                    self.score_translate = self.score
                self.description = f"{self.team_domicile} à {self.score_translate} face à {self.team_exterieur}"

        format_date = self.start.strftime('%A %d %B %Hh%M').capitalize()
        self.title = f"[{self.competition_name_initial}] - {self.message} - {'Résultats !'if self.ended else f'{format_date}'}"

    def __str__(self) -> str:
        return f'[{self.id}] [{self.competition_name_initial}] - {self.message} - {self.start.strftime("%d/%m/%y")}'

    def today(self) -> bool:
        now = datetime.now(pytz.timezone(TIMEZONE_STR))
        return self.date.date() == now.date()

    def outdated(self) -> bool:
        now = datetime.now(pytz.timezone(TIMEZONE_STR))
        return self.date < now

    def get_short_team(self, title_string) -> tuple[str, str]:
        teamA, teamB = extract_around_vs(title_string)
        return teamA, teamB

    def get_full_team(self, logo_url) -> str:
        return extract_teamname(logo_url, self.competition_name)

    def today(self) -> bool:
        now = datetime.now(pytz.timezone(TIMEZONE_STR))
        return self.start.date() == now.date()

    def outdated(self) -> bool:
        now = datetime.now(pytz.timezone(TIMEZONE_STR))
        return self.start < now

    def base_embed_attachement_message(self) -> tuple:
        attachments = []
        # basic info
        #  gamemode
        #  date
        embed = discord.Embed(title=self.title,
                              description=self.description,
                              color=get_game_color(self.competition_name_enum),
                              timestamp=self.start)
        #  author
        attachments.append(discord.File("media/KC_default.jpg", filename="KC_default.jpg"))
        embed.set_author(name=f"{self.message}",
                         icon_url="attachment://KC_default.jpg")
        #  footer
        attachments.append(discord.File("media/bluewall.jpg",
                                        filename="bluewall.jpg"))
        embed.set_footer(text="Fin du match",
                         icon_url="attachment://bluewall.jpg")

        #  Gamemode image
        gamemode_file_image = get_game_img(self.competition_name_enum)
        gamemode_filename_image = gamemode_file_image.replace("media/", "")
        attachments.append(discord.File(gamemode_file_image,
                                        filename=gamemode_filename_image))
        embed.set_thumbnail(url=f"attachment://{gamemode_filename_image}")

        return embed, attachments

    def get_embed_result_message(self) -> tuple:
        embed, attachments = self.base_embed_attachement_message()

        #  Image Result
        output_name = f"{self.competition_name}_{self.message}.png".lower().replace(' ', '_').replace('[', '').replace(']', '')
        file_path = f"media/created/{output_name}"
        file_path = self.generate_image(file_path)

        new_output_name = file_path.replace('.png',
                                            "_result.png")
        file_path = edit_image_add_score(file_path, self.score, self.score_color, output_name=new_output_name)
        new_output_name = new_output_name.replace("media/created/", "")
        print(new_output_name)
        attachments.append(discord.File(file_path, filename=new_output_name))
        embed.set_image(url=f"attachment://{new_output_name}")

        return embed, attachments

    def get_embed_message(self) -> tuple:
        embed, attachments = self.base_embed_attachement_message()
        
        #  Image VS
        output_name = f"{self.competition_name}_{self.message}.png".lower().replace(' ', '_').replace('[', '').replace(']', '')
        file_path = f"media/created/{output_name}"
        file_path = self.generate_image(file_path)
        attachments.append(discord.File(file_path, filename=output_name))
        embed.set_image(url=f"attachment://{output_name}")

        return embed, attachments

    def generate_image(self, output_name: str) -> str:
        if self.mode == Mode.MATCH:   
            logo_a = check_logo(self.team_domicile.logo)
            logo_b = check_logo(self.team_exterieur.logo)
            file_path = generate_image_team_vs_team(logo_a, logo_b, output_name=output_name)
            return file_path
        elif self.mode == Mode.PLAYER:
            return generate_image_team(self.logo, ', '.join(self.player), len(self.player), output_name=output_name)
        return generate_image_team(self.team.logo, self.team.name, 1, output_name=output_name)


def get_message_info(message):
    """
    Dans le channel KC_id on recup chaque message et cette fonction permet 
      de dire si un message est conforme ou non.
    """
    pattern = re.compile(r'\[(.*?)\]\s-\s(.*)')

    # Chercher le modèle dans le texte donné
    match = pattern.search(message)

    if match:
        # Extraire les groupes capturés
        id_event = match.group(1).strip()
        id_message = match.group(2).strip()
        return id_event, id_message
    return None, None
