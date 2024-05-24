from PIL import Image
from io import BytesIO
import requests

def open_image_from_url(url):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content)).convert("RGBA")
    return image

def generate_image_team_vs_team(img_a, img_b, vs_logo="media/vs_logo.png", output_name="media/created/result_image.png"):
    # Charger les images
    if "http" in img_a:
        team_a_logo = open_image_from_url(img_a)
    else:
        team_a_logo = Image.open(img_a)

    if "http" in img_b:
        team_b_logo = open_image_from_url(img_b)
    else:
        team_b_logo = Image.open(img_b)
    
    vs_logo = Image.open(vs_logo)

    # Redimensionner les images pour s'assurer qu'elles ont des tailles cohérentes
    team_a_logo = team_a_logo.resize((220, 220), Image.Resampling.LANCZOS)
    team_b_logo = team_b_logo.resize((220, 220), Image.Resampling.LANCZOS)
    vs_logo = vs_logo.resize((140, 120), Image.Resampling.LANCZOS)

    # Calculer la taille de l'image finale
    width = team_a_logo.width + vs_logo.width + team_b_logo.width + 40  # Espacement de 20px de chaque côté du "VS"
    height = max(team_a_logo.height, vs_logo.height, team_b_logo.height)

    # Créer une nouvelle image avec un fond blanc
    result_image = Image.new('RGBA', (width, height), (255, 255, 255, 0))

    # Positionner les images
    result_image.paste(team_a_logo, (0, (height - team_a_logo.height) // 2), team_a_logo)
    result_image.paste(vs_logo, ((team_a_logo.width + 20), (height - vs_logo.height) // 2), vs_logo)
    result_image.paste(team_b_logo, (team_a_logo.width + vs_logo.width + 40, (height - team_b_logo.height) // 2), team_b_logo)


    # Sauvegarder l'image finale
    result_image.save(output_name)
    return output_name
    
