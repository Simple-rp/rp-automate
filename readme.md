# FiveM Focus Bots

Deux scripts rapides :

* `recolte-ble.py` : X → G → Tab → clic sur `items/ble.png` (moitié gauche) → Tab → E, en boucle toutes les **120 s par défaut**.
* `vente-pain.py` : séquence similaire, mais clique sur `items/pain.png` sur la **moitié droite**.

## Démarrage rapide

```powershell
pip install -r requirements.txt
python recolte-ble.py   # ou python vente-pain.py
```

## Conseils

* Remplace les images si nécessaire ;
* Ajuste `FIVEM_BOT_INTERVAL` pour la cadence.

**Exemple :**
Pour la vente, mets l’intervalle à **150 s** et **50** pour le nombre d’items à transférer.

## Mises à jour possibles

* Fusionner les deux fichiers en un seul ;
* Extraire les fonctions communes des deux fichiers afin de garder des fichiers plus petits et plus propres.

## Serveur FiveM compatible

Diamond City
