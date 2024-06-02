from functions.kc.config import BASE_URL
API_EVENT = f"{BASE_URL}/events"
API_RESULTS = f"{BASE_URL}/events_results"


import requests



def get_events():
    """
    Récupère la liste des matches
    """
    r = requests.get(API_EVENT)
    if r.status_code == 200:
        return r.json()
    return []

def get_id_event(id:bool) -> dict:
    events = get_events()
    return filtre_result(events, id)

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