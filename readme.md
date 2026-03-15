# FiveM Focus Bots
Version: 1.1.0

Scripts simples pour automatiser des actions repetitives dans FiveM.
Compatible avec le serveur: **Diamond City**.

## Apercu rapide

- Lanceur simple avec menu (`run.bat`).
- Scripts Python par metier, images dans `assets/items/`.
- Compatible FiveM en fenetre visible, sans modification du jeu.

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

Si tu utilises `run.bat`, il peut installer les dependances automatiquement au premier lancement.

## 3) Utilisation (au quotidien)

1. Lance FiveM et place ton personnage au bon endroit.
2. Double-clique sur `run.bat`.
3. Choisis le script dans la liste (tape le numero).
4. Pour arreter un script: `Ctrl + C`.

Astuce: si tu changes `requirements.txt`, supprime le fichier `.deps_installed` pour forcer la reinstallation.

## Scripts disponibles

- `scripts/diamond/atom/recolte-ble.py`
- `scripts/diamond/atom/vente-pain.py`
- `scripts/diamond/ferme-cayo/recolte-pistache.py`
- `scripts/diamond/ferme-cayo/vente-pistache.py`
- `scripts/diamond/ferme-cayo/recolte-menth.py`
- `scripts/diamond/mine/recolte-pierre.py`
- `scripts/diamond/mine/vente-acier.py`

## Organisation des fichiers

- Scripts: `scripts/diamond/...`
- Images d'items: `assets/items/`
- Lancer avec menu: `run.bat` ou `python cli.py`

## Changer la vitesse (optionnel)

Par defaut, les scripts tournent toutes les **155 secondes**.

Pour mettre 150 secondes (PowerShell):

```powershell
$env:FIVEM_BOT_INTERVAL=150
python cli.py
```

Autre option: definir `FIVEM_BOT_PYTHON` pour utiliser un Python specifique.

## En cas de probleme

- Ferme et relance `run.bat`.
- Verifie que FiveM est ouvert et visible a l'ecran.
- Si une image n'est pas reconnue, remplace-la dans `assets/items/`.
