import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime
import asyncio
import math
from dotenv import load_dotenv
from collections import defaultdict
import logging

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Constantes
SABLE_PAR_MESSAGE = 10
SABLE_PAR_MINUTE_VOCAL = 5
SABLE_BOOST_SERVEUR = 500
SABLE_INVITE = 100
JOUEURS_FILE = 'joueurs.json'
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
FONDATEUR_ID = int(os.getenv('FONDATEUR_ID', '0'))
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')

# Prestige et Daily Login
NIVEAU_PRESTIGE = 100  # Niveau nécessaire pour prestige
SABLE_DAILY_BASE = 200  # Sable de base pour daily login
BONUS_STREAK_MAX = 14  # Bonus max après 14 jours consécutifs

# Système de Tickets
MAIN_CHANNEL_ID = os.getenv('MAIN_CHANNEL_ID')  # Salon principal "Marchand de Sable"
TICKETS_CATEGORY_ID = int(os.getenv('TICKETS_CATEGORY_ID', '0'))  # Catégorie pour les salons privés
TICKETS_FILE = 'tickets.json'

# Récompenses tutoriel
SABLE_TUTORIEL = 100  # Bonus sable pour terminer le tutoriel
SABLE_SKIP_TUTORIEL = -50  # Pénalité pour skipper

# Cooldowns (défini avant les fonctions)
cooldowns = defaultdict(lambda: {})

def ajouter_cooldown(user_id, commande, secondes):
    """Ajoute un cooldown pour une commande"""
    cooldowns[user_id][commande] = datetime.now().timestamp() + secondes

def verifier_cooldown(user_id, commande):
    """Vérifie si le cooldown est actif"""
    if user_id not in cooldowns or commande not in cooldowns[user_id]:
        return True
    return cooldowns[user_id][commande] < datetime.now().timestamp()

# Système de logs
async def envoyer_log(message, type_log="INFO"):
    """Envoie un log sur Discord et dans la console"""
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log_message = f"[{timestamp}] [{type_log}] {message}"
    
    logger.info(log_message)
    
    if LOG_CHANNEL_ID:
        try:
            channel = bot.get_channel(int(LOG_CHANNEL_ID))
            if isinstance(channel, discord.TextChannel):
                await channel.send(f"```{log_message}```")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du log: {e}")

# Système de niveaux infini basé sur la puissance
def calculer_niveau(puissance):
    """Calcule le niveau basé sur la puissance (système infini)"""
    if puissance < 50:
        return 1
    niveau = int(1 + math.log10(puissance / 50) * 10)
    return max(1, niveau)

def calculer_seuil_prochain_niveau(niveau_actuel):
    """Calcule la puissance nécessaire pour atteindre le prochain niveau"""
    return int(50 * (10 ** ((niveau_actuel) / 10)))

# Classes et équipements (système scalable avec niveaux)
CLASSES = {
    'chevalier': {
        'emoji': '🛡️',
        'description': 'Inébranlable et puissant',
        'armes': [
            {'nom': 'Épée de bronze', 'cout': 100, 'puissance': 10, 'niveau_min': 1},
            {'nom': 'Épée de fer', 'cout': 300, 'puissance': 25, 'niveau_min': 1},
            {'nom': 'Épée d\'acier', 'cout': 1000, 'puissance': 50, 'niveau_min': 2},
            {'nom': 'Lame légendaire du Roi', 'cout': 5000, 'puissance': 150, 'niveau_min': 5},
            {'nom': 'Épée des anciens dieux', 'cout': 15000, 'puissance': 400, 'niveau_min': 10},
            {'nom': 'Excalibur - Lame suprême', 'cout': 50000, 'puissance': 1200, 'niveau_min': 20}
        ],
        'armures': [
            {'nom': 'Armure de cuir', 'cout': 150, 'defense': 15, 'niveau_min': 1},
            {'nom': 'Armure de fer', 'cout': 400, 'defense': 35, 'niveau_min': 1},
            {'nom': 'Armure d\'acier forgé', 'cout': 1500, 'defense': 75, 'niveau_min': 2},
            {'nom': 'Armure légendaire du Roi', 'cout': 6000, 'defense': 200, 'niveau_min': 5},
            {'nom': 'Armure des anciens dieux', 'cout': 18000, 'defense': 550, 'niveau_min': 10},
            {'nom': 'Armure indestructible de Hephaïstos', 'cout': 60000, 'defense': 1600, 'niveau_min': 20}
        ]
    },
    'samourai': {
        'emoji': '⚔️',
        'description': 'Rapide et tranchant',
        'armes': [
            {'nom': 'Katana en bois', 'cout': 80, 'puissance': 8, 'niveau_min': 1},
            {'nom': 'Katana de bronze', 'cout': 250, 'puissance': 22, 'niveau_min': 1},
            {'nom': 'Katana de fer forgé', 'cout': 900, 'puissance': 48, 'niveau_min': 2},
            {'nom': 'Kusanagi - L\'épée de la légende', 'cout': 4500, 'puissance': 140, 'niveau_min': 5},
            {'nom': 'Murasama - Lame de tempête', 'cout': 13000, 'puissance': 380, 'niveau_min': 10},
            {'nom': 'Honjo Masamune - Lame immortelle', 'cout': 45000, 'puissance': 1100, 'niveau_min': 20}
        ],
        'armures': [
            {'nom': 'Armure de soie', 'cout': 120, 'defense': 12, 'niveau_min': 1},
            {'nom': 'Armure de cuir renforcé', 'cout': 350, 'defense': 30, 'niveau_min': 1},
            {'nom': 'Armure de laques', 'cout': 1200, 'defense': 65, 'niveau_min': 2},
            {'nom': 'Armure légendaire du Shogun', 'cout': 5500, 'defense': 180, 'niveau_min': 5},
            {'nom': 'Armure de samouraï ancestral', 'cout': 16000, 'defense': 520, 'niveau_min': 10},
            {'nom': 'Armure du Daimyo éternel', 'cout': 55000, 'defense': 1550, 'niveau_min': 20}
        ]
    },
    'mage': {
        'emoji': '✨',
        'description': 'Mystique et puissant',
        'armes': [
            {'nom': 'Bâton d\'apprenti', 'cout': 120, 'puissance': 12, 'niveau_min': 1},
            {'nom': 'Bâton de sorcier', 'cout': 350, 'puissance': 28, 'niveau_min': 1},
            {'nom': 'Bâton des anciens', 'cout': 1100, 'puissance': 55, 'niveau_min': 2},
            {'nom': 'Bâton du Sorcier Suprême', 'cout': 5500, 'puissance': 160, 'niveau_min': 5},
            {'nom': 'Bâton du Archmage', 'cout': 14000, 'puissance': 420, 'niveau_min': 10},
            {'nom': 'Bâton de Morgue - Source infinie de magie', 'cout': 48000, 'puissance': 1250, 'niveau_min': 20}
        ],
        'armures': [
            {'nom': 'Robe de novice', 'cout': 100, 'defense': 10, 'niveau_min': 1},
            {'nom': 'Robe de magicien', 'cout': 300, 'defense': 25, 'niveau_min': 1},
            {'nom': 'Robe des sages', 'cout': 1000, 'defense': 60, 'niveau_min': 2},
            {'nom': 'Robe légendaire de Merlin', 'cout': 5000, 'defense': 170, 'niveau_min': 5},
            {'nom': 'Robe du Grand Mage', 'cout': 15000, 'defense': 580, 'niveau_min': 10},
            {'nom': 'Robe de l\'Enchanteur Éternel', 'cout': 52000, 'defense': 1700, 'niveau_min': 20}
        ]
    }
}

# Système de achievements/badges
ACHIEVEMENTS = {
    'first_steps': {
        'nom': 'Premiers pas',
        'emoji': '👣',
        'description': 'Choisir une classe',
        'condition': lambda profil: profil.get('classe') is not None
    },
    'collector': {
        'nom': 'Collectionneur',
        'emoji': '🎁',
        'description': 'Acheter son premier équipement',
        'condition': lambda profil: profil.get('arme') is not None or profil.get('armure') is not None
    },
    'spender': {
        'nom': 'Dépensier',
        'emoji': '💸',
        'description': 'Dépenser 1000 sable',
        'condition': lambda profil: profil.get('sable_depense', 0) >= 1000
    },
    'wealthy': {
        'nom': 'Riche',
        'emoji': '💰',
        'description': 'Accumuler 10,000 sable',
        'condition': lambda profil: profil.get('sable', 0) >= 10000
    },
    'powerful': {
        'nom': 'Puissant',
        'emoji': '⚡',
        'description': 'Atteindre le niveau 5',
        'condition': lambda profil: profil.get('niveau', 1) >= 5
    },
    'legendary': {
        'nom': 'Légendaire',
        'emoji': '👑',
        'description': 'Atteindre le niveau 20',
        'condition': lambda profil: profil.get('niveau', 1) >= 20
    },
    'talker': {
        'nom': 'Bavard',
        'emoji': '💬',
        'description': 'Envoyer 100 messages',
        'condition': lambda profil: profil.get('messages_envoyes', 0) >= 100
    },
    'voice_master': {
        'nom': 'Maître du vocal',
        'emoji': '🎤',
        'description': 'Passer 1 heure en vocal',
        'condition': lambda profil: profil.get('temps_vocal_minutes', 0) >= 60
    },
    'boost_champion': {
        'nom': 'Champion du boost',
        'emoji': '🚀',
        'description': 'Booster le serveur',
        'condition': lambda profil: profil.get('boosts', 0) > 0
    },
    'elite_collector': {
        'nom': 'Collectionneur élite',
        'emoji': '🏆',
        'description': 'Avoir les 6 tiers d\'équipement',
        'condition': lambda profil: profil.get('equipment_count', 0) >= 6
    }
}

