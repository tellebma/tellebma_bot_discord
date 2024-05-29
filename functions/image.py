from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests

def open_image_from_url(url)->Image.Image:
    response = requests.get(url)
    image = Image.open(BytesIO(response.content)).convert("RGBA")
    return image

def generate_image_team_vs_team(img_a, img_b, vs_logo="media/vs_logo.png", output_name="media/created/result_image.png")->str:
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

def generate_image_team(img_a, text, num_player=1, output_name="media/created/result_image.png")->str:
    # Charger les images
    if "http" in img_a:
        team_a_logo = open_image_from_url(img_a)
    else:
        team_a_logo = Image.open(img_a)
    
    # Redimensionner les images pour s'assurer qu'elles ont des tailles cohérentes
    team_a_logo = team_a_logo.resize((220, 220), Image.Resampling.LANCZOS)
    
    # Calculer la taille de l'image finale
    width = team_a_logo.width + 100  # Espacement de 20px de chaque côté du "VS"
    height = team_a_logo.height + 50

    # Créer une nouvelle image avec un fond blanc
    result_image = Image.new('RGBA', (width, height), (255, 255, 255, 0))

    # Positionner le logo au centre
    result_image.paste(team_a_logo, ((width - team_a_logo.width) // 2, (height - team_a_logo.height) // 2 - 30))

    # Ajouter du texte en dessous du logo
    draw = ImageDraw.Draw(result_image)
    font = ImageFont.truetype("media\Oswald-SemiBold.ttf", 40 // num_player)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    text_position = ((width - text_width) // 2, height - text_height - 50)  # Positionner le texte en bas et au centre
    draw.text(text_position, text, fill=(255, 255, 255), font=font)

    # Sauvegarder l'image finale
    result_image.save(output_name)
    return output_name

