# 💻 Guide : Utiliser Google Cloud Shell Editor

Vous avez raison d'utiliser cet éditeur ! C'est le moyen le plus puissant et direct pour gérer votre API GeoCongo AI. Voici comment s'en servir pour finaliser notre déploiement.

## 1. Accéder au code
L'image que vous avez envoyée montre que vous êtes déjà au bon endroit. Votre code est sur le Cloud Shell.
- Utilisez l'explorateur à gauche pour ouvrir `app/main.py`.
- J'ai fait des modifications pour que l'API soit plus rapide à démarrer.

## 2. Gérer le déploiement depuis l'éditeur
Ouvrez le terminal intégré (en bas de l'éditeur) et lancez les commandes que je vous donnerai.

## 3. Pourquoi l'API a mis trop de temps (Startup Timeout) ?
Le message d'erreur `Container failed to become healthy` signifie que l'API a pris plus de 4 minutes pour charger les modèles SAM 2 et Prithvi via le montage GCS (réseau).
**Solution injectée :**
- J'ai activé le **"Startup CPU Boost"** : Google donne 2x plus de puissance CPU à l'API uniquement pendant la phase de démarrage pour charger les modèles instantanément.
- J'ai augmenté le **Timeout à 10 minutes** pour être large.

## 4. Prochaines étapes
1. **Dites-moi si vous voulez que je modifie le code directement via l'agent** (je peux le faire sur vos fichiers locaux, et vous n'aurez qu'à cliquer sur "Déployer").
2. **Relancer le script `scripts/deploy.sh`** une dernière fois depuis le terminal Cloud Shell.

---
**💡 Conseil d'expert :** L'éditeur Cloud Shell vous permet aussi de voir les logs en temps réel si vous cliquez sur l'onglet "Cloud Code" en bas à gauche de la barre de statut.
