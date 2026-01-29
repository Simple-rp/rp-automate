# FiveM Focus Bot

Bot Windows minimal pour FiveM :
- met la fenêtre FiveM devant,
- envoie X → G → Tab → clic sur l’image `items/ble.png` (moitié gauche de la fenêtre) → Tab → E,
- boucle toutes les `FIVEM_BOT_INTERVAL` secondes (120s par défaut).

## Démarrage rapide
```powershell
cd e:\Workspaces\fivem-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python fivem_focus_bot.py
```

Conseils : lance le bot au même niveau d’admin que FiveM ; remplace `items/ble.png` si besoin ; ajuste `FIVEM_BOT_INTERVAL` si tu veux plus/moins souvent.
