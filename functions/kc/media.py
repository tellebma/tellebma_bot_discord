from functions.kc.enum import GameMode
import random


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
        return "media/" + random.choice(["Takken.png", "Street_Fighter_6.png"]) 
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