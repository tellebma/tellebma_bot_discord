
import requests
from datetime import datetime, timezone, timedelta
from functions.image import generate_image_team_vs_team
import discord
import locale

# Définir la localisation en français
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

API_URL="https://www.lebluewall.fr/api/karmine/events"
def get_events():
    """
    Récupère la liste des matches
    """
    r = requests.get(API_URL)
    if r.status_code == 200:
        return r.json()
    return {}

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
    def __init__(self,json_object) -> None:
        self.date = datetime.fromisoformat(json_object.get("date").replace("Z", "+00:00")) + timedelta(minutes=5)
        self.competition_name = json_object.get("competition_name")
        self.team_domicile = json_object.get("team_domicile")
        self.team_exterieur = json_object.get("team_exterieur")
        self.out_dated = self.outdated()
        self.isToday = self.today()
        self.all = json_object

    def today(self)->bool:
        if str(self.date)[:10] == str(datetime.now(timezone.utc))[:10]:
            return True
        return False

    
    def outdated(self)->bool:
        if self.date < datetime.now(timezone.utc):
            return True
        return False

    def print(self)->None:
        print(f"{self.out_dated=} {self.isToday=} {self.date=}")
        print(f"Jeu: {self.competition_name}")
        print(f"T1: {self.team_domicile.get('name')}")
        print(f"T2: {self.team_exterieur.get('name','UnKnown')}")
    
    def get_embed_message(self)->str:
        format_date = self.date.strftime('%A %d %B %Hh%M').capitalize()

        embed=discord.Embed(title=self.competition_name, description=format_date, color=0x009dff)
        embed.set_author(name=f"{self.team_domicile.get('name')} vs {self.team_exterieur.get('name','N/A')}", icon_url=f"http://www.lebluewall.fr/_next/image?url=%2Fgames%2F{self.competition_name.lower()[3:]}.webp&w=48&q=75")
        output_name = f"{self.competition_name.lower()}_{self.team_domicile.get('name').lower()}_vs_{self.team_exterieur.get('name','unknow').lower()}.png"
        file_path = f"media/created/{output_name}"
        file_path = self.generate_image(file_path)
        attachment = discord.File(file_path, filename=output_name)
        embed.set_image(url=f"attachment://{output_name}")
        return embed, attachment


    def generate_image(self,output_name)->None:
        logo_a = check_logo(self.team_domicile.get('logo'))
        logo_b = check_logo(self.team_exterieur.get('logo'))
        file_path = generate_image_team_vs_team(logo_a, logo_b, output_name=output_name)
        return file_path

def check_logo(logo_url):
    if "http" not in logo_url:
        return "media/unknown.png"
    return logo_url