# ================== GESTION DES DONNÉES ==================

def charger_joueurs():
    """Charge les données des joueurs depuis le JSON"""
    if os.path.exists(JOUEURS_FILE):
        try:
            with open(JOUEURS_FILE, 'r', encoding='utf-8') as f:
                contenu = f.read().strip()
                if contenu:
                    return json.loads(contenu)
        except (json.JSONDecodeError, ValueError):
            logger.error("Erreur lors du chargement du JSON, retour dict vide")
    return {}

def sauvegarder_joueurs(joueurs):
    """Sauvegarde les données des joueurs"""
    try:
        with open(JOUEURS_FILE, 'w', encoding='utf-8') as f:
            json.dump(joueurs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde: {e}")

def migrer_profil(profil):
    """Migre un profil ancien vers le nouveau format"""
    champs_requis = {
        'id': str(profil.get('id', '')),
        'username': profil.get('username', 'Inconnu'),
        'sable': profil.get('sable', 50),
        'classe': profil.get('classe', None),
        'arme': profil.get('arme', None),
        'armure': profil.get('armure', None),
        'puissance': profil.get('puissance', 0),
        'niveau': profil.get('niveau', 1),
        'date_creation': profil.get('date_creation', datetime.now().isoformat()),
        'temps_vocal_minutes': profil.get('temps_vocal_minutes', 0),
        'dernier_gain_message': profil.get('dernier_gain_message', 0),
        'dernier_gain_vocal': profil.get('dernier_gain_vocal', 0),
        'achievements': profil.get('achievements', []),
        'messages_envoyes': profil.get('messages_envoyes', 0),
        'sable_depense': profil.get('sable_depense', 0),
        'boosts': profil.get('boosts', 0),
        'equipment_count': profil.get('equipment_count', 0),
        'prestige': profil.get('prestige', 0),
        'dernier_daily': None,
        'streak_daily': 0
    }
    return champs_requis

def creer_profil_joueur(user_id, username):
    """Crée un nouveau profil de joueur"""
    return {
        'id': str(user_id),
        'username': username,
        'sable': 50,
        'classe': None,
        'arme': None,
        'armure': None,
        'puissance': 0,
        'niveau': 1,
        'date_creation': datetime.now().isoformat(),
        'temps_vocal_minutes': 0,
        'dernier_gain_message': 0,
        'dernier_gain_vocal': 0,
        'achievements': [],
        'messages_envoyes': 0,
        'sable_depense': 0,
        'boosts': 0,
        'equipment_count': 0,
        'prestige': 0,
        'dernier_daily': None,
        'streak_daily': 0
    }

def verifier_achievements(profil):
    """Vérifie quels achievements le joueur devrait avoir"""
    achievements_actuels = set(profil.get('achievements', []))
    achievements_nouveaux = []
    
    for achievement_id, achievement_data in ACHIEVEMENTS.items():
        if achievement_id not in achievements_actuels:
            if achievement_data['condition'](profil):
                achievements_nouveaux.append(achievement_id)
    
    return achievements_nouveaux

def ajouter_achievement(profil, achievement_id):
    """Ajoute un achievement au profil du joueur"""
    if 'achievements' not in profil:
        profil['achievements'] = []
    
    if achievement_id not in profil['achievements']:
        profil['achievements'].append(achievement_id)
        return True
    return False

def passer_prestige(profil):
    """Permet à un joueur de faire un prestige"""
    if profil.get('niveau', 1) >= NIVEAU_PRESTIGE:
        profil['prestige'] = profil.get('prestige', 0) + 1
        profil['niveau'] = 1 + profil.get('prestige', 0)  # Bonus de niveau
        profil['puissance'] = 0
        profil['arme'] = None
        profil['armure'] = None
        profil['sable'] = 50
        return True
    return False

def verifier_daily_login(profil):
    """Vérifie et applique le daily login bonus"""
    dernier_daily = profil.get('dernier_daily')
    now = datetime.now()
    today = now.date().isoformat()
    
    # Si c'est la première fois ou dernier daily est d'un autre jour
    if dernier_daily is None:
        dernier_daily_date = None
    else:
        dernier_daily_date = datetime.fromisoformat(dernier_daily).date().isoformat() if isinstance(dernier_daily, str) else None
    
    # Déjà collecté aujourd'hui
    if dernier_daily_date == today:
        return None, profil.get('streak_daily', 0)
    
    # Calcul du streak
    streak = profil.get('streak_daily', 0)
    if dernier_daily_date:
        derniere_date = datetime.fromisoformat(dernier_daily).date()
        jours_passes = (now.date() - derniere_date).days
        
        if jours_passes == 1:
            # Jour consécutif
            streak = min(streak + 1, BONUS_STREAK_MAX)
        else:
            # Streak cassé
            streak = 1
    else:
        streak = 1
    
    # Calcul du bonus
    bonus_sable = SABLE_DAILY_BASE + (streak * 10)
    profil['sable'] += bonus_sable
    profil['dernier_daily'] = now.isoformat()
    profil['streak_daily'] = streak
    
    return bonus_sable, streak

def obtenir_joueur(user_id):
    """Récupère le profil d'un joueur"""
    joueurs = charger_joueurs()
    profil = joueurs.get(str(user_id))
    
    if profil:
        # Migrer le profil s'il manque des champs
        profil = migrer_profil(profil)
        joueurs[str(user_id)] = profil
        sauvegarder_joueurs(joueurs)
        return profil
    return None

def sauvegarder_joueur(user_id, profil):
    """Sauvegarde le profil d'un joueur"""
    try:
        joueurs = charger_joueurs()
        joueurs[str(user_id)] = profil
        sauvegarder_joueurs(joueurs)
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du joueur {user_id}: {e}")

# ================== GESTION DES TICKETS ==================

def charger_tickets():
    """Charge les données des tickets depuis le JSON"""
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
                contenu = f.read().strip()
                if contenu:
                    return json.loads(contenu)
        except (json.JSONDecodeError, ValueError):
            logger.error("Erreur lors du chargement des tickets")
    return {}

def sauvegarder_tickets(tickets):
    """Sauvegarde les données des tickets"""
    try:
        with open(TICKETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tickets, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des tickets: {e}")

def creer_ticket(user_id, channel_id):
    """Crée un ticket dans la DB"""
    tickets = charger_tickets()
    tickets[str(user_id)] = {
        'user_id': str(user_id),
        'channel_id': str(channel_id),
        'creation_date': datetime.now().isoformat(),
        'tutoriel_etape': 1,
        'tutoriel_complete': False,
        'archive': False
    }
    sauvegarder_tickets(tickets)

def obtenir_ticket(user_id):
    """Récupère le ticket d'un utilisateur"""
    tickets = charger_tickets()
    return tickets.get(str(user_id))

def sauvegarder_ticket(user_id, ticket_data):
    """Sauvegarde les données d'un ticket"""
    tickets = charger_tickets()
    tickets[str(user_id)] = ticket_data
    sauvegarder_tickets(tickets)

def calculer_puissance(classe, arme_data, armure_data):
    """Calcule la puissance totale"""
    puissance = 0
    if arme_data:
        puissance += arme_data.get('puissance', 0)
    if armure_data:
        puissance += armure_data.get('defense', 0)
    return puissance

def mettre_a_jour_niveau(joueur):
    """Met à jour le niveau du joueur selon sa puissance"""
    ancien_niveau = joueur.get('niveau', 1)
    nouveau_niveau = calculer_niveau(joueur['puissance'])
    joueur['niveau'] = nouveau_niveau
    
    return nouveau_niveau > ancien_niveau

async def assigner_role_classe(member, classe):
    """Assigne le rôle Discord correspondant à la classe"""
    try:
        guild = member.guild
        role_name = f"Rêveur {classe.capitalize()}"
        
        role = discord.utils.get(guild.roles, name=role_name)
        
        if not role:
            if classe == 'chevalier':
                color = discord.Color.from_rgb(192, 192, 192)
            elif classe == 'samourai':
                color = discord.Color.from_rgb(255, 140, 0)
            else:
                color = discord.Color.from_rgb(138, 43, 226)
            
            role = await guild.create_role(
                name=role_name,
                color=color,
                reason=f"Rôle pour la classe {classe}"
            )
        
        await member.add_roles(role)
        await envoyer_log(f"{member.name} a choisi la classe {classe}", "CLASSE")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'assignation du rôle: {e}")
        await envoyer_log(f"Erreur rôle: {e}", "ERROR")
        return False

def obtenir_pseudo_serveur(member: discord.User | discord.Member):
    """Obtient le pseudo du serveur (nickname) ou le nom d'utilisateur"""
    if isinstance(member, discord.Member) and member.nick:
        return member.nick
    return member.name

# ================== ÉVÉNEMENTS ==================

@bot.event
async def on_ready():
    """Quand le bot est prêt"""
    if bot.user:
        print(f'{bot.user} est connecté !')
        print(f'Bot ID: {bot.user.id}')
        await envoyer_log(f"Bot démarré - {bot.user.name}", "START")
    compteur_vocal.start()
    
    # Ajouter les views persistentes pour les boutons
    bot.add_view(BoutonCommencerAventure())
    bot.add_view(BoutonsTutoriel(0, 0))  # Les user_id/etape vrai seront mis à jour
    bot.add_view(BoutonsClasse(0))
    bot.add_view(BoutonsFermeture(0))

@bot.event
async def on_message(message):
    """Récompense les messages"""
    if message.author.bot:
        return
    
    try:
        joueur = obtenir_joueur(message.author.id)
        if not joueur:
            joueur = creer_profil_joueur(message.author.id, message.author.name)
            sauvegarder_joueur(message.author.id, joueur)
        
        # Récompenser les messages SEULEMENT si classe choisie et pas de cooldown
        if joueur['classe']:
            timestamp_actuel = datetime.now().timestamp()
            if timestamp_actuel - joueur.get('dernier_gain_message', 0) >= 1:  # Min 1 sec entre les gains
                joueur['sable'] += SABLE_PAR_MESSAGE
                joueur['messages_envoyes'] = joueur.get('messages_envoyes', 0) + 1
                joueur['dernier_gain_message'] = timestamp_actuel
                
                # Vérifier les achievements
                achievements_gagnes = verifier_achievements(joueur)
                for ach_id in achievements_gagnes:
                    ajouter_achievement(joueur, ach_id)
                
                sauvegarder_joueur(message.author.id, joueur)
        
    except Exception as e:
        logger.error(f"Erreur dans on_message: {e}")
        await envoyer_log(f"Erreur message: {e}", "ERROR")
    
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    """Gère les changements d'état vocal"""
    try:
        joueur = obtenir_joueur(member.id)
        if not joueur:
            joueur = creer_profil_joueur(member.id, member.name)
            sauvegarder_joueur(member.id, joueur)
    except Exception as e:
        logger.error(f"Erreur dans on_voice_state_update: {e}")

@bot.event
async def on_member_update(before, after):
    """Détecte les boosts du serveur"""
    try:
        if before.premium_since != after.premium_since and after.premium_since is not None:
            joueur = obtenir_joueur(after.id)
            if not joueur:
                joueur = creer_profil_joueur(after.id, after.name)
            
            joueur['sable'] += SABLE_BOOST_SERVEUR
            joueur['boosts'] = joueur.get('boosts', 0) + 1
            
            # Vérifier les achievements
            achievements_gagnes = verifier_achievements(joueur)
            for ach_id in achievements_gagnes:
                ajouter_achievement(joueur, ach_id)
            
            sauvegarder_joueur(after.id, joueur)
            
            pseudo = obtenir_pseudo_serveur(after)
            await envoyer_log(f"{pseudo} a boosté le serveur +{SABLE_BOOST_SERVEUR} ⏳", "BOOST")
    except Exception as e:
        logger.error(f"Erreur dans on_member_update: {e}")

@tasks.loop(minutes=1)
async def compteur_vocal():
    """Récompense les utilisateurs en vocal chaque minute"""
    try:
        for guild in bot.guilds:
            for member in guild.members:
                if member.voice and member.voice.channel and not member.bot:
                    joueur = obtenir_joueur(member.id)
                    if not joueur:
                        joueur = creer_profil_joueur(member.id, member.name)
                    
                    if joueur['classe']:
                        timestamp_actuel = datetime.now().timestamp()
                        if timestamp_actuel - joueur.get('dernier_gain_vocal', 0) >= 60:  # 1 minute minimum
                            joueur['sable'] += SABLE_PAR_MINUTE_VOCAL
                            joueur['temps_vocal_minutes'] += 1
                            joueur['dernier_gain_vocal'] = timestamp_actuel
                            sauvegarder_joueur(member.id, joueur)
    except Exception as e:
        logger.error(f"Erreur dans compteur_vocal: {e}")
        await envoyer_log(f"Erreur vocal: {e}", "ERROR")

# ================== VIEWS ET BOUTONS ==================

class BoutonCommencerAventure(discord.ui.View):
    """Bouton pour commencer l'aventure"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Commencer l'Aventure", style=discord.ButtonStyle.success, emoji="🎮")
    async def commencer(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Crée un ticket pour l'utilisateur"""
        await interaction.response.defer()
        
        try:
            user_id = interaction.user.id
            guild = interaction.guild
            
            if not guild:
                await interaction.followup.send("❌ Erreur: Pas de serveur!", ephemeral=True)
                return
            
            # Vérifier si l'utilisateur a déjà un ticket
            ticket_existant = obtenir_ticket(user_id)
            if ticket_existant and not ticket_existant.get('archive'):
                await interaction.followup.send(
                    "❌ Vous avez déjà un salon d'aventure ! Allez le voir.",
                    ephemeral=True
                )
                return
            
            # Créer le canal privé
            fondateur = guild.get_member(FONDATEUR_ID) if FONDATEUR_ID else None
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            if fondateur:
                overwrites[fondateur] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            category = guild.get_channel(int(TICKETS_CATEGORY_ID)) if TICKETS_CATEGORY_ID else None
            channel = await guild.create_text_channel(
                f"🎮-aventure-{interaction.user.name}",
                category=category if isinstance(category, discord.CategoryChannel) else None,
                overwrites=overwrites
            )
            
            # Créer le ticket dans la DB
            creer_ticket(user_id, channel.id)
            
            # Envoyer le tutoriel
            await envoyer_tutoriel_etape1(channel, interaction.user)
            
            await interaction.followup.send(
                f"✅ Votre salon d'aventure a été créé ! {channel.mention}",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Erreur dans commencer l'aventure: {e}")
            await interaction.followup.send("❌ Une erreur s'est produite !", ephemeral=True)

class BoutonsTutoriel(discord.ui.View):
    """Boutons pour le tutoriel"""
    def __init__(self, user_id, etape):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.etape = etape
    
    @discord.ui.button(label="Suivant", style=discord.ButtonStyle.primary, emoji="➡️")
    async def suivant(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Passe à l'étape suivante"""
        if interaction.user.id != self.user_id:
            await interaction.response.defer()
            return
        
        await interaction.response.defer()
        etape_suivante = self.etape + 1
        
        ticket = obtenir_ticket(self.user_id)
        if ticket:
            ticket['tutoriel_etape'] = etape_suivante
            sauvegarder_ticket(self.user_id, ticket)
        
        if etape_suivante == 2 and isinstance(interaction.channel, discord.TextChannel):
            await envoyer_tutoriel_etape2(interaction.channel, interaction.user)
        elif etape_suivante == 3 and isinstance(interaction.channel, discord.TextChannel):
            await envoyer_tutoriel_etape3(interaction.channel, interaction.user)
        elif etape_suivante == 4 and isinstance(interaction.channel, discord.TextChannel):
            await envoyer_tutoriel_etape4(interaction.channel, interaction.user)
        elif etape_suivante == 5 and isinstance(interaction.channel, discord.TextChannel):
            await envoyer_tutoriel_etape5(interaction.channel, interaction.user)
        elif etape_suivante == 6 and isinstance(interaction.channel, discord.TextChannel):
            await envoyer_tutoriel_complete(interaction.channel, interaction.user)

class BoutonsClasse(discord.ui.View):
    """Boutons pour choisir une classe dans le tutoriel"""
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id
    
    @discord.ui.button(label="Chevalier", style=discord.ButtonStyle.danger, emoji="🛡️")
    async def chevalier(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer()
            return
        await self.choisir_classe(interaction, "chevalier")
    
    @discord.ui.button(label="Samouraï", style=discord.ButtonStyle.secondary, emoji="⚔️")
    async def samourai(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer()
            return
        await self.choisir_classe(interaction, "samourai")
    
    @discord.ui.button(label="Mage", style=discord.ButtonStyle.blurple, emoji="✨")
    async def mage(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer()
            return
        await self.choisir_classe(interaction, "mage")
    
    async def choisir_classe(self, interaction: discord.Interaction, classe: str):
        await interaction.response.defer()
        
        joueur = obtenir_joueur(interaction.user.id)
        if not joueur:
            joueur = creer_profil_joueur(interaction.user.id, interaction.user.name)
        
        if joueur['classe']:
            await interaction.followup.send(f"❌ Vous avez déjà une classe !", ephemeral=True)
            return
        
        joueur['classe'] = classe
        
        # Vérifier achievements
        achievements_gagnes = verifier_achievements(joueur)
        for ach_id in achievements_gagnes:
            ajouter_achievement(joueur, ach_id)
        
        sauvegarder_joueur(interaction.user.id, joueur)
        
        # Assigner rôle
        try:
            if interaction.guild:
                role_name = f"Rêveur {classe.capitalize()}"
                role = discord.utils.get(interaction.guild.roles, name=role_name)
                if not role:
                    role = await interaction.guild.create_role(name=role_name)
                if isinstance(interaction.user, discord.Member):
                    await interaction.user.add_roles(role)
        except Exception as e:
            logger.error(f"Erreur assigning role: {e}")
        
        embed = discord.Embed(
            title="✅ Classe Choisie !",
            description=f"Tu es maintenant un {CLASSES[classe]['emoji']} **{classe.capitalize()}**",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # Passer automatiquement à l'étape 3
        if isinstance(interaction.channel, discord.TextChannel):
            await envoyer_tutoriel_etape3(interaction.channel, interaction.user)

class BoutonsFermeture(discord.ui.View):
    """Bouton pour fermer le salon d'aventure"""
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id
    
    @discord.ui.button(label="Terminer l'Aventure", style=discord.ButtonStyle.red, emoji="🏁")
    async def fermer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer()
            return
        
        await interaction.response.defer()
        
        ticket = obtenir_ticket(self.user_id)
        joueur = obtenir_joueur(self.user_id)
        
        embed = discord.Embed(
            title="📋 Résumé Final",
            description="Merci d'avoir joué à Le Marchand de Sable !",
            color=discord.Color.gold()
        )
        
        if joueur:
            embed.add_field(name="Sable Accumulé", value=f"{joueur['sable']} ⏳", inline=True)
            embed.add_field(name="Niveau Atteint", value=f"{joueur.get('niveau', 1)} ⭐", inline=True)
            embed.add_field(name="Achievements", value=f"{len(joueur.get('achievements', []))} 🏆", inline=True)
        
        embed.set_footer(text="Salon sera archivé dans 7 jours")
        await interaction.followup.send(embed=embed)
        
        if ticket:
            ticket['archive'] = True
            sauvegarder_ticket(self.user_id, ticket)
        
        await envoyer_log(f"{interaction.user.name} a terminé son aventure", "ADVENTURE_END")

# Fonctions d'envoi du tutoriel

async def envoyer_tutoriel_etape1(channel: discord.TextChannel, user: discord.User | discord.Member):
    """Étape 1: Bienvenue"""
    embed = discord.Embed(
        title="👋 Étape 1: Bienvenue",
        description="Bienvenue dans Le Marchand de Sable !",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📖 L'Histoire",
        value="Tu as découvert un marché magique contrôlé par un mystérieux marchand. "
              "Ici, le sable magique ⏳ est la monnaie ultime. En restant actif sur le serveur, "
              "tu accumules du sable et peux acheter des équipements de plus en plus puissants.",
        inline=False
    )
    
    embed.add_field(
        name="🎯 Ton Objectif",
        value="Devenir le plus puissant de tous ! Accumule du sable, "
              "achète des équipements légendaires et atteins des niveaux inimaginables.",
        inline=False
    )
    
    embed.add_field(
        name="⏳ Progression",
        value="**Étape 1 de 5** - Bienvenue ✅",
        inline=False
    )
    
    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
    
    view = BoutonsTutoriel(user.id, 1)
    await channel.send(embed=embed, view=view)

async def envoyer_tutoriel_etape2(channel: discord.TextChannel, user: discord.User | discord.Member):
    """Étape 2: Choisir une classe"""
    embed = discord.Embed(
        title="🎭 Étape 2: Choisir Ta Classe",
        description="Chaque classe a ses propres équipements uniques !",
        color=discord.Color.purple()
    )
    
    for nom, info in CLASSES.items():
        embed.add_field(
            name=f"{info['emoji']} {nom.capitalize()}",
            value=info['description'],
            inline=False
        )
    
    embed.add_field(
        name="⏳ Progression",
        value="**Étape 2 de 5** - Choisir une classe",
        inline=False
    )
    
    view = BoutonsClasse(user.id)
    await channel.send(embed=embed, view=view)

async def envoyer_tutoriel_etape3(channel: discord.TextChannel, user: discord.User | discord.Member):
    """Étape 3: Équipement gratuit"""
    embed = discord.Embed(
        title="🎁 Étape 3: Ton Premier Équipement",
        description="Voici un équipement gratuit pour bien commencer !",
        color=discord.Color.green()
    )
    
    joueur = obtenir_joueur(user.id)
    if joueur and joueur['classe']:
        classe_data = CLASSES[joueur['classe']]
        arme = classe_data['armes'][0]
        
        joueur['arme'] = arme['nom']
        joueur['sable'] += SABLE_TUTORIEL
        
        # Calculer puissance
        arme_data = arme
        armure_data = None
        joueur['puissance'] = calculer_puissance(joueur['classe'], arme_data, armure_data)
        
        sauvegarder_joueur(user.id, joueur)
        
        embed.add_field(
            name="⚔️ Équipement Reçu",
            value=f"{arme['nom']}\nPuissance: +{arme['puissance']} ⚡",
            inline=False
        )
        
        embed.add_field(
            name="💰 Bonus Sable",
            value=f"+{SABLE_TUTORIEL} ⏳ pour commencer !",
            inline=False
        )
    
    embed.add_field(
        name="⏳ Progression",
        value="**Étape 3 de 5** - Équipement ✅",
        inline=False
    )
    
    view = BoutonsTutoriel(user.id, 3)
    await channel.send(embed=embed, view=view)

async def envoyer_tutoriel_etape4(channel: discord.TextChannel, user: discord.User | discord.Member):
    """Étape 4: Système de sable"""
    embed = discord.Embed(
        title="💰 Étape 4: Comment Gagner du Sable",
        description="Il y a plusieurs façons de devenir riche !",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="💬 Messages",
        value=f"+{SABLE_PAR_MESSAGE} ⏳ par message (min 1 sec entre 2)",
        inline=False
    )
    
    embed.add_field(
        name="🎤 Vocal",
        value=f"+{SABLE_PAR_MINUTE_VOCAL} ⏳ par minute en vocal",
        inline=False
    )
    
    embed.add_field(
        name="🚀 Boosts Serveur",
        value=f"+{SABLE_BOOST_SERVEUR} ⏳ quand tu boostes le serveur",
        inline=False
    )
    
    embed.add_field(
        name="⏳ Progression",
        value="**Étape 4 de 5** - Système de Sable",
        inline=False
    )
    
    view = BoutonsTutoriel(user.id, 4)
    await channel.send(embed=embed, view=view)

async def envoyer_tutoriel_etape5(channel: discord.TextChannel, user: discord.User | discord.Member):
    """Étape 5: Commandes essentielles"""
    embed = discord.Embed(
        title="📚 Étape 5: Commandes Essentielles",
        description="Voici les commandes principales !",
        color=discord.Color.blurple()
    )
    
    embed.add_field(
        name="💰 Économie",
        value="`!sable` - Voir ton sable rapidement\n"
              "`!info` - Voir ton profil complet",
        inline=False
    )
    
    embed.add_field(
        name="🛍️ Achat",
        value="`!boutique armes` - Voir les armes\n"
              "`!boutique armures` - Voir les armures\n"
              "`!acheter arme 1` - Acheter l'arme #1",
        inline=False
    )
    
    embed.add_field(
        name="🏆 Progressio",
        value="`!classement` - Top 5 les plus puissants\n"
              "`!achievements` - Voir tes badges\n"
              "`!prestige` - Reset au niveau 100",
        inline=False
    )
    
    embed.add_field(
        name="⏳ Progression",
        value="**Étape 5 de 5** - Commandes",
        inline=False
    )
    
    view = BoutonsTutoriel(user.id, 5)
    await channel.send(embed=embed, view=view)

async def envoyer_tutoriel_complete(channel: discord.TextChannel, user: discord.User | discord.Member):
    """Tutoriel complété"""
    embed = discord.Embed(
        title="🎉 Tutoriel Complété !",
        description="Tu es prêt à commencer ton aventure !",
        color=discord.Color.green()
    )
    
    joueur = obtenir_joueur(user.id)
    if joueur:
        joueur['sable'] += SABLE_TUTORIEL * 2  # Bonus final
        sauvegarder_joueur(user.id, joueur)
        
        embed.add_field(
            name="🎁 Récompenses Finales",
            value=f"+{SABLE_TUTORIEL * 2} ⏳ bonus de completion",
            inline=False
        )
    
    embed.add_field(
        name="📝 Conseils",
        value="• Reste actif pour gagner du sable\n"
              "• Achète des équipements pour monter de niveau\n"
              "• Rejoins les événements pour des bonus\n"
              "• Partage avec tes amis ! 👥",
        inline=False
    )
    
    ticket = obtenir_ticket(user.id)
    if ticket:
        ticket['tutoriel_complete'] = True
        sauvegarder_ticket(user.id, ticket)
    
    view = BoutonsFermeture(user.id)
    await channel.send(embed=embed, view=view)

# ================== COMMANDES ==================

@bot.command(name='sable')
async def afficher_sable(ctx):
    """Affiche le sable du joueur"""
    try:
        if not verifier_cooldown(ctx.author.id, 'sable'):
            await ctx.send("⏱️ Attendez un peu avant de relancer cette commande !")
            return
        
        ajouter_cooldown(ctx.author.id, 'sable', 2)
        
        joueur = obtenir_joueur(ctx.author.id)
        if not joueur:
            joueur = creer_profil_joueur(ctx.author.id, ctx.author.name)
            sauvegarder_joueur(ctx.author.id, joueur)
        
        pseudo = obtenir_pseudo_serveur(ctx.author)
        
        embed = discord.Embed(
            title=f"⏳ Profil de {pseudo}",
            color=discord.Color.gold(),
            description=f"**Sable Magique:** {joueur['sable']} ⏳"
        )
        embed.add_field(name="Puissance", value=f"{joueur['puissance']} ⚡", inline=False)
        if joueur['arme']:
            embed.add_field(name="Arme", value=joueur['arme'], inline=True)
        if joueur['armure']:
            embed.add_field(name="Armure", value=joueur['armure'], inline=True)
        if joueur['classe']:
            embed.add_field(name="Classe", value=f"{CLASSES[joueur['classe']]['emoji']} {joueur['classe'].capitalize()}", inline=True)
        
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Erreur dans !sable: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !sable: {e}", "ERROR")

@bot.command(name='info')
async def afficher_info(ctx, membre: discord.Member | None = None):
    """Affiche les informations détaillées d'un profil"""
    try:
        if not verifier_cooldown(ctx.author.id, 'info'):
            await ctx.send("⏱️ Attendez un peu avant de relancer cette commande !")
            return
        
        ajouter_cooldown(ctx.author.id, 'info', 2)
        
        if membre is None:
            membre = ctx.author
        
        if not membre:
            await ctx.send("❌ Impossible de trouver le membre !")
            return
        
        joueur = obtenir_joueur(membre.id)
        if not joueur:
            pseudo = obtenir_pseudo_serveur(membre)
            await ctx.send(f"❌ {pseudo} n'a pas encore de profil !")
            return
        
        pseudo = obtenir_pseudo_serveur(membre)
        
        embed = discord.Embed(
            title=f"📋 Profil détaillé de {pseudo}",
            color=discord.Color.blue(),
            description=f"ID: {membre.id}"
        )
        
        if joueur['classe']:
            embed.add_field(
                name="💰 Économie",
                value=f"Sable: {joueur['sable']} ⏳\nStatut: ✅ Actif",
                inline=False
            )
        else:
            embed.add_field(
                name="💰 Économie",
                value=f"Sable: {joueur['sable']} ⏳\nStatut: ❌ Classe non choisie",
                inline=False
            )
        
        if joueur['classe']:
            classe_data = CLASSES[joueur['classe']]
            embed.add_field(
                name="🎭 Classe",
                value=f"{classe_data['emoji']} {joueur['classe'].capitalize()}",
                inline=True
            )
        
        if joueur['arme']:
            embed.add_field(name="⚔️ Arme", value=joueur['arme'], inline=True)
        if joueur['armure']:
            embed.add_field(name="🛡️ Armure", value=joueur['armure'], inline=True)
        
        niveau = joueur.get('niveau', 1)
        prochain_seuil = calculer_seuil_prochain_niveau(niveau)
        embed.add_field(
            name="📊 Niveau et Puissance",
            value=f"Niveau: **{niveau}** ⭐\nPuissance: {joueur['puissance']} ⚡\nProchain palier: {prochain_seuil} ⚡",
            inline=False
        )
        
        embed.add_field(
            name="🎙️ Activité",
            value=f"Temps en vocal: {joueur['temps_vocal_minutes']} minutes",
            inline=False
        )
        
        # Vérifier et mettre à jour les achievements
        achievements_gagnes = verifier_achievements(joueur)
        for ach_id in achievements_gagnes:
            ajouter_achievement(joueur, ach_id)
        sauvegarder_joueur(membre.id, joueur)
        
        achievements = joueur.get('achievements', [])
        achievements_display = ""
        if achievements:
            for ach_id in achievements:
                if ach_id in ACHIEVEMENTS:
                    ach = ACHIEVEMENTS[ach_id]
                    achievements_display += f"{ach['emoji']} {ach['nom']}\n"
        else:
            achievements_display = "Aucun achievement pour l'instant"
        
        embed.add_field(
            name=f"🏆 Achievements ({len(achievements)}/{len(ACHIEVEMENTS)})",
            value=achievements_display,
            inline=False
        )
        
        # Prestige et Daily Info
        prestige = joueur.get('prestige', 0)
        streak_daily = joueur.get('streak_daily', 0)
        
        prestige_display = "⭐" * prestige if prestige > 0 else "Aucun prestige"
        embed.add_field(
            name="✨ Prestige",
            value=f"{prestige_display}\nNiveau actuel: {niveau} (Base: 1 + Prestige bonus: {prestige})",
            inline=False
        )
        
        embed.add_field(
            name="🔥 Daily Login Streak",
            value=f"Jours consécutifs: **{streak_daily}**",
            inline=False
        )
        
        date_creation = datetime.fromisoformat(joueur['date_creation'])
        embed.add_field(
            name="📅 Profil créé le",
            value=date_creation.strftime("%d/%m/%Y à %H:%M"),
            inline=False
        )
        
        if membre.avatar:
            embed.set_thumbnail(url=membre.avatar.url)
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Erreur dans !info: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !info: {e}", "ERROR")

@bot.command(name='classe')
async def choisir_classe(ctx, classe: str | None = None):
    """Choisit une classe (chevalier, samourai, mage)"""
    try:
        joueur = obtenir_joueur(ctx.author.id)
        if not joueur:
            joueur = creer_profil_joueur(ctx.author.id, ctx.author.name)
        
        if not classe:
            embed = discord.Embed(
                title="🌙 Choisir votre classe",
                color=discord.Color.purple(),
                description="Tapez `!classe <nom>` pour choisir votre classe"
            )
            for nom, info in CLASSES.items():
                embed.add_field(
                    name=f"{info['emoji']} {nom.capitalize()}",
                    value=info['description'],
                    inline=False
                )
            await ctx.send(embed=embed)
            return
        
        classe = classe.lower()
        if classe not in CLASSES:
            await ctx.send("❌ Classe invalide ! Choisissez entre : chevalier, samourai, mage")
            return
        
        if joueur['classe']:
            await ctx.send(f"❌ Vous avez déjà choisi la classe **{joueur['classe'].capitalize()}** !")
            return
        
        joueur['classe'] = classe
        
        # Vérifier les achievements
        achievements_gagnes = verifier_achievements(joueur)
        for ach_id in achievements_gagnes:
            ajouter_achievement(joueur, ach_id)
        
        sauvegarder_joueur(ctx.author.id, joueur)
        
        await assigner_role_classe(ctx.author, classe)
        
        embed = discord.Embed(
            title="✨ Classe choisie !",
            color=discord.Color.green(),
            description=f"Vous êtes désormais un {CLASSES[classe]['emoji']} **{classe.capitalize()}**\n\n{CLASSES[classe]['description']}\n\n💰 Le système de récompense est maintenant activé !"
        )
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Erreur dans !classe: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !classe: {e}", "ERROR")

@bot.command(name='retirer_classe')
async def retirer_classe(ctx):
    """Retire la classe du joueur (arrête les gains de sable)"""
    try:
        joueur = obtenir_joueur(ctx.author.id)
        if not joueur:
            await ctx.send("❌ Vous n'avez pas encore de profil !")
            return
        
        if not joueur['classe']:
            await ctx.send("❌ Vous n'avez pas de classe actuellement !")
            return
        
        try:
            for classe_nom in CLASSES.keys():
                role_name = f"Rêveur {classe_nom.capitalize()}"
                role = discord.utils.get(ctx.guild.roles, name=role_name)
                if role and role in ctx.author.roles:
                    await ctx.author.remove_roles(role)
        except Exception as e:
            logger.error(f"Erreur retrait rôles: {e}")
        
        ancienne_classe = joueur['classe']
        joueur['classe'] = None
        sauvegarder_joueur(ctx.author.id, joueur)
        
        await envoyer_log(f"{obtenir_pseudo_serveur(ctx.author)} a retiré la classe {ancienne_classe}", "CLASSE")
        
        embed = discord.Embed(
            title="🛑 Classe retirée",
            color=discord.Color.orange(),
            description=f"Vous avez retiré la classe **{ancienne_classe.capitalize()}**\n\n"
                        f"⚠️ **Le système de récompense est maintenant désactivé !**"
        )
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Erreur dans !retirer_classe: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !retirer_classe: {e}", "ERROR")

@bot.command(name='boutique')
async def afficher_boutique(ctx, categorie: str | None = None):
    """Affiche la boutique d'équipements"""
    try:
        if not verifier_cooldown(ctx.author.id, 'boutique'):
            await ctx.send("⏱️ Attendez un peu avant de relancer cette commande !")
            return
        
        ajouter_cooldown(ctx.author.id, 'boutique', 2)
        
        joueur = obtenir_joueur(ctx.author.id)
        if not joueur:
            joueur = creer_profil_joueur(ctx.author.id, ctx.author.name)
            sauvegarder_joueur(ctx.author.id, joueur)
        
        if not joueur['classe']:
            await ctx.send("❌ Vous devez d'abord choisir une classe avec `!classe <nom>`")
            return
        
        classe_data = CLASSES[joueur['classe']]
        niveau = joueur.get('niveau', 1)
        
        if not categorie or categorie.lower() == 'armes':
            embed = discord.Embed(
                title=f"🛒 Armes - {classe_data['emoji']} {joueur['classe'].capitalize()}",
                color=discord.Color.orange(),
                description=f"Votre sable: {joueur['sable']} ⏳ | Niveau: {niveau} ⭐\n\nTapez `!acheter arme <numéro>`"
            )
            for i, arme in enumerate(classe_data['armes'], 1):
                statut = "✅" if joueur.get('arme') == arme['nom'] else ""
                niveau_requis = arme.get('niveau_min', 1)
                etat = f"🔒 Niveau {niveau_requis} requis" if niveau < niveau_requis else f"✅ Accessible"
                
                embed.add_field(
                    name=f"{i}. {arme['nom']} {statut}",
                    value=f"Coût: {arme['cout']} ⏳ | Puissance: {arme['puissance']} ⚡ | {etat}",
                    inline=False
                )
            embed.set_footer(text="Tapez !boutique armures pour voir les armures")
            await ctx.send(embed=embed)
        
        elif categorie.lower() == 'armures':
            embed = discord.Embed(
                title=f"🛒 Armures - {classe_data['emoji']} {joueur['classe'].capitalize()}",
                color=discord.Color.blue(),
                description=f"Votre sable: {joueur['sable']} ⏳ | Niveau: {niveau} ⭐\n\nTapez `!acheter armure <numéro>`"
            )
            for i, armure in enumerate(classe_data['armures'], 1):
                statut = "✅" if joueur.get('armure') == armure['nom'] else ""
                niveau_requis = armure.get('niveau_min', 1)
                etat = f"🔒 Niveau {niveau_requis} requis" if niveau < niveau_requis else f"✅ Accessible"
                
                embed.add_field(
                    name=f"{i}. {armure['nom']} {statut}",
                    value=f"Coût: {armure['cout']} ⏳ | Défense: {armure['defense']} 🛡️ | {etat}",
                    inline=False
                )
            embed.set_footer(text="Tapez !boutique armes pour voir les armes")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Catégorie invalide ! Utilisez : `!boutique armes` ou `!boutique armures`")
    except Exception as e:
        logger.error(f"Erreur dans !boutique: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !boutique: {e}", "ERROR")

@bot.command(name='acheter')
async def acheter_equipement(ctx, categorie: str, numero: int):
    """Achète un équipement"""
    try:
        if not verifier_cooldown(ctx.author.id, 'acheter'):
            await ctx.send("⏱️ Attendez un peu avant de relancer cette commande !")
            return
        
        ajouter_cooldown(ctx.author.id, 'acheter', 2)
        
        joueur = obtenir_joueur(ctx.author.id)
        if not joueur:
            joueur = creer_profil_joueur(ctx.author.id, ctx.author.name)
            sauvegarder_joueur(ctx.author.id, joueur)
        
        if not joueur['classe']:
            await ctx.send("❌ Vous devez d'abord choisir une classe avec `!classe <nom>`")
            return
        
        classe_data = CLASSES[joueur['classe']]
        categorie = categorie.lower()
        
        if categorie == 'arme':
            if numero < 1 or numero > len(classe_data['armes']):
                await ctx.send(f"❌ Numéro invalide ! Choisissez entre 1 et {len(classe_data['armes'])}")
                return
            equipement = classe_data['armes'][numero - 1]
        elif categorie == 'armure':
            if numero < 1 or numero > len(classe_data['armures']):
                await ctx.send(f"❌ Numéro invalide ! Choisissez entre 1 et {len(classe_data['armures'])}")
                return
            equipement = classe_data['armures'][numero - 1]
        else:
            await ctx.send("❌ Catégorie invalide ! Utilisez : `arme` ou `armure`")
            return
        
        niveau_requis = equipement.get('niveau_min', 1)
        niveau_joueur = joueur.get('niveau', 1)
        
        if niveau_joueur < niveau_requis:
            await ctx.send(f"❌ Vous ne pouvez pas acheter cet équipement ! Vous devez atteindre le niveau **{niveau_requis}** (vous êtes niveau {niveau_joueur})")
            return
        
        if joueur['sable'] < equipement['cout']:
            await ctx.send(f"❌ Vous n'avez pas assez de sable ! Il vous faut {equipement['cout'] - joueur['sable']} ⏳ de plus.")
            return
        
        joueur['sable'] -= equipement['cout']
        joueur['sable_depense'] = joueur.get('sable_depense', 0) + equipement['cout']
        joueur['equipment_count'] = joueur.get('equipment_count', 0) + 1
        
        if categorie == 'arme':
            joueur['arme'] = equipement['nom']
        else:
            joueur['armure'] = equipement['nom']
        
        arme_data = None
        armure_data = None
        if joueur['arme']:
            for arme in classe_data['armes']:
                if arme['nom'] == joueur['arme']:
                    arme_data = arme
                    break
        if joueur['armure']:
            for armure in classe_data['armures']:
                if armure['nom'] == joueur['armure']:
                    armure_data = armure
                    break
        
        joueur['puissance'] = calculer_puissance(joueur['classe'], arme_data, armure_data)
        
        # Vérifier les achievements
        achievements_gagnes = verifier_achievements(joueur)
        for ach_id in achievements_gagnes:
            ajouter_achievement(joueur, ach_id)
        
        niveau_up = mettre_a_jour_niveau(joueur)
        sauvegarder_joueur(ctx.author.id, joueur)
        
        nouveau_niveau = joueur.get('niveau', 1)
        message_niveau = ""
        if niveau_up:
            message_niveau = f"\n\n🎉 **AUGMENTATION DE NIVEAU !** 🎉\nVous êtes passé au niveau **{nouveau_niveau}** ⭐"
        
        pseudo = obtenir_pseudo_serveur(ctx.author)
        await envoyer_log(f"{pseudo} a acheté {equipement['nom']} - Puissance: {joueur['puissance']}", "ACHAT")
        
        embed = discord.Embed(
            title="✨ Achat réussi !",
            color=discord.Color.green(),
            description=f"Vous avez acquis **{equipement['nom']}** !\n\n"
                        f"Sable restant: {joueur['sable']} ⏳\n"
                        f"Puissance totale: {joueur['puissance']} ⚡{message_niveau}"
        )
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Erreur dans !acheter: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !acheter: {e}", "ERROR")

@bot.command(name='classement')
async def afficher_classement(ctx):
    """Affiche le classement des 5 plus puissants"""
    try:
        if not verifier_cooldown(ctx.author.id, 'classement'):
            await ctx.send("⏱️ Attendez un peu avant de relancer cette commande !")
            return
        
        ajouter_cooldown(ctx.author.id, 'classement', 5)
        
        joueurs = charger_joueurs()
        
        if not joueurs:
            await ctx.send("Aucun joueur pour le moment !")
            return
        
        classement = sorted(
            [(profil, nom) for nom, profil in joueurs.items()],
            key=lambda x: x[0]['puissance'],
            reverse=True
        )[:5]
        
        embed = discord.Embed(
            title="🏆 Top 5 des Rêveurs les Plus Puissants",
            color=discord.Color.gold(),
            description="Classement de puissance"
        )
        
        for i, (profil, user_id) in enumerate(classement, 1):
            classe_emoji = ''
            if profil['classe']:
                classe_emoji = CLASSES[profil['classe']]['emoji']
            
            niveau = profil.get('niveau', 1)
            medal = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][i-1]
            
            try:
                member = await ctx.guild.fetch_member(int(user_id))
                pseudo = obtenir_pseudo_serveur(member)
            except:
                pseudo = profil['username']
            
            embed.add_field(
                name=f"{medal} {pseudo} {classe_emoji}",
                value=f"Niveau: {niveau} ⭐ | Puissance: {profil['puissance']} ⚡ | Sable: {profil['sable']} ⏳",
                inline=False
            )
        
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Erreur dans !classement: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !classement: {e}", "ERROR")

@bot.command(name='reset')
async def reset_economie(ctx):
    """Reset l'économie et les rôles (fondateur seulement) - Nouvelle saison"""
    try:
        if ctx.author.id != FONDATEUR_ID:
            await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande !")
            return
        
        confirmation_msg = await ctx.send("⚠️ **ATTENTION !** Vous êtes sur le point de lancer une **NOUVELLE SAISON**:\n"
                                          "• Tous les profils seront réinitialisés\n"
                                          "• Tous les rôles de classe seront retirés\n"
                                          "• Chaque joueur retrouvera 50 ⏳ de sable\n\n"
                                          "Tapez `!confirm` pour confirmer.")
        
        def check(msg):
            return msg.author == ctx.author and msg.content.lower() == '!confirm'
        
        try:
            await bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await confirmation_msg.edit(content="❌ Reset annulé (délai dépassé)")
            return
        
        # Message de démarrage du reset
        reset_msg = await ctx.send("🔄 **Réinitialisation en cours...**\n⏳ Suppression des rôles...")
        
        # Étape 1: Supprimer tous les rôles de classe
        rôles_supprimes = 0
        try:
            for classe_nom in CLASSES.keys():
                role_name = f"Rêveur {classe_nom.capitalize()}"
                role = discord.utils.get(ctx.guild.roles, name=role_name)
                if role:
                    # Retirer le rôle de tous les membres
                    for member in ctx.guild.members:
                        if role in member.roles:
                            await member.remove_roles(role)
                    # Supprimer le rôle
                    await role.delete()
                    rôles_supprimes += 1
                    logger.info(f"Rôle supprimé: {role_name}")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des rôles: {e}")
            await envoyer_log(f"Erreur suppression rôles: {e}", "ERROR")
        
        await reset_msg.edit(content=f"🔄 **Réinitialisation en cours...**\n✅ {rôles_supprimes} rôles supprimés\n⏳ Réinitialisation des profils...")
        
        # Étape 2: Réinitialiser tous les profils
        joueurs = charger_joueurs()
        joueurs_resetés = 0
        for user_id, profil in joueurs.items():
            profil['sable'] = 50
            profil['classe'] = None
            profil['arme'] = None
            profil['armure'] = None
            profil['puissance'] = 0
            profil['niveau'] = 1
            profil['temps_vocal_minutes'] = 0
            profil['dernier_gain_message'] = 0
            profil['dernier_gain_vocal'] = 0
            joueurs_resetés += 1
        
        sauvegarder_joueurs(joueurs)
        
        # Message de confirmation final
        embed = discord.Embed(
            title="🌙 NOUVELLE SAISON - RÉINITIALISATION COMPLÈTE",
            color=discord.Color.gold(),
            description=f"✅ La réinitialisation est terminée avec succès !\n\n"
                        f"**Statistiques:**\n"
                        f"• {rôles_supprimes} rôles supprimés\n"
                        f"• {joueurs_resetés} profils réinitialisés\n"
                        f"• Chaque joueur: 50 ⏳ de sable\n\n"
                        f"🎮 Les joueurs peuvent maintenant recommencer avec `!classe <nom>` !"
        )
        
        await reset_msg.delete()
        await ctx.send(embed=embed)
        await envoyer_log(f"NOUVELLE SAISON lancée - {joueurs_resetés} joueurs réinitialisés, {rôles_supprimes} rôles supprimés", "RESET")
        
    except Exception as e:
        logger.error(f"Erreur dans !reset: {e}")
        await ctx.send("❌ Une erreur s'est produite lors du reset !")
        await envoyer_log(f"Erreur !reset critique: {e}", "ERROR")

@bot.command(name='setup_marchand')
async def setup_marchand(ctx):
    """Configure et poste le message d'accueil du jeu (fondateur seulement)"""
    try:
        if ctx.author.id != FONDATEUR_ID:
            await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande !")
            return
        
        embed = discord.Embed(
            title="🌙 Bienvenue au Marchand de Sable",
            color=discord.Color.purple(),
            description="Découvrez un monde magique où le sable est la monnaie suprême !",
            url="https://discord.gg"
        )
        
        embed.add_field(
            name="✨ L'Aventure t'attend",
            value="Clique sur le bouton ci-dessous pour commencer ton voyage !\n\n"
                  "Tu seras guidé pas à pas à travers un tutoriel complet pour apprendre à jouer.",
            inline=False
        )
        
        embed.add_field(
            name="🎯 L'Objectif",
            value="Deviens le plus puissant de tous ! \n\n"
                  "Accumule du sable magique ⏳ en restant actif sur le serveur et achète des équipements légendaires pour augmenter ta puissance. "
                  "Tu découvriras comment gagner du sable lors du tutoriel ! 📚",
            inline=False
        )
        
        embed.add_field(
            name="🛡️ Les 3 Grandes Classes",
            value=f"{CLASSES['chevalier']['emoji']} **Chevalier** - Puissant et inébranlable\n"
                  f"{CLASSES['samourai']['emoji']} **Samouraï** - Rapide et tranchant\n"
                  f"{CLASSES['mage']['emoji']} **Mage** - Mystique et puissant",
            inline=False
        )
        
        embed.add_field(
            name="📊 Progression Infinie",
            value="Débloquez toujours de nouveaux équipements et niveaux ! "
                  "Le système n'a pas de limite - deviens aussi puissant que tu le souhaites.",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Achievements & Prestige",
            value="Gagne des badges en accomplissant des objectifs et deviens légendaire avec le système de prestige !",
            inline=False
        )
        
        embed.set_footer(text="Bonne chance, Rêveur ! 🌙")
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1995/1995506.png")
        
        view = BoutonCommencerAventure()
        await ctx.send(embed=embed, view=view)
        
        await envoyer_log(f"{ctx.author.name} a posté le message d'accueil du Marchand de Sable", "SETUP")
        await ctx.send("✅ Message d'accueil posté avec succès !")
    except Exception as e:
        logger.error(f"Erreur dans !setup_marchand: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !setup_marchand: {e}", "ERROR")

@bot.command(name='aide')
async def afficher_aide(ctx):
    """Affiche l'aide du jeu"""
    try:
        embed = discord.Embed(
            title="🌙 Le Marchand de Sable - Aide",
            color=discord.Color.purple(),
            description="Guide complet du jeu"
        )
        
        embed.add_field(
            name="📚 Commandes principales",
            value="`!sable` - Affiche votre sable rapidement\n"
                  "`!info` - Voir votre profil détaillé\n"
                  "`!info @membre` - Voir le profil d'un autre joueur\n"
                  "`!classe <nom>` - Choisir votre classe\n"
                  "`!retirer_classe` - Retirer votre classe (arrête les gains)\n"
                  "`!boutique <armes/armures>` - Voir les équipements\n"
                  "`!acheter <arme/armure> <numéro>` - Acheter un équipement\n"
                  "`!classement` - Voir le top 5 des plus puissants",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Progression et Statistiques",
            value="`!achievements` - Voir vos badges et achievements\n"
                  "`!stats` - Voir les statistiques du serveur\n"
                  "`!niveaux` - Comprendre le système de niveaux infini",
            inline=False
        )
        
        embed.add_field(
            name="✨ Prestige et Récompenses",
            value="`!daily` - Recevoir le bonus quotidien de sable (Streak system)\n"
                  "`!prestige` - Passer un prestige quand vous atteignez niveau 100\n"
                  "Niveau requis pour prestige: **100**",
            inline=False
        )
        embed.add_field(
            name="💰 Comment gagner du sable",
            value=f"**⚠️ Vous devez d'abord choisir une classe avec `!classe`**\n\n"
                  f"• Envoyer un message: +{SABLE_PAR_MESSAGE} ⏳\n"
                  f"• Rester en vocal (par minute): +{SABLE_PAR_MINUTE_VOCAL} ⏳\n"
                  f"• Booster le serveur: +{SABLE_BOOST_SERVEUR} ⏳",
            inline=False
        )
        
        embed.add_field(
            name="🎮 Classes disponibles",
            value=f"{CLASSES['chevalier']['emoji']} **Chevalier** - {CLASSES['chevalier']['description']}\n"
                  f"{CLASSES['samourai']['emoji']} **Samouraï** - {CLASSES['samourai']['description']}\n"
                  f"{CLASSES['mage']['emoji']} **Mage** - {CLASSES['mage']['description']}",
            inline=False
        )
        
        embed.add_field(
            name="🎭 Rôles automatiques",
            value="Quand vous choisissez une classe, un rôle Discord est assigné automatiquement !",
            inline=False
        )
        
        embed.add_field(
            name="⭐ Système de niveaux infini",
            value="Plus votre puissance augmente, plus votre niveau monte ! Débloquez de nouveaux équipements toujours plus puissants.\nTapez `!niveaux` pour plus de détails.",
            inline=False
        )
        
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Erreur dans !aide: {e}")
        await ctx.send("❌ Une erreur s'est produite !")

@bot.command(name='niveaux')
async def afficher_niveaux(ctx):
    """Affiche le système de niveaux"""
    try:
        embed = discord.Embed(
            title="⭐ Système de Niveaux Infini",
            color=discord.Color.gold(),
            description="Progression sans fin avec déblocage d'équipements progressifs"
        )
        
        embed.add_field(
            name="📈 Comment ça marche ?",
            value="Chaque équipement augmente votre **puissance** ⚡. "
                  "À chaque palier de puissance atteint, votre **niveau** ⭐ augmente et de nouveaux équipements se débloquent !",
            inline=False
        )
        
        embed.add_field(
            name="🔓 Déblocage d'équipements",
            value="• **Niveau 1**: Débuts\n"
                  "• **Niveau 2**: Équipements avancés (Puissance: 50+)\n"
                  "• **Niveau 5**: Équipements légendaires (Puissance: 300+)\n"
                  "• **Niveau 10**: Équipements anciens (Puissance: 2,000+)\n"
                  "• **Niveau 20+**: Équipements suprêmes (Puissance: 100,000+)\n"
                  "• **Et bien d'autres...**",
            inline=False
        )
        
        embed.add_field(
            name="💡 Progression",
            value="Votre progression est **illimitée** ! Continuez à acheter des équipements de plus en plus puissants et vous débloquerez des niveaux de plus en plus élevés.",
            inline=False
        )
        
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Erreur dans !niveaux: {e}")
        await ctx.send("❌ Une erreur s'est produite !")

@bot.command(name='achievements')
async def afficher_achievements(ctx, utilisateur: discord.User | None = None):
    """Affiche les achievements du joueur"""
    try:
        if utilisateur is None:
            utilisateur = ctx.author
        
        if not utilisateur:
            await ctx.send("❌ Impossible de trouver l'utilisateur !")
            return
        
        joueur = obtenir_joueur(utilisateur.id)
        if not joueur:
            await ctx.send("❌ Ce joueur n'a pas encore de profil !")
            return
        
        # Vérifier et mettre à jour les achievements actuels
        achievements_gagnes = verifier_achievements(joueur)
        for ach_id in achievements_gagnes:
            ajouter_achievement(joueur, ach_id)
        sauvegarder_joueur(utilisateur.id, joueur)
        
        pseudo = obtenir_pseudo_serveur(utilisateur)
        embed = discord.Embed(
            title=f"🏆 Achievements de {pseudo}",
            color=discord.Color.gold(),
            description=f"Total: {len(joueur.get('achievements', []))} / {len(ACHIEVEMENTS)}"
        )
        
        achievements_list = joueur.get('achievements', [])
        
        for ach_id, ach_data in ACHIEVEMENTS.items():
            if ach_id in achievements_list:
                status = "✅"
                value = f"Débloqué ! {ach_data['description']}"
            else:
                status = "🔒"
                value = f"Verrouillé - {ach_data['description']}"
            
            embed.add_field(
                name=f"{status} {ach_data['emoji']} {ach_data['nom']}",
                value=value,
                inline=False
            )
        
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Erreur dans !achievements: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !achievements: {e}", "ERROR")

@bot.command(name='stats')
async def afficher_stats(ctx):
    """Affiche les statistiques du serveur"""
    try:
        joueurs = charger_joueurs()
        
        if not joueurs:
            await ctx.send("❌ Aucune donnée de joueur disponible !")
            return
        
        total_joueurs = len(joueurs)
        total_sable = sum(j.get('sable', 0) for j in joueurs.values())
        total_puissance = sum(j.get('puissance', 0) for j in joueurs.values())
        total_messages = sum(j.get('messages_envoyes', 0) for j in joueurs.values())
        total_vocal = sum(j.get('temps_vocal_minutes', 0) for j in joueurs.values())
        
        # Calculer les niveaux et moyenne
        niveaux = [j.get('niveau', 1) for j in joueurs.values()]
        niveau_moyen = sum(niveaux) / len(niveaux) if niveaux else 0
        
        # Classe la plus populaire
        classes_count = {}
        for j in joueurs.values():
            classe = j.get('classe')
            if classe:
                classes_count[classe] = classes_count.get(classe, 0) + 1
        
        classe_populaire = "Aucune" if not classes_count else max(classes_count, key=lambda x: classes_count[x])
        
        # Joueur plus riche
        joueur_plus_riche = max(joueurs.values(), key=lambda j: j.get('sable', 0))
        pseudo_riche = joueur_plus_riche.get('username', 'Inconnu')
        sable_max = joueur_plus_riche.get('sable', 0)
        
        # Joueur le plus puissant
        joueur_plus_puissant = max(joueurs.values(), key=lambda j: j.get('puissance', 0))
        pseudo_puissant = joueur_plus_puissant.get('username', 'Inconnu')
        puissance_max = joueur_plus_puissant.get('puissance', 0)
        
        embed = discord.Embed(
            title="📊 Statistiques du Serveur",
            color=discord.Color.blue(),
            description="Vue d'ensemble de l'économie du Marchand de Sable"
        )
        
        embed.add_field(
            name="👥 Joueurs",
            value=f"**{total_joueurs}** joueurs actifs",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Niveau Moyen",
            value=f"**{niveau_moyen:.1f}**",
            inline=True
        )
        
        embed.add_field(
            name="💰 Sable Total",
            value=f"**{total_sable:,}** ⏳",
            inline=True
        )
        
        embed.add_field(
            name="⚡ Puissance Totale",
            value=f"**{total_puissance:,}**",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Classe Populaire",
            value=f"**{classe_populaire.capitalize()}** ({classes_count.get(classe_populaire, 0)} joueurs)",
            inline=True
        )
        
        embed.add_field(
            name="💬 Messages Envoyés",
            value=f"**{total_messages:,}** messages",
            inline=True
        )
        
        embed.add_field(
            name="🎤 Temps Vocal",
            value=f"**{total_vocal:,}** minutes",
            inline=True
        )
        
        embed.add_field(
            name="💎 Joueur le Plus Riche",
            value=f"**{pseudo_riche}** - {sable_max:,} ⏳",
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Joueur le Plus Puissant",
            value=f"**{pseudo_puissant}** - Puissance: {puissance_max:,}",
            inline=False
        )
        
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Erreur dans !stats: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !stats: {e}", "ERROR")

@bot.command(name='daily')
async def daily_login(ctx):
    """Réclamez votre bonus quotidien"""
    try:
        joueur = obtenir_joueur(ctx.author.id)
        if not joueur:
            joueur = creer_profil_joueur(ctx.author.id, ctx.author.name)
            sauvegarder_joueur(ctx.author.id, joueur)
        
        bonus_sable, streak = verifier_daily_login(joueur)
        
        if bonus_sable is None:
            await ctx.send(f"❌ Vous avez déjà reçu votre bonus aujourd'hui !\nRevenez demain (Streak: {streak} 🔥)")
            return
        
        sauvegarder_joueur(ctx.author.id, joueur)
        
        embed = discord.Embed(
            title="✅ Daily Login Bonus",
            color=discord.Color.gold(),
            description=f"Bonus reçu: **{bonus_sable}** ⏳"
        )
        
        streak_display = "🔥" * streak if streak <= 14 else "🔥" * 14 + f" +{streak - 14}"
        embed.add_field(
            name="Streak",
            value=f"{streak} jours consécutifs\n{streak_display}",
            inline=False
        )
        
        embed.add_field(
            name="💰 Nouveau total",
            value=f"**{joueur['sable']}** ⏳",
            inline=False
        )
        
        embed.set_footer(text="Revenez demain pour continuer votre streak !")
        await ctx.send(embed=embed)
        
        pseudo = obtenir_pseudo_serveur(ctx.author)
        await envoyer_log(f"{pseudo} a reçu le daily login (+{bonus_sable} ⏳, Streak: {streak})", "DAILY")
    except Exception as e:
        logger.error(f"Erreur dans !daily: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !daily: {e}", "ERROR")

@bot.command(name='prestige')
async def faire_prestige(ctx):
    """Faire un prestige (reset à niveau 1 + bonus)"""
    try:
        joueur = obtenir_joueur(ctx.author.id)
        if not joueur:
            await ctx.send("❌ Vous n'avez pas encore de profil !")
            return
        
        if joueur.get('niveau', 1) < NIVEAU_PRESTIGE:
            await ctx.send(f"❌ Vous devez atteindre le niveau **{NIVEAU_PRESTIGE}** pour faire un prestige ! (Vous êtes niveau {joueur.get('niveau', 1)})")
            return
        
        ancien_niveau = joueur.get('niveau', 1)
        ancien_prestige = joueur.get('prestige', 0)
        
        passer_prestige(joueur)
        sauvegarder_joueur(ctx.author.id, joueur)
        
        pseudo = obtenir_pseudo_serveur(ctx.author)
        embed = discord.Embed(
            title="⭐ PRESTIGE ! ⭐",
            color=discord.Color.gold(),
            description="Vous avez passé un prestige !"
        )
        
        embed.add_field(
            name="📊 Progression",
            value=f"Ancien niveau: **{ancien_niveau}**\n"
                  f"Ancien prestige: **{ancien_prestige}**\n"
                  f"Nouveau prestige: **{joueur['prestige']}** ⭐\n"
                  f"Nouveau niveau: **{joueur['niveau']}** (bonus: +{joueur['prestige']})",
            inline=False
        )
        
        embed.add_field(
            name="💰 Nouveau départ",
            value=f"Sable: {joueur['sable']} ⏳\n"
                  f"Arme: Réinitialisée\n"
                  f"Armure: Réinitialisée",
            inline=False
        )
        
        embed.add_field(
            name="🎁 Récompenses de Prestige",
            value=f"• +1 étoile de prestige ⭐\n"
                  f"• Réinitialisation complète\n"
                  f"• Niveau de base augmenté\n"
                  f"• Recommencer l'aventure !",
            inline=False
        )
        
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
        
        await envoyer_log(f"✨ {pseudo} a passé un prestige ! Prestige: {joueur['prestige']} ⭐", "PRESTIGE")
    except Exception as e:
        logger.error(f"Erreur dans !prestige: {e}")
        await ctx.send("❌ Une erreur s'est produite !")
        await envoyer_log(f"Erreur !prestige: {e}", "ERROR")

@bot.event
async def on_command_error(ctx, error):
    """Gère les erreurs de commandes"""
    try:
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Commande non trouvée ! Tapez `!aide` pour voir toutes les commandes.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Arguments manquants ! Tapez `!aide` pour la syntaxe correcte.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Argument invalide !")
        else:
            logger.error(f"Erreur non gérée: {error}")
            await ctx.send("❌ Une erreur s'est produite !")
            await envoyer_log(f"Erreur commande: {error}", "ERROR")
    except Exception as e:
        logger.error(f"Erreur dans on_command_error: {e}")

# Lancer le bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ ERREUR: Token Discord non trouvé dans .env")
        exit(1)
    
    bot.run(DISCORD_TOKEN)
