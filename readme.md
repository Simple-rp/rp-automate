# FiveM Focus Bots

Scripts simples pour automatiser des actions repetitives dans FiveM.
Compatible avec le serveur: **Diamond City**.

## 1) Ce qu'il faut avant

- Windows
- FiveM installe et fonctionnel
- Python 3 installe

Si Python n'est pas installe: https://www.python.org/downloads/

## 2) Installation (a faire une seule fois)

Ouvre un terminal dans ce dossier, puis lance:

```powershell
pip install -r requirements.txt
```

## 3) Utilisation (au quotidien)

1. Lance FiveM et place ton personnage au bon endroit.
2. Double-clique sur `run.bat`.
3. Choisis le script dans la liste (tape le numero).
4. Pour arreter un script: `Ctrl + C`.

## Scripts disponibles

- `scripts/diamond/atom/recolte-ble.py`
- `scripts/diamond/atom/vente-pain.py`
- `scripts/diamond/ferme-cayo/recolte-pistache.py`
- `scripts/diamond/ferme-cayo/vente-pistache.py`
- `scripts/diamond/ferme-cayo/recolte-menth.py`
- `scripts/diamond/ferme-cayo/recolte-pierre.py`

## Changer la vitesse (optionnel)

Par defaut, les scripts tournent toutes les **155 secondes**.

Pour mettre 150 secondes (PowerShell):

```powershell
$env:FIVEM_BOT_INTERVAL=150
python cli.py
```

## En cas de probleme

- Ferme et relance `run.bat`.
- Verifie que FiveM est ouvert et visible a l'ecran.
- Si une image n'est pas reconnue, remplace-la dans `assets/items/`.
