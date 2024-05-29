from enum import Enum

class GameMode(Enum):
    LEAGUE_OF_LEGENDS = "LeagueOfLegends"
    LEAGUE_OF_LEGENDS_LEC = "LeagueOfLegendsLEC"
    LEAGUE_OF_LEGENDS_LFL = "LeagueOfLegendsLFL"
    FORTNITE = "Fortnite"
    VALORANT = "Valorant"
    VALORANT_VCT_GC = "ValorantVCT_GC"
    VALORANT_VCT = "ValorantVCT"
    TFT = "TFT"
    ROCKET_LEAGUE = "RocketLeague"

class Mode(Enum):
    PLAYER = "Player"
    TEAM = "Team"
    MATCH = "Match"