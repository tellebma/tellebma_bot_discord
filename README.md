# Discord BOT Python 
*Ce projet est pour un usage personel.*


## KC alerts
Le bot regarde les matchs a venir de la journée (check a 4h du matin) et envoie une notification dans un canal discord 2h avant l'heure du match.
![Screen Notification Event](/media/doc/screen_discord_match_alert.png)


Une seconde tache tourne tous les jours à `9,12,15,18,20,22`h et verifie si des résultats de match on été trouvé. 
en se basant sur un autre canal dans lequel ont été envoyé les Id des matchs il sait les notifs qu'il a déjà envoyé et celle a traiter. 
Voici le rendu du résultat:
![Screen Notification Event](/media/doc/screen_discord_match_result.png)

### Data
Les données proviennent de l'extension officiel de la karmine corp. je ne sais pas si c'est intentionnel ni si on a le droit de l'utiliser mais Merci a eux sinon ce serait pas possible. 
(big up au BlueWall qui utilise déjà ces données sur leur site)

### TODO
- [ ] Anti spoiler dans le embed text + image
- [ ] Vérifier si ca marche bien
- [ ] Enregistrer les images pour ne pas les télécharger 1000x 
- Verifier:
   - [ ] Fortnite
   - [ ] TFT
   - [ ] Valorant 

## NF
Un autre objectif serait de trouver des films a plus de 90% de rating présent sur mon serveur Jellyfin et de les publier dans un channel une fois par semaine. 
### TODO 
- [ ] All
- [ ] BDD ? local ? export xlsx ? connexion a un docker ? 

