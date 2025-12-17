# 🌙 Le Marchand de Sable - Bot Discord

Un bot Discord complet avec système d'économie, progression infinie, tickets personnalisés et tutoriel interactif !

## 🎮 Fonctionnalités

### Économie
- 💰 Gagnez du sable en envoyant des messages, en restant en vocal, en boostant
- 🛡️ 3 classes uniques (Chevalier, Samouraï, Mage)
- ⚡ 6 équipements par classe avec niveaux infinis
- 🏆 Système de classement en temps réel

### Progression
- 👣 10 achievements/badges débloquables
- ⭐ Système de prestige (reset à niveau 100)
- 🔥 Daily login bonus avec streak system
- 📊 Statistiques complètes du serveur

### Expérience Utilisateur
- 🎮 Salons privés automatiques (tickets)
- 📚 Tutoriel interactif 5 étapes
- 🎁 Récompenses progressives pour les nouveaux joueurs
- 🏁 Archivage automatique des salons

## 📋 Commandes

**Économie:**
- `!sable` - Voir votre sable
- `!info` - Profil complet
- `!boutique armes/armures` - Voir équipements
- `!acheter arme/armure <numéro>` - Acheter

**Progression:**
- `!classement` - Top 5 plus puissants
- `!achievements` - Voir vos badges
- `!stats` - Statistiques du serveur
- `!niveaux` - Système de niveaux

**Spécial:**
- `!daily` - Bonus quotidien
- `!prestige` - Reset niveau 100
- `!setup_marchand` - Afficher embed principal (Admin)
- `!aide` - Aide générale

## ⚙️ Installation

### Sur Replit
1. Va sur https://replit.com
2. Clique "Create" → "Import from GitHub"
3. Colle l'URL: `https://github.com/ton-username/MarchandDeSable`
4. Configure les "Secrets":
   - DISCORD_TOKEN
   - FONDATEUR_ID
   - LOG_CHANNEL_ID
   - MAIN_CHANNEL_ID
   - TICKETS_CATEGORY_ID
5. Clique "Run"

### Localement
```bash
git clone https://github.com/ton-username/MarchandDeSable
cd MarchandDeSable
pip install -r requirements.txt
python main.py
```

## 🔐 Variables d'Environnement

Crée un fichier `.env` avec:
```
DISCORD_TOKEN=ton_token_discord
FONDATEUR_ID=699786476560580638
LOG_CHANNEL_ID=1450700489216884736
MAIN_CHANNEL_ID=1450708945361703045
TICKETS_CATEGORY_ID=1450709577648836610
```

## 📁 Structure

```
MarchandDeSable/
├── main.py                 # Bot principal
├── joueurs.json           # Données des joueurs
├── tickets.json           # Données des tickets
├── requirements.txt       # Dépendances Python
├── .env                   # Variables d'environnement
└── README.md             # Ce fichier
```

## 🚀 Utilisation

1. **Créer l'embed principal:**
   ```
   !setup_marchand
   ```

2. **Les joueurs cliquent "Commencer l'Aventure"**

3. **Tutoriel automatique démarre**

4. **Ils peuvent jouer avec les commandes !**

## 💡 Conseils

- Le bot gère les permissions automatiquement
- Les salons privés se créent automatiquement
- Les données sont sauvegardées en JSON (compatible avec Replit)
- Le tutoriel est obligatoire pour les nouveaux joueurs

## 📊 Gains

| Action | Gain |
|--------|------|
| Message | +10 ⏳ |
| Vocal (par min) | +5 ⏳ |
| Boost serveur | +500 ⏳ |
| Tutoriel complet | +300 ⏳ |
| Daily login | +200 ⏳ |

## 🎯 Prochaines Améliorations

- [ ] Système de duels PvP
- [ ] Guildes/Teams
- [ ] Quêtes quotidiennes
- [ ] Chasses contre créatures
- [ ] Marché de trading

## 📝 License

MIT License - Libre d'utilisation

## 👤 Auteur

Créé par [Ton Nom]

---

**Besoin d'aide ? Contacte-moi sur Discord !**
