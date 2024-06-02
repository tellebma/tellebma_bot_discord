from functions.kc.enum import GameMode, Mode
from functions.kc.image import generate_image_team, generate_image_team_vs_team, edit_image_add_score

from datetime import datetime, timedelta
import discord
import pytz
import re

from functions.kc.config import TIMEZONE_STR
from functions.kc.api import filtre_result, get_events, get_id_event, get_result
from functions.kc.functions import update_timezone, filtre_player, extract_teamname, extract_around_vs, get_message_info
from functions.kc.media import get_game_str, get_game_color, get_game_img, check_logo
from functions.log import logger



def get_today_events() -> list:
    """
    Récupère exclusivement la liste des matches du jours et qui on pas encore commencé.
    """
    
    events = get_events()
    today_events = []
    for event in events:
        e = Event(event)
        if e.today() and not e.outdated():
            today_events.append(e)
    return today_events

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
        return self.start.date() == now.date()

    def outdated(self) -> bool:
        now = datetime.now(pytz.timezone(TIMEZONE_STR))
        return self.start < now

    def get_short_team(self, title_string) -> tuple[str, str]:
        teamA, teamB = extract_around_vs(title_string)
        return teamA, teamB

    def get_full_team(self, logo_url) -> str:
        return extract_teamname(logo_url, self.competition_name)

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
        attachments.append(discord.File("media/KC_default.jpg", filename="annonce.jpg"))
        embed.set_author(name=f"{self.message}",
                         icon_url="attachment://annonce.jpg")
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
        output_name = f"{self.competition_name_initial}_{self.message}.png".lower().replace(' ', '_').replace('[', '').replace(']', '').replace(",","")
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


