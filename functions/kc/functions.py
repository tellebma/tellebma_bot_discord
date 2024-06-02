import re
import pytz
from datetime import datetime
from typing import Tuple, Optional

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



def update_timezone(datetime_object: datetime,
                    timezone_base=pytz.utc,
                    timezone_dest_str: str = "Europe/Paris") -> datetime:
    if datetime_object.tzinfo is None:
        # Si naïf, localisez-le au fuseau horaire de base
        datetime_object = timezone_base.localize(datetime_object)

    timezone_dest = pytz.timezone(timezone_dest_str)
    return datetime_object.astimezone(timezone_dest)


def get_message_info(message)->Tuple[Optional[int], Optional[int]]:
    """
    Dans le channel KC_id on recup chaque message et cette fonction permet 
      de dire si un message est conforme ou non.
    """
    pattern = re.compile(r'\[(.*?)\]\s-\s(.*)')

    # Chercher le modèle dans le texte donné
    match = pattern.search(message)

    if match:
        try:
            # Extraire les groupes capturés et les convertir en int
            id_event = int(match.group(1).strip())
            id_message = int(match.group(2).strip())
            return id_event, id_message
        except ValueError:
            # Gestion des erreurs de conversion en int
            return None, None
    return None, None
