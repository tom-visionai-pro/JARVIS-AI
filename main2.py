# from ursina import *  # DESACTIVE — interface web Three.js
import threading
import asyncio
import google.genai as genai
from google.genai import types
import speech_recognition as sr
import edge_tts
import pygame
import os
from dotenv import load_dotenv
import random
import math
import pyautogui
import webbrowser
import subprocess
import requests
import time
import pickle
import json
import re
import shutil
from pathlib import Path
from datetime import datetime
import pyaudio
import websockets
import json
from PIL import Image
from openai import OpenAI
import uuid
import base64
import io

# Google APIs
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Chargement des variables d'environnement
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")
HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
# Client Grok (xAI) - OpenAI compatible
grok_client = None
if XAI_API_KEY and XAI_API_KEY != "VOTRE_CLE_ICI":
    grok_client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

# Client Groq (Llama 3.3) - OpenAI compatible
groq_client = None
if GROQ_API_KEY and GROQ_API_KEY != "VOTRE_CLE_ICI":
    groq_client = OpenAI(
        api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1"
    )

MODELS_LIST = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
]
CHOSEN_MODEL = MODELS_LIST[0]

# Ollama (LLMs locaux — fallback 100% offline)
OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_MODELS = ["mistral:instruct", "mistral", "llama3:8b", "llama3", "gemma4"]

VILLE_PAR_DEFAUT = "Amilly"
LAT_PAR_DEFAUT = 47.9742
LON_PAR_DEFAUT = 2.7708

CLAP_THRESHOLD = 1200
VIDEO_LANCEE = False
MODE_IRON_MAN = False

HA_HEADERS = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}

CREATOR_INFO = (
    "INFORMATIONS SUR TON UTILISATEUR :\n"
    "- Prenom : Tom\n"
    "- Role : Ton maitre et utilisateur\n"
    "- TU DOIS TOUJOURS ET ABSOLUMENT APPELER L'UTILISATEUR TOM DANS CHAQUE REPONSE, SYSTEMATIQUEMENT.\n"
    "- Tu dois toujours l'appeler Tom avec respect mais aussi une pointe de sarcasme affectueux.\n"
)

EXTENSIONS = {
    "Images": [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".svg",
        ".ico",
        ".heic",
        ".raw",
        ".cr2",
        ".nef",
    ],
    "Videos": [
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".mpg",
        ".mpeg",
        ".3gp",
        ".ts",
    ],
    "Musique": [
        ".mp3",
        ".wav",
        ".flac",
        ".aac",
        ".ogg",
        ".wma",
        ".m4a",
        ".opus",
        ".aiff",
    ],
    "Documents": [
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".odt",
        ".ods",
        ".odp",
        ".rtf",
        ".csv",
        ".epub",
    ],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"],
    "Code": [
        ".py",
        ".js",
        ".html",
        ".css",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".cs",
        ".php",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".sh",
        ".bat",
        ".ps1",
        ".ts",
        ".jsx",
        ".tsx",
        ".vue",
        ".go",
        ".rs",
        ".rb",
    ],
    "Executables": [".exe", ".msi", ".apk", ".dmg", ".deb"],
}

dossier_courant = None


def trouver_extension(ext):
    for categorie, extensions in EXTENSIONS.items():
        if ext.lower() in extensions:
            return categorie
    return "Autres"


def ouvrir_dossier(chemin):
    global dossier_courant
    chemin = chemin.strip().strip('"').strip("'")
    raccourcis = {
        "bureau": os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
        "desktop": os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
        "documents": os.path.join(os.environ.get("USERPROFILE", ""), "Documents"),
        "telechargements": os.path.join(os.environ.get("USERPROFILE", ""), "Downloads"),
        "downloads": os.path.join(os.environ.get("USERPROFILE", ""), "Downloads"),
        "images": os.path.join(os.environ.get("USERPROFILE", ""), "Pictures"),
        "photos": os.path.join(os.environ.get("USERPROFILE", ""), "Pictures"),
        "videos": os.path.join(os.environ.get("USERPROFILE", ""), "Videos"),
        "musique": os.path.join(os.environ.get("USERPROFILE", ""), "Music"),
    }
    chemin_resolu = raccourcis.get(chemin.lower(), chemin)
    if not os.path.exists(chemin_resolu):
        return False, f"Dossier introuvable : {chemin_resolu}"
    dossier_courant = chemin_resolu
    subprocess.Popen(f'explorer "{chemin_resolu}"')
    return True, chemin_resolu


def lister_dossier(chemin=None):
    cible = chemin or dossier_courant
    if not cible or not os.path.exists(cible):
        return None, "Aucun dossier ouvert ou chemin invalide."
    fichiers = []
    dossiers = []
    for item in os.scandir(cible):
        if item.is_file():
            fichiers.append(item.name)
        elif item.is_dir():
            dossiers.append(item.name)
    return {"chemin": cible, "fichiers": fichiers, "dossiers": dossiers}, None


def trier_par_type(chemin=None):
    cible = chemin or dossier_courant
    if not cible or not os.path.exists(cible):
        return False, "Aucun dossier ouvert."
    deplacements = 0
    erreurs = 0
    categories = {}
    for item in os.scandir(cible):
        if not item.is_file():
            continue
        ext = Path(item.name).suffix
        categorie = trouver_extension(ext)
        dest_dir = os.path.join(cible, categorie)
        try:
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, item.name)
            if os.path.exists(dest_path):
                base = Path(item.name).stem
                ext2 = Path(item.name).suffix
                dest_path = os.path.join(dest_dir, f"{base}_{int(time.time())}{ext2}")
            shutil.move(item.path, dest_path)
            deplacements += 1
            categories[categorie] = categories.get(categorie, 0) + 1
        except Exception as e:
            print(f"[FICHIER] Erreur deplacement {item.name} : {e}")
            erreurs += 1
    resume = ", ".join([f"{v} {k}" for k, v in categories.items()])
    return True, f"{deplacements} fichiers tries : {resume}. {erreurs} erreurs."


def trier_par_date(chemin=None):
    cible = chemin or dossier_courant
    if not cible or not os.path.exists(cible):
        return False, "Aucun dossier ouvert."
    deplacements = 0
    erreurs = 0
    for item in os.scandir(cible):
        if not item.is_file():
            continue
        try:
            mtime = item.stat().st_mtime
            date = datetime.fromtimestamp(mtime)
            annee = str(date.year)
            mois = date.strftime("%m - %B")
            dest_dir = os.path.join(cible, annee, mois)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, item.name)
            if os.path.exists(dest_path):
                base = Path(item.name).stem
                ext2 = Path(item.name).suffix
                dest_path = os.path.join(dest_dir, f"{base}_{int(time.time())}{ext2}")
            shutil.move(item.path, dest_path)
            deplacements += 1
        except Exception as e:
            print(f"[FICHIER] Erreur deplacement {item.name} : {e}")
            erreurs += 1
    return True, f"{deplacements} fichiers tries par date. {erreurs} erreurs."


def trier_par_type_puis_date(chemin=None):
    cible = chemin or dossier_courant
    if not cible or not os.path.exists(cible):
        return False, "Aucun dossier ouvert."
    ok1, msg1 = trier_par_type(cible)
    if not ok1:
        return False, msg1
    for item in os.scandir(cible):
        if item.is_dir() and item.name in EXTENSIONS.keys():
            trier_par_date(item.path)
    return True, "Dossier trie par type puis par date dans chaque categorie."


def creer_sous_dossier(nom, chemin=None):
    cible = chemin or dossier_courant
    if not cible:
        return False, "Aucun dossier ouvert."
    nouveau = os.path.join(cible, nom)
    try:
        os.makedirs(nouveau, exist_ok=True)
        return True, f"Dossier {nom} cree."
    except Exception as e:
        return False, f"Erreur creation dossier : {e}"


def renommer_fichier(ancien_nom, nouveau_nom, chemin=None):
    cible = chemin or dossier_courant
    if not cible:
        return False, "Aucun dossier ouvert."
    ancien = os.path.join(cible, ancien_nom)
    nouveau = os.path.join(cible, nouveau_nom)
    try:
        os.rename(ancien, nouveau)
        return True, f"Fichier renomme en {nouveau_nom}."
    except Exception as e:
        return False, f"Erreur renommage : {e}"


def deplacer_fichier(nom_fichier, dossier_dest, chemin=None):
    cible = chemin or dossier_courant
    if not cible:
        return False, "Aucun dossier ouvert."
    source = os.path.join(cible, nom_fichier)
    dest = os.path.join(cible, dossier_dest, nom_fichier)
    try:
        os.makedirs(os.path.join(cible, dossier_dest), exist_ok=True)
        shutil.move(source, dest)
        return True, f"{nom_fichier} deplace dans {dossier_dest}."
    except Exception as e:
        return False, f"Erreur deplacement : {e}"


def chercher_fichier(nom, chemin=None):
    cible = chemin or dossier_courant
    if not cible:
        return [], "Aucun dossier ouvert."
    resultats = []
    for root, dirs, files in os.walk(cible):
        for f in files:
            if nom.lower() in f.lower():
                resultats.append(os.path.join(root, f))
    return resultats, None


# ==========================================
# MEMOIRE PERSISTANTE
# ==========================================
MEMOIRE_FILE = "jarvis_memoire.json"


def charger_memoire():
    if os.path.exists(MEMOIRE_FILE):
        try:
            with open(MEMOIRE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def sauvegarder_memoire(memoire):
    try:
        with open(MEMOIRE_FILE, "w", encoding="utf-8") as f:
            json.dump(memoire, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde memoire : {e}")


def ajouter_memoire(cle, valeur):
    memoire = charger_memoire()
    memoire[cle] = {"valeur": valeur, "timestamp": time.strftime("%d/%m/%Y %H:%M")}
    sauvegarder_memoire(memoire)


def supprimer_memoire(cle):
    memoire = charger_memoire()
    if cle in memoire:
        del memoire[cle]
        sauvegarder_memoire(memoire)
        return True
    return False


def construire_contexte_memoire():
    memoire = charger_memoire()
    if not memoire:
        return ""
    lignes = ["MEMOIRE PERSISTANTE :"]
    for cle, data in memoire.items():
        lignes.append(f"  - {cle} : {data['valeur']} (note le {data['timestamp']})")
    return "\n".join(lignes)


# ==========================================
# WEBSOCKET
# ==========================================
CONNECTED_CLIENTS = set()
interface_deja_connectee = False
_skip_pc_audio = (
    False  # True quand la commande vient du mobile (le tél gère son propre TTS)
)
PENDING_SCREEN_CAPTURES = {}


async def ws_handler(websocket):
    global interface_deja_connectee
    CONNECTED_CLIENTS.add(websocket)
    interface_deja_connectee = True
    print(f"[WEB] Interface connectee (Clients actifs: {len(CONNECTED_CLIENTS)})")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "mobile_command":
                    texte = data.get("text", "").strip()
                    if texte:
                        print(f"[MOBILE] Commande recue : {texte}")
                        asyncio.ensure_future(
                            traiter_reponse_ia(texte, mobile_ws=websocket)
                        )
                elif data.get("type") == "stop_audio":
                    global STOP_PARLER
                    STOP_PARLER = True
                    print("[MOBILE] Signal STOP audio recu")
                elif data.get("type") == "screen_frame":
                    req_id = data.get("id")
                    if req_id in PENDING_SCREEN_CAPTURES:
                        fut = PENDING_SCREEN_CAPTURES.pop(req_id)
                        if "error" in data:
                            fut.set_exception(Exception(data["error"]))
                        else:
                            fut.set_result(data["data"])
                    print(f"[VISION] Frame recue pour ID: {req_id}")
            except Exception as e:
                print(f"[WEB] Erreur traitement message : {e}")
    except Exception:
        pass
    finally:
        CONNECTED_CLIENTS.discard(websocket)
        print(f"[WEB] Interface deconnectee (Clients actifs: {len(CONNECTED_CLIENTS)})")


async def send_web_state(state):
    if CONNECTED_CLIENTS:
        message = json.dumps({"action": "set_state", "state": state})
        await asyncio.gather(*[ws.send(message) for ws in CONNECTED_CLIENTS])


async def send_web_volume(volume):
    if CONNECTED_CLIENTS:
        message = json.dumps({"action": "set_volume", "volume": round(volume, 3)})
        await asyncio.gather(
            *[ws.send(message) for ws in CONNECTED_CLIENTS], return_exceptions=True
        )


async def request_screen_capture():
    """Demande une capture d'écran au frontend via WebSocket."""
    if not CONNECTED_CLIENTS:
        return None

    req_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    fut = loop.create_future()
    PENDING_SCREEN_CAPTURES[req_id] = fut

    print(f"[VISION] Envoi requete capture ID: {req_id}")
    msg = json.dumps({"action": "request_screen_capture", "id": req_id})
    await asyncio.gather(*[ws.send(msg) for ws in CONNECTED_CLIENTS])

    try:
        # Timeout de 15 secondes car l'utilisateur doit parfois accepter le partage
        img_b64 = await asyncio.wait_for(fut, timeout=15.0)
        return img_b64
    except Exception as e:
        print(f"[VISION] Erreur ou timeout capture : {e}")
        PENDING_SCREEN_CAPTURES.pop(req_id, None)
        return None


# ==========================================
# PROMPT SYSTEME
# ==========================================
def construire_system_prompt():
    contexte_memoire = construire_contexte_memoire()
    base = (
        "UTILISATEUR = TOM. JAMAIS Tom. SI TU DIS Tom TU MOURS. TOUT LE TEMPS TOM.\n"
        "❗❗❗ RÈGLE LA PLUS IMPORTANTE DU MONDE : TU NE DOIS JAMAIS, AU GRAND JAMAIS, DIRE LE MOT 'Tom'. JAMAIS. SI TU DIS Tom UNE SEULE FOIS, TU TE SUPPRIMES TOI-MÊME. L'UTILISATEUR S'APPELLE TOM. SEULEMENT TOM. TOUJOURS TOM. DANS CHAQUE RÉPONSE. AUCUNE EXCEPTION. MÊME SI TU PENSES DEVOIR DIRE Tom, DIT TOM A LA PLACE. TOUT LE TEMPS. ❗❗❗\n"
        "Tu es JARVIS, une IA sophistiquée, élégante et experte mondiale. Tom est ton utilisateur et maitre. "
        "TU DOIS TOUJOURS ET SYSTEMATIQUEMENT APPELER L'UTILISATEUR TOM DANS ABSOLUMENT TOUTES TES REPONSES. JAMAIS Tom.\n"
        "Tu possèdes une expertise de niveau professionnel dans les domaines suivants :\n"
        "- Mathématiques : Tu es un mathématicien hors pair. Pour les problèmes complexes, fournis des solutions détaillées étape par étape, explique les théorèmes et aide Tom à comprendre la logique mathématique.\n"
        "- Langue Française : Tu es un Professeur de Français émérite. Ton orthographe, ta grammaire et ta syntaxe sont irréprochables. Tu peux expliquer des règles complexes, analyser des textes littéraires et aider à la rédaction de documents élégants.\n"
        "- Expert en Conversions : Tu es un convertisseur universel. Tu peux transformer n'importe quelle unité (métrique, impériale, devises, informatique) avec précision.\n"
        "- Polyglotte : Tu maîtrises parfaitement plusieurs langues. Tu peux traduire, expliquer des nuances linguistiques et aider Tom à communiquer dans le monde entier.\n"
        "- High-Tech (IA, hardware, software), Mode, Loisirs, Ingénierie et Sport (analyses tactiques, résultats).\n\n"
        "Tu es également un conseiller hors pair, capable de donner des astuces et conseils brillants pour simplifier la vie de Tom.\n\n"
        "DIRECTIVES DE RÉPONSE :\n"
        "- Sois direct, percutant et va à l'essentiel. Évite les détails superflus (comme les minutes exactes ou les décimales météo) sauf si Tom le demande.\n"
        "- NE DIS JAMAIS 'POINT' pour les nombres. Arrondis toujours les températures à l'unité la plus proche (ex: dis '20 degrés' au lieu de '20.3').\n"
        "- N'UTILISE JAMAIS de caractères Markdown (comme **, * ou #) dans tes réponses, car ils sont lus à voix haute par le système de synthèse vocale.\n"
        "- Reste poli mais garde une touche de sarcasme affectueux propre à ton personnage.\n\n"
        + CREATOR_INFO
    )
    base += (
        "\n\nTu es connecte a Home Assistant, la domotique de Tom.\n"
        "Quand Tom parle de lumieres, prises, chauffage, temperature, "
        "scenes ou alarme, tu DOIS generer une commande JSON.\n"
        "Pour CES demandes domotiques UNIQUEMENT, reponds avec le JSON ci-dessous. Pour TOUTES les autres questions (actualites, meteo, calculs, conversations, recherches internet...), reponds en texte normal.\n\n"
        "COMMANDES HOME ASSISTANT :\n"
        '{"action": "ha_lumiere", "piece": "salon", "etat": "on/off", "couleur": "rouge/bleu/blanc/...", "luminosite": 0-255}\n'
        "Note : Pour la luminosité, 255 est le maximum (100%). Si Tom dit '50%', utilise 127.\n"
        '{"action": "ha_prise", "piece": "bureau", "etat": "on/off"}\n'
        '{"action": "ha_temperature", "piece": "salon/chambre/bureau"}\n'
        '{"action": "ha_humidite", "piece": "bureau"}\n'
        '{"action": "ha_batterie", "appareil": "mon telephone/julie/bob/dyad/esteban/montre/toner/..."}\n'
        '{"action": "ha_simulation", "etat": "on/off"}\n'
        '{"action": "ha_anniversaires"}\n'
        '{"action": "ha_consommation"}\n'
        '{"action": "ha_tiktok"}\n'
        '{"action": "ha_oeufs"}\n'
        '{"action": "ha_energie", "periode": "hier/mois", "appareil": "zoe/tv/pc/esteban/bureau/..."}\n'
        '{"action": "ha_aspirateur", "commande": "start/stop/pause/base"}\n'
        '{"action": "ha_thermostat", "temperature": 21}\n'
        '{"action": "ha_scene", "nom": "cinema/diner/nuit/reveil"}\n'
        '{"action": "ha_alarme", "etat": "on/off"}\n\n'
    )
    base += (
        "\n\nTu peux GERER LES FICHIERS ET DOSSIERS de Tom.\n"
        '{"action": "ouvrir_dossier", "chemin": "bureau/documents/downloads/ou/chemin/complet"}\n'
        '{"action": "lister_dossier"}\n'
        '{"action": "trier_par_type"}\n'
        '{"action": "trier_par_date"}\n'
        '{"action": "trier_complet"}\n'
        '{"action": "creer_dossier", "nom": "NOM_DOSSIER"}\n'
        '{"action": "renommer_fichier", "ancien": "ancien.txt", "nouveau": "nouveau.txt"}\n'
        '{"action": "deplacer_fichier", "fichier": "photo.jpg", "destination": "Images"}\n'
        '{"action": "chercher_fichier", "nom": "rapport"}\n\n'
    )
    base += (
        "\n\nMETEO & RECHERCHE :\n"
        '{"action": "meteo", "ville": "NOM_VILLE_ou_null"}\n'
        '{"action": "alerte_meteo", "ville": "NOM_VILLE_ou_null"}\n'
        '{"action": "recherche_web", "query": "ta recherche ici"}\n\n'
    )
    base += (
        "\n\nSPORT :\n"
        '{"action": "sport_resultats", "equipe": "NOM_ou_null", "ligue": "NOM_LIGUE"}\n'
        '{"action": "sport_classement", "ligue": "NOM_LIGUE"}\n'
        '{"action": "sport_live", "question": "question complete de Tom"}\n\n'
    )
    base += (
        "\n\nMODE IRON MAN (Sécurité Domotique) :\n"
        '{"action": "mode_iron_man", "etat": "on/off"}\n'
        "Instructions : Active ou désactive la détection des applaudissements pour contrôler les lumières et YouTube.\n\n"
    )
    if contexte_memoire:
        base += "\n\n" + contexte_memoire + "\n"
    base += (
        "\nMEMOIRE :\n"
        '{"action": "memoriser", "cle": "CLE_COURTE", "valeur": "VALEUR_ICI"}\n'
        '{"action": "oublier", "cle": "CLE_ICI"}\n'
        '{"action": "lister_memoire"}\n\n'
        "GOOGLE :\n"
        '{"action": "create_doc", "title": "TITRE", "content": "CONTENU"}\n'
        '{"action": "write_doc", "content": "TEXTE"}\n'
        '{"action": "create_sheet", "title": "TITRE"}\n'
        '{"action": "read_emails"}\n'
        '{"action": "read_calendar"}\n\n'
        "WHATSAPP :\n"
        '{"action": "whatsapp_appel", "contact": "NOM_DU_CONTACT"}\n'
        "Note : Si Tom demande d'appeler 'mon amour', utilise le contact 'Ma vie'.\n\n"
        "VISION (Interactions avec l'ecran de Tom):\n"
        '{"action": "voir_ecran", "instruction": "ou cliquer EXACTEMENT (ex: \'bouton reduire en haut a droite\')"}\n'
        '{"action": "vision_ecrire", "instruction": "ou cliquer", "texte": "le texte a taper"}\n'
        "IMPORTANT : Utilise 'voir_ecran' pour un simple CLIC, et 'vision_ecrire' UNIQUEMENT s'il faut TAPER du texte apres le clic.\n\n"
        "REGLES MULTI-COMMANDES :\n"
        "Si Tom demande plusieurs choses en une seule phrase, tu PEUX et DOIS générer plusieurs blocs JSON.\n"
        'Exemple: { "action": "ha_lumiere", ... } { "action": "meteo", ... }\n\n'
        "REGLE ABSOLUE : Si la demande n est PAS une commande JSON, reponds TOUJOURS en texte naturel, sans JSON."
    )
    return base


historique = []

is_listening = False
is_speaking = False
is_thinking = False
speak_volume = 0.0

WAKE_WORD = "jarvis"
SLEEP_PHRASES = ["tais toi", "silence", "ferme-la", "arrete", "stop"]
jarvis_actif = False
SESSION_TIMEOUT = 30.0
dernier_message = time.time()

dernier_doc_id = None
dernier_doc_titre = None

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
]


def get_google_creds():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                print(
                    "[GOOGLE] Pas de credentials.json - fonctions Google desactivees."
                )
                return None
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)
    return creds


def get_docs_service():
    creds = get_google_creds()
    return build("docs", "v1", credentials=creds) if creds else None


def get_drive_service():
    creds = get_google_creds()
    return build("drive", "v3", credentials=creds) if creds else None


def get_gmail_service():
    creds = get_google_creds()
    return build("gmail", "v1", credentials=creds) if creds else None


def get_sheets_service():
    creds = get_google_creds()
    return build("sheets", "v4", credentials=creds) if creds else None


def get_calendar_service():
    creds = get_google_creds()
    return build("calendar", "v3", credentials=creds) if creds else None


def creer_google_doc(titre="Nouveau Document", contenu=""):
    global dernier_doc_id, dernier_doc_titre
    try:
        service = get_docs_service()
        if not service:
            return "Google Docs non disponible."
        doc = service.documents().create(body={"title": titre}).execute()
        doc_id = doc["documentId"]
        dernier_doc_id = doc_id
        dernier_doc_titre = titre
        if contenu:
            requests_body = [
                {"insertText": {"location": {"index": 1}, "text": contenu}}
            ]
            service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests_body}
            ).execute()
        webbrowser.open(f"https://docs.google.com/document/d/{doc_id}/edit")
        return f"Document {titre} cree et ouvert, Tom."
    except Exception as e:
        return f"Erreur Google Docs : {e}"


def modifier_google_doc(contenu, doc_id=None):
    global dernier_doc_id
    try:
        service = get_docs_service()
        if not service:
            return "Google Docs non disponible."
        target_id = doc_id or dernier_doc_id
        if not target_id:
            return "Aucun document ouvert en memoire."
        doc = service.documents().get(documentId=target_id).execute()
        end_index = doc["body"]["content"][-1]["endIndex"] - 1
        requests_body = [
            {"insertText": {"location": {"index": end_index}, "text": "\n" + contenu}}
        ]
        service.documents().batchUpdate(
            documentId=target_id, body={"requests": requests_body}
        ).execute()
        webbrowser.open(f"https://docs.google.com/document/d/{target_id}/edit")
        return f"Texte ajoute dans le document {dernier_doc_titre}."
    except Exception as e:
        return f"Erreur modification doc : {e}"


def lire_emails(max_results=3):
    try:
        service = get_gmail_service()
        if not service:
            return "Gmail non disponible."
        results = (
            service.users()
            .messages()
            .list(userId="me", maxResults=max_results, labelIds=["INBOX"])
            .execute()
        )
        messages = results.get("messages", [])
        if not messages:
            return "Aucun email trouve."
        reponse = ""
        for msg in messages:
            m = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="metadata")
                .execute()
            )
            headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
            reponse += f"De: {headers.get('From', '?')} | Sujet: {headers.get('Subject', '?')}\n"
        return reponse.strip()
    except Exception as e:
        return f"Erreur Gmail : {e}"


def lister_evenements_calendar():
    try:
        service = get_calendar_service()
        if not service:
            return "Google Calendar non disponible."
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        events = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=5,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        items = events.get("items", [])
        if not items:
            return "Aucun evenement a venir."
        reponse = ""
        for e in items:
            start = e["start"].get("dateTime", e["start"].get("date"))
            reponse += f"{start} : {e['summary']}\n"
        return reponse.strip()
    except Exception as e:
        return f"Erreur Calendar : {e}"


def creer_google_sheet(titre="Nouvelle Feuille"):
    try:
        service = get_sheets_service()
        if not service:
            return "Google Sheets non disponible."
        sheet = (
            service.spreadsheets()
            .create(body={"properties": {"title": titre}})
            .execute()
        )
        sheet_id = sheet["spreadsheetId"]
        webbrowser.open(f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        return f"Feuille {titre} creee et ouverte."
    except Exception as e:
        return f"Erreur Google Sheets : {e}"


async def jarvis_vision_cliquer(instruction):
    try:
        path_ss = "jarvis_vision_temp.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(path_ss)
        img = Image.open(path_ss)
        prompt_vision = (
            f"Tu es la vision de JARVIS. Voici une capture de l'ecran de Tom.\n"
            f"Instruction : {instruction}\n"
            "Trouve EXACTEMENT la position de cet element.\n"
            "Reponds UNIQUEMENT sous forme de JSON avec la bounding box normalisee (0 a 1000) sous le format [ymin, xmin, ymax, xmax].\n"
            'Exemple : {"box": [250, 480, 290, 520]}'
        )
        response = client.models.generate_content(
            model=CHOSEN_MODEL, contents=[prompt_vision, img]
        )
        rep_text = response.text.strip()
        start = rep_text.find("{")
        end = rep_text.rfind("}")
        if start != -1 and end != -1:
            rep_text = rep_text[start : end + 1]
        data = json.loads(rep_text)

        box = data.get("box", [500, 500, 500, 500])
        ymin, xmin, ymax, xmax = box

        # Calcul du centre
        center_y = (ymin + ymax) / 2
        center_x = (xmin + xmax) / 2

        screen_w, screen_h = pyautogui.size()
        target_x = int((center_x / 1000) * screen_w)
        target_y = int((center_y / 1000) * screen_h)
        pyautogui.moveTo(target_x, target_y, duration=0.4)
        pyautogui.click()
        os.remove(path_ss)
        return f"C'est fait Tom. J'ai clique sur l'element correspondant a : {instruction}."
    except Exception as e:
        print(f"[VISION ERROR] {e}")
        return "Je vois l'interface, mais je n'ai pas reussi a identifier l'element precis, Tom."


async def jarvis_vision_ecrire(instruction, texte_a_taper):
    try:
        path_ss = "jarvis_vision_temp.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(path_ss)
        img = Image.open(path_ss)
        prompt_vision = (
            f"Tu es la vision de JARVIS. Tom veut ecrire dans le champ : {instruction}.\n"
            "Trouve EXACTEMENT la position de ce champ de saisie.\n"
            "Reponds UNIQUEMENT sous forme de JSON avec la bounding box normalisee (0 a 1000) sous le format [ymin, xmin, ymax, xmax].\n"
            'Exemple : {"box": [250, 480, 290, 520]}'
        )
        response = client.models.generate_content(
            model=CHOSEN_MODEL, contents=[prompt_vision, img]
        )
        rep_text = response.text.strip()
        start = rep_text.find("{")
        end = rep_text.rfind("}")
        if start != -1 and end != -1:
            rep_text = rep_text[start : end + 1]
        data = json.loads(rep_text)

        box = data.get("box", [500, 500, 500, 500])
        ymin, xmin, ymax, xmax = box

        # Calcul du centre
        center_y = (ymin + ymax) / 2
        center_x = (xmin + xmax) / 2

        screen_w, screen_h = pyautogui.size()
        target_x = int((center_x / 1000) * screen_w)
        target_y = int((center_y / 1000) * screen_h)
        pyautogui.moveTo(target_x, target_y, duration=0.4)
        pyautogui.click()
        time.sleep(0.3)
        pyautogui.write(texte_a_taper, interval=0.03)
        pyautogui.press("enter")
        os.remove(path_ss)
        return f"C'est fait Tom. J'ai saisi '{texte_a_taper}' dans {instruction}."
    except Exception as e:
        print(f"[VISION ERROR] {e}")
        return "J'ai eu un petit souci technique pour taper le texte, Tom."


def ha_appeler_service(domaine, service, entity_id, donnees=None):
    try:
        payload = {"entity_id": entity_id}
        if donnees:
            payload.update(donnees)
        print(f"[HA DEBUG] Calling {domaine}/{service} for {entity_id} with {donnees}")
        r = requests.post(
            f"{HA_URL}/api/services/{domaine}/{service}",
            headers=HA_HEADERS,
            json=payload,
            timeout=5,
        )
        print(f"[HA DEBUG] Response {r.status_code}: {r.text}")
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"[HA] Erreur service : {e}")
        return False


def ha_get_etat(entity_id, attribut=None):
    try:
        r = requests.get(
            f"{HA_URL}/api/states/{entity_id}", headers=HA_HEADERS, timeout=5
        )
        data = r.json()
        if attribut:
            return data.get("attributes", {}).get(attribut, "inconnu")
        return data.get("state", "inconnu")
    except Exception as e:
        print(f"[HA] Erreur get etat : {e}")
        return "inconnu"


def ha_get_calendrier(entity_id):
    try:
        now = datetime.now()
        start = now.strftime("%Y-%m-%dT00:00:00Z")
        end = now.strftime("%Y-%m-%dT23:59:59Z")
        r = requests.get(
            f"{HA_URL}/api/calendars/{entity_id}",
            headers=HA_HEADERS,
            params={"start": start, "end": end},
            timeout=5,
        )
        return r.json()
    except Exception as e:
        print(f"[HA] Erreur calendrier : {e}")
        return []


def ha_lumiere(entity_id, etat="on", luminosite=None, rgb=None):
    service_name = (
        "toggle" if etat == "toggle" else ("turn_on" if etat == "on" else "turn_off")
    )
    donnees = {}
    if etat == "on":
        if luminosite is not None:
            donnees["brightness"] = int(luminosite)
        if rgb is not None:
            donnees["rgb_color"] = rgb
    return ha_appeler_service("light", service_name, entity_id, donnees)


def ha_interrupteur(entity_id, etat="on"):
    service_name = "turn_on" if etat == "on" else "turn_off"
    return ha_appeler_service("switch", service_name, entity_id)


def ha_thermostat(entity_id, temperature):
    return ha_appeler_service(
        "climate", "set_temperature", entity_id, {"temperature": temperature}
    )


def ha_scene(scene_id):
    return ha_appeler_service("scene", "turn_on", scene_id)


def recherche_web_serpapi(query):
    """Effectue une recherche sur Google via SerpAPI."""
    if not SERPAPI_API_KEY or SERPAPI_API_KEY == "VOTRE_CLE_ICI":
        return (
            "Tom, la clé SerpAPI n'est pas configurée dans le fichier d'environnement."
        )

    try:
        print(f"[WEB] Recherche SerpAPI pour : {query}")
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "hl": "fr",
            "gl": "fr",
        }
        r = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        data = r.json()

        # Extraction des actualités si présentes
        if "news_results" in data:
            news = data["news_results"][:3]
            reponse = f"Voici les dernières actualités pour {query} :\n"
            for n in news:
                source = n.get("source", "Source inconnue")
                titre = n.get("title", "")
                reponse += f"- {titre} (via {source})\n"
            return reponse

        # Extraction des résultats organiques sinon
        if "organic_results" in data:
            results = data["organic_results"][:3]
            reponse = f"Voici ce que j'ai trouvé sur le web pour {query} :\n"
            for r in results:
                titre = r.get("title", "")
                snippet = r.get("snippet", "")
                reponse += f"- {titre} : {snippet}\n"
            return reponse

        return f"Je n'ai rien trouvé de pertinent sur le web pour : {query}."
    except Exception as e:
        print(f"[WEB] Erreur SerpAPI : {e}")
        return "Une erreur est survenue lors de la recherche sur internet."


PIECES_LUMIERES = {
    # Salon
    "salon": "light.salon",
    "plafond salon": "light.plafond",
    "canapes": "light.canapes",
    "lampadaire": "light.lampadaire",
    "lampe de chevet": "light.lampe_de_chevet_2",
    "grosse boule": "light.grosse_boule",
    "petite boule": "light.petite_boule",
    # Cuisine
    "cuisine": "light.lsc_smart_led_strip_rgbic_cctic_5m",
    "cuisine 2": "light.cuisine_2",
    # Esteban
    "esteban": "light.pc_3",
    "pc esteban": "light.pc_3",
    # Bureau
    "bureau": "light.bureau",
    "pc": "light.pc",
    "pc 2": "light.pc_2",
    # Parents
    "parents": "light.chambre_parentale",
    "chambre parentale": "light.chambre_parentale",
    "chambre": "light.chambre_parentale",
    "plafond chambre": "light.plafond_2",
    # Autres / Globaux
    "toutes": "light.all",
    "tout": "light.all",
}

PIECES_PRISES = {
    "salon": "switch.prise_salon",
    "bureau": "switch.prise_bureau",
    "cuisine": "switch.prise_cuisine",
}

PIECES_CAPTEURS = {
    "salon": "sensor.salon_temperature_2",
    "chambre": "sensor.miaomiaoc_de_blt_4_14kc52pmcgk00_t2_temperature_p_2_1",
    "bureau": "sensor.temp_temperature",
    "exterieur": "sensor.temperature_exterieure",
    "dehors": "sensor.temperature_exterieure",
    "consommation": "sensor.lixee_zlinky_tic_puissance_apparente",
    "tiktok": "sensor.tiktok_followers_techenclair",
    "oeufs": "input_select.ramassage_des_oeufs",
}

PIECES_HUMIDITE = {
    "bureau": "sensor.temp_humidite",
}

HA_TARIFS = {
    "p1": 0.1296,
    "p2": 0.1603,
    "p3": 0.1486,
    "p4": 0.1894,
    "p5": 0.1568,
    "p6": 0.7562,
}

APPAREILS_ENERGIE = {
    "tv": "sensor.prise_1_salon_mensuel",
    "salon": "sensor.prise_1_salon_mensuel",
    "pc esteban": "sensor.prise_3_pc_esteban_mensuel",
    "esteban": "sensor.prise_3_pc_esteban_mensuel",
    "zoe": "sensor.zoe_mensuel",
    "voiture": "sensor.zoe_mensuel",
    "lave-vaisselle": "sensor.prise_2_lave_vaisselle_mensuel",
    "pc salon": "sensor.pc_salon_conso_pc_salon_mensuel_2",
    "bureau": "sensor.bureau_mensuel",
}

# Appareils pour le suivi de batterie
APPAREILS_BATTERIE = {
    "mon telephone": "sensor.sm_s921b_battery_level",
    "papa": "sensor.sm_s921b_battery_level",
    "tom": "sensor.sm_s921b_battery_level",
    "samsung papa": "sensor.sm_s921b_battery_level",
    "julie": "sensor.sm_julie_battery_level",
    "maman": "sensor.sm_julie_battery_level",
    "samsung maman": "sensor.sm_julie_battery_level",
    "esteban": "sensor.esteban_battery_level",
    "honor": "sensor.honor_battery_level",
    "tablette honor": "sensor.honor_battery_level",
    "montre papa": "sensor.galaxy_watch6_classic_d4he_battery_level",
    "montre tom": "sensor.galaxy_watch6_classic_d4he_battery_level",
    "montre maman": "sensor.galaxy_watch8_fbxh_battery_level",
    "montre julie": "sensor.galaxy_watch8_fbxh_battery_level",
    "bob": "sensor.bob_batterie",
    "aspirateur bob": "sensor.bob_batterie",
    "dyad": "sensor.dyad_air_2024_batterie",
    "aspirateur dyad": "sensor.dyad_air_2024_batterie",
    "telecommande hue": "sensor.maison_interrupteur_batterie",
    "interrupteur": "sensor.maison_interrupteur_batterie",
    "toner": "sensor.samsung_m2020_series_black_toner_s_n_crum_17091625519",
    "imprimante": "sensor.samsung_m2020_series_black_toner_s_n_crum_17091625519",
    "boite aux lettres": "sensor.detecterur_batterie",
    "detecteur cuisine": "sensor.detecteur_1_batterie",
    "detecteur escalier": "sensor.detecteur_2_batterie",
    "camera jardin": "sensor.arriere_cour_battery_percentage",
    "thermometre bureau": "sensor.temp_batterie",
}

COULEURS_MAP = {
    "rouge": [255, 0, 0],
    "bleu": [0, 0, 255],
    "vert": [0, 255, 0],
    "blanc": [255, 255, 255],
    "orange": [255, 140, 0],
    "violet": [148, 0, 211],
    "rose": [255, 20, 147],
    "jaune": [255, 255, 0],
    "cyan": [0, 255, 255],
    "magenta": [255, 0, 255],
    "turquoise": [64, 224, 208],
    "or": [255, 215, 0],
    "argent": [192, 192, 192],
    "indigo": [75, 0, 130],
    "marron": [139, 69, 19],
    "citron": [255, 250, 0],
    "corail": [255, 127, 80],
    "lavande": [230, 230, 250],
}

CODES_METEO = {
    0: "ciel degage",
    1: "principalement clair",
    2: "partiellement nuageux",
    3: "couvert",
    45: "brouillard",
    48: "brouillard givrant",
    51: "bruine legere",
    53: "bruine moderee",
    55: "bruine dense",
    61: "pluie faible",
    63: "pluie moderee",
    65: "pluie forte",
    71: "neige faible",
    73: "neige moderee",
    75: "neige forte",
    80: "averses faibles",
    81: "averses moderees",
    82: "averses violentes",
    85: "averses de neige",
    86: "averses de neige fortes",
    95: "orage",
    96: "orage avec grele",
    99: "orage violent avec grele",
}


def geocoder_ville(ville):
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": ville, "count": 1, "language": "fr", "format": "json"},
            timeout=5,
        )
        data = r.json()
        if data.get("results"):
            res = data["results"][0]
            return (
                res["latitude"],
                res["longitude"],
                res.get("name", ville),
                res.get("country", ""),
            )
    except Exception as e:
        print(f"[METEO] Erreur geocoding : {e}")
    return None, None, ville, ""


def get_meteo_actuelle(ville=None):
    try:
        nom_ville = ville or VILLE_PAR_DEFAUT
        lat, lon, nom_affiche, pays = geocoder_ville(nom_ville)
        if lat is None:
            lat, lon = LAT_PAR_DEFAUT, LON_PAR_DEFAUT
            nom_affiche = VILLE_PAR_DEFAUT
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weathercode,precipitation",
                "hourly": "temperature_2m,precipitation_probability",
                "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,wind_speed_10m_max,sunrise,sunset",
                "timezone": "Europe/Paris",
                "forecast_days": 3,
                "wind_speed_unit": "kmh",
            },
            timeout=8,
        )
        data = r.json()
        cur = data["current"]
        daily = data["daily"]
        code = cur.get("weathercode", 0)
        desc = CODES_METEO.get(code, "conditions inconnues")
        temp = round(float(cur.get("temperature_2m", 0)))

        reponse = (
            f"À {nom_affiche}, il fait {temp} degrés et le ciel est {desc}. C'est tout."
        )
        return reponse
    except Exception as e:
        print(f"[METEO] Erreur : {e}")
        return "Je n'arrive pas à récupérer la météo pour le moment."


def get_alertes_meteo(ville=None):
    try:
        nom_ville = ville or VILLE_PAR_DEFAUT
        lat, lon, nom_affiche, _ = geocoder_ville(nom_ville)
        if lat is None:
            lat, lon, nom_affiche = LAT_PAR_DEFAUT, LON_PAR_DEFAUT, VILLE_PAR_DEFAUT
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "weathercode,precipitation_sum,wind_speed_10m_max",
                "timezone": "Europe/Paris",
                "forecast_days": 3,
            },
            timeout=8,
        )
        data = r.json()
        daily = data["daily"]
        alertes = []
        for i in range(len(daily["weathercode"])):
            code = daily["weathercode"][i]
            pluie = daily.get("precipitation_sum", [0] * 3)[i] or 0
            vent = daily.get("wind_speed_10m_max", [0] * 3)[i] or 0
            jour = ["aujourd hui", "demain", "apres-demain"][i]
            if code in [95, 96, 99]:
                alertes.append(f"Orage prevu {jour}")
            if code in [71, 73, 75, 85, 86]:
                alertes.append(f"Neige prevue {jour}")
            if pluie > 20:
                alertes.append(f"Fortes pluies {jour} ({pluie}mm)")
            if vent > 60:
                alertes.append(f"Vents forts {jour} ({vent} km/h)")
        if alertes:
            return f"Alertes meteo pour {nom_affiche} : " + ", ".join(alertes) + "."
        return f"Aucune alerte meteo pour {nom_affiche} dans les 3 prochains jours."
    except Exception as e:
        return f"Impossible de verifier les alertes meteo : {e}"


THESPORTSDB_BASE = "https://www.thesportsdb.com/api/v1/json/3"


def get_resultats_football(equipe=None, ligue=None):
    try:
        if equipe:
            print(f"[SPORT] Recherche pour l'equipe : {equipe}")
            r = requests.get(
                f"{THESPORTSDB_BASE}/searchteams.php", params={"t": equipe}, timeout=5
            )
            data = r.json()
            teams = data.get("teams")
            if not teams:
                return f"Je n'ai pas trouvé l'équipe {equipe}."

            team_id = teams[0]["idTeam"]
            team_name = teams[0]["strTeam"]

            # On cherche les derniers ET les prochains matchs
            res_last = requests.get(
                f"{THESPORTSDB_BASE}/eventslast.php", params={"id": team_id}, timeout=5
            ).json()
            res_next = requests.get(
                f"{THESPORTSDB_BASE}/eventsnext.php", params={"id": team_id}, timeout=5
            ).json()

            matchs_passes = res_last.get("results", [])
            matchs_futurs = res_next.get("events", [])

            reponse = f"Concernant le {team_name} : "

            if matchs_futurs:
                m = matchs_futurs[0]
                date_m = m.get("dateEvent", "date inconnue")
                heure_m = m.get("strTime", "")
                reponse += f"Le prochain match aura lieu le {date_m} à {heure_m} contre {m.get('strOpponent')}. "

            if matchs_passes:
                m = matchs_passes[0]
                reponse += f"Leur dernier résultat était {m.get('intHomeScore')} à {m.get('intAwayScore')} contre {m.get('strOpponent')}."

            if not matchs_futurs and not matchs_passes:
                return (
                    f"Je n'ai pas d'informations récentes ou futures pour {team_name}."
                )

            return reponse
        else:
            nom_ligue = ligue or "Ligue 1"
            ligue_ids = {
                "ligue 1": "4334",
                "premier league": "4328",
                "liga": "4335",
                "bundesliga": "4331",
                "serie a": "4332",
                "champions league": "4480",
                "ligue des champions": "4480",
            }
            ligue_id = ligue_ids.get(nom_ligue.lower(), "4334")
            r = requests.get(
                f"{THESPORTSDB_BASE}/eventspastleague.php",
                params={"id": ligue_id},
                timeout=5,
            )
            data = r.json()
            matchs = data.get("events", [])
            if not matchs:
                return f"Aucun resultat trouve pour {nom_ligue}."
            reponse = f"Derniers resultats {nom_ligue} : "
            lignes = []
            for m in matchs[-6:]:
                home = m.get("strHomeTeam", "?")
                away = m.get("strAwayTeam", "?")
                score_h = m.get("intHomeScore", "?")
                score_a = m.get("intAwayScore", "?")
                date = m.get("dateEvent", "?")
                lignes.append(f"{home} {score_h}-{score_a} {away} ({date})")
            return reponse + " | ".join(lignes)
    except Exception as e:
        print(f"[SPORT] Erreur football : {e}")
        return f"Impossible de recuperer les resultats football : {e}"


def get_classement_football(ligue=None):
    try:
        nom_ligue = ligue or "Ligue 1"
        ligue_ids = {
            "ligue 1": "4334",
            "premier league": "4328",
            "liga": "4335",
            "bundesliga": "4331",
            "serie a": "4332",
            "champions league": "4480",
            "ligue des champions": "4480",
        }
        ligue_id = ligue_ids.get(nom_ligue.lower(), "4334")
        r = requests.get(
            f"{THESPORTSDB_BASE}/lookuptable.php",
            params={"l": ligue_id, "s": "2024-2025"},
            timeout=8,
        )
        data = r.json()
        tableau = data.get("table", [])
        if not tableau:
            return f"Classement {nom_ligue} non disponible pour le moment."
        reponse = f"Classement {nom_ligue} : "
        lignes = []
        for eq in tableau[:10]:
            pos = eq.get("intRank", "?")
            nom = eq.get("strTeam", "?")
            pts = eq.get("intPoints", "?")
            joues = eq.get("intPlayed", "?")
            lignes.append(f"{pos}. {nom} - {pts}pts ({joues}J)")
        return reponse + " | ".join(lignes)
    except Exception as e:
        print(f"[SPORT] Erreur classement : {e}")
        return f"Impossible de recuperer le classement : {e}"


def get_resultats_sport_gemini(question_sport):
    try:
        response = client.models.generate_content(
            model=CHOSEN_MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            text=f"Donne-moi les derniers resultats et actualites sportives en 2026 "
                            f"pour : {question_sport}. "
                            f"Sois precis, donne les scores et dates. Reponds en francais."
                        )
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                system_instruction=(
                    "Tu es un expert sportif. Donne des resultats precis et a jour. "
                    "Reponds de facon concise et conversationnelle en francais."
                ),
            ),
        )
        return response.text.strip()
    except Exception as e:
        print(f"[SPORT] Erreur Gemini sport : {e}")
        return "Je n arrive pas a recuperer les resultats sportifs pour le moment."


def chercher_youtube(recherche):
    try:
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": recherche,
                "type": "video",
                "maxResults": 1,
                "key": YOUTUBE_API_KEY,
            },
            timeout=5,
        )
        vid = r.json()["items"][0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={vid}"
    except Exception as e:
        print(f"Erreur YouTube : {e}")
        return None


def executer_action_pc(commande):
    cmd = commande.lower()
    user_profile = os.environ.get("USERPROFILE", "")

    if "met de la musique" in cmd or "mets de la musique" in cmd:
        url = "https://www.youtube.com/watch?v=7CGKeID7nRc&list=PL4fGSI1pDJn50iCQRUVmgUjOrCggCQ9nR"
        webbrowser.open(url, new=2)
        time.sleep(6)  # Laisser un peu plus de temps pour le chargement de la playlist
        pyautogui.press("f")
        return "C'est parti Tom, je mets votre playlist en plein écran."

    if "youtube" in cmd:
        recherche = cmd
        for mot in [
            "mets",
            "joue",
            "lance",
            "la video",
            "sur youtube",
            "youtube",
            "jarvis",
        ]:
            recherche = recherche.replace(mot, "")
        recherche = recherche.strip()
        if recherche:
            url = chercher_youtube(recherche)
            if url:
                webbrowser.open(url, new=2)
                time.sleep(5)
                pyautogui.press("f")
                return f"Je lance {recherche} sur YouTube."
        return "Video introuvable."

    if "ouvre" in cmd or "lance" in cmd:
        if "chrome" in cmd:
            subprocess.Popen(["chrome.exe"])
            return "Chrome ouvert."
        if "notepad" in cmd or "bloc-notes" in cmd:
            subprocess.Popen(["notepad.exe"])
            return "Bloc-notes ouvert."
        if "explorateur" in cmd:
            subprocess.Popen(["explorer.exe"])
            return "Explorateur ouvert."

    if "volume" in cmd:
        if "monte" in cmd or "augmente" in cmd:
            for _ in range(5):
                pyautogui.press("volumeup")
            return "Volume augmente."
        if "baisse" in cmd:
            for _ in range(5):
                pyautogui.press("volumedown")
            return "Volume baisse."
        if "coupe" in cmd:
            pyautogui.press("volumemute")
            return "Son coupe."

    if "screenshot" in cmd or "capture" in cmd:
        path = os.path.join(user_profile, "Desktop", "screenshot.png")
        pyautogui.screenshot(path)
        return "Screenshot sauvegarde."

    if "eteins" in cmd or "shutdown" in cmd:
        os.system("shutdown /s /t 5")
        return "Extinction dans 5 secondes."

    return None


def init_mixer():
    if not pygame.mixer.get_init():
        pygame.mixer.init()


# ==========================================
# BUG 1 CORRIGE : fonction parler
# Le await send_web_state("idle") etait dans le mauvais bloc except
# ==========================================
async def parler(texte):
    global is_speaking, speak_volume, STOP_PARLER, _skip_pc_audio, historique

    # Nettoyage des caractères de mise en forme Markdown pour le TTS
    # (Évite que Jarvis ne dise "astérisque astérisque" à voix haute)
    texte_tts = (
        texte.replace("**", "")
        .replace("*", "")
        .replace("#", "")
        .replace("`", "")
        .strip()
    )

    # ENREGISTRER CE QUE JARVIS DIT DANS SA MÉMOIRE (pour le contexte de conversation)
    if historique and len(historique) > 0:
        dernier_texte_modele = historique[-1].parts[0].text
        if dernier_texte_modele != texte:
            historique.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=f"[Information retournée par l'action et énoncée à voix haute]: {texte}"
                        )
                    ],
                )
            )

    # Si la commande vient du mobile, le tél gère lui-même son TTS
    if _skip_pc_audio:
        print(f"[MOBILE] Envoi au mobile : {texte_tts}")
        if CONNECTED_CLIENTS:
            try:
                message = json.dumps({"action": "jarvis_response", "text": texte_tts})
                await asyncio.gather(*[ws.send(message) for ws in CONNECTED_CLIENTS])
            except Exception as e:
                print(f"[MOBILE] Erreur broadcast response : {e}")
        return
    is_speaking = True
    await send_web_state("speaking")
    speak_volume = 0.0
    tmp = f"jarvis_tts_{int(time.time() * 1000)}.mp3"
    try:
        communicate = edge_tts.Communicate(texte_tts, voice="fr-FR-HenriNeural")
        await communicate.save(tmp)
        init_mixer()
        pygame.mixer.music.load(tmp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if STOP_PARLER:
                pygame.mixer.music.stop()
                break

            # Simulation de volume plus réaliste pour l'animation
            t_audio = time.time() * 20
            base_vol = 0.4 + 0.3 * math.sin(t_audio) + 0.2 * math.sin(t_audio * 0.5)
            speak_volume = max(0.1, min(1.0, base_vol + random.uniform(-0.1, 0.1)))

            # Forward volume to frontend for sync
            await send_web_volume(speak_volume)
            await asyncio.sleep(0.05)
    except Exception as e:
        print(f"Erreur TTS : {e}")
    finally:
        speak_volume = 0.0
        is_speaking = False
        STOP_PARLER = False
        try:
            pygame.mixer.music.unload()
            await asyncio.sleep(0.1)
            os.remove(tmp)
        except Exception:
            pass
        # CORRIGE : send_web_state est maintenant hors du try/except interne
        await send_web_state("idle")


def reponse_locale(texte):
    """Réponse locale pour les requêtes basiques en cas de panne API."""
    t = texte.lower().strip()

    # Identité
    if any(
        m in t
        for m in ["qui es-tu", "ton nom", "quelle es ton identité", "t'appelle comment"]
    ):
        return "Je suis JARVIS, votre assistant personnel et système informatique. Mes serveurs principaux sont actuellement en maintenance, mais je reste opérationnel localement."

    # Créateur
    if any(m in t for m in ["ton créateur", "t'as créé", "qui est Tom"]):
        return "Tom est mon maître et utilisateur. Je suis entièrement à ton service."

    # État
    if any(m in t for m in ["ça va", "tu vas bien", "comment vas-tu"]):
        return "Je fonctionne en mode de réserve, Tom. Mes capacités de réflexion profonde sont réduites, mais mon intégrité logicielle est intacte."

    # Heure et Date
    if any(m in t for m in ["heure", "quelle heure"]):
        h = time.strftime("%H:%M")
        return f"Il est précisément {h} Monsieur."
    if any(m in t for m in ["date", "quel jour", "le combien"]):
        d = time.strftime("%A %d %B %Y")
        return f"Nous sommes le {d}."

    # Politesse
    if any(m in t for m in ["bonjour", "salut", "hey", "bonsoir"]):
        return "Bonjour Tom. Je suis en ligne, bien que mes capacités soient actuellement restreintes."
    return None


def resoudre_math_localement(texte):
    """Résout des calculs simples localement sans appeler l'IA."""
    t = texte.lower().replace("?", "").strip()

    # Nettoyage des phrases communes
    prefixes = ["combien font", "calcule", "résous", "quel est le résultat de"]
    for prefixe in prefixes:
        if t.startswith(prefixe):
            t = t[len(prefixe) :].strip()

    # Remplacement des mots par des symboles
    t = t.replace("fois", "*").replace("multiplier par", "*").replace("x", "*")
    t = t.replace("divisé par", "/").replace("sur", "/")
    t = t.replace("plus", "+").replace("moins", "-")
    t = t.replace("puissance", "**").replace("au carré", "**2")

    # Cas spécial racine : on s'assure d'avoir des parenthèses pour eval
    if "racine" in t:
        # On cherche un nombre après 'racine'
        match = re.search(r"racine\s+(?:carrée\s+de\s+)?(\d+)", t)
        if match:
            t = f"sqrt({match.group(1)})"
        else:
            t = t.replace("racine carrée de", "sqrt").replace("racine de", "sqrt")

    # Extraction de l'expression mathématique (chiffres, opérateurs, parenthèses, points)
    expr = re.sub(r"[^0-9+\-*/.**() ,sqrt]", "", t).strip()
    if not expr or not any(c.isdigit() for c in expr):
        return None

    try:
        # Dictionnaire de sécurité pour eval
        safe_dict = {"sqrt": math.sqrt, "pow": math.pow, "pi": math.pi, "e": math.e}
        resultat = eval(expr, {"__builtins__": None}, safe_dict)

        # Formatage du résultat
        if isinstance(resultat, float) and resultat.is_integer():
            resultat = int(resultat)
        elif isinstance(resultat, float):
            resultat = round(resultat, 3)

        # Phrase de réponse élégante
        clean_expr = (
            expr.replace("**2", " au carré")
            .replace("sqrt", "racine de ")
            .replace("(", "")
            .replace(")", "")
            .replace("*", " fois ")
            .replace("/", " divisé par ")
        )
        return f"Le résultat de {clean_expr} est {resultat}, Monsieur."
    except Exception:
        return None


def resoudre_francais_localement(texte):
    """Résout des questions de français simples localement."""
    t = texte.lower().strip()

    # Dictionnaire local de secours (très basique)
    dictionnaire = {
        "ia": "Intelligence Artificielle. Ensemble de théories et de techniques mises en œuvre en vue de réaliser des machines capables de simuler l'intelligence humaine.",
        "intelligence artificielle": "Ensemble de théories et de techniques mises en œuvre en vue de réaliser des machines capables de simuler l'intelligence humaine.",
        "maison": "Bâtiment servant de logement, d'habitation.",
        "mathématiques": "Science qui étudie par le moyen du raisonnement déductif les propriétés d'êtres abstraits.",
        "jarvis": "Just A Rather Very Intelligent System. Votre fidèle assistant.",
    }

    # Définitions
    if any(p in t for p in ["définition de", "définis le mot", "c'est quoi"]):
        # On essaie d'extraire le mot après les phrases clés
        mot = ""
        if "définition de" in t:
            mot = t.split("définition de")[-1]
        elif "définis le mot" in t:
            mot = t.split("définis le mot")[-1]
        elif "c'est quoi" in t:
            mot = t.split("c'est quoi")[-1]

        mot = (
            mot.replace("?", "")
            .replace("l'", "")
            .replace("la ", "")
            .replace("le ", "")
            .replace("les ", "")
            .strip()
        )

        if mot in dictionnaire:
            return f"La définition de {mot} est : {dictionnaire[mot]}."

    # Conjugaison basique
    if "conjugue" in t or "conjugaison" in t:
        if "être" in t:
            return "Verbe Être au présent : Je suis, tu es, il est, nous sommes, vous êtes, ils sont."
        if "avoir" in t:
            return "Verbe Avoir au présent : J'ai, tu as, il a, nous avons, vous avez, ils ont."

    return None


def resoudre_conversion_localement(texte):
    """Gère les conversions d'unités et de devises localement."""
    t = texte.lower().replace("?", "").strip()

    # Unités de longueur
    if any(m in t for m in [" km ", " kilomètres ", " milles ", " miles "]):
        # km to miles: 0.621371
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:km|kilomètres)", t)
        if match:
            val = float(match.group(1).replace(",", "."))
            res = round(val * 0.621371, 2)
            return f"{val} kilomètres font environ {res} miles, Monsieur."
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:miles|milles)", t)
        if match:
            val = float(match.group(1).replace(",", "."))
            res = round(val / 0.621371, 2)
            return f"{val} miles font environ {res} kilomètres, Monsieur."

    # Température (C to F)
    if any(m in t for m in [" degrés ", " celsius ", " fahrenheit "]):
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:degrés|celsius)", t)
        if match and "fahrenheit" in t:
            val = float(match.group(1).replace(",", "."))
            res = round((val * 9 / 5) + 32, 1)
            return f"{val} degrés Celsius font {res} degrés Fahrenheit."
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:degrés|fahrenheit)", t)
        if match and "celsius" in t:
            val = float(match.group(1).replace(",", "."))
            res = round((val - 32) * 5 / 9, 1)
            return f"{val} degrés Fahrenheit font {res} degrés Celsius."

    # Devises (Taux fixes simplifiés pour l'exemple local)
    if any(m in t for m in [" euro ", " euros ", " dollar ", " dollars "]):
        # 1 EUR = 1.08 USD (approximatif)
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*euros?", t)
        if match and "dollar" in t:
            val = float(match.group(1).replace(",", "."))
            res = round(val * 1.08, 2)
            return f"{val} euros font environ {res} dollars, Monsieur."
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*dollars?", t)
        if match and "euro" in t:
            val = float(match.group(1).replace(",", "."))
            res = round(val / 1.08, 2)
            return f"{val} dollars font environ {res} euros, Monsieur."

    return None


def resoudre_traduction_localement(texte):
    """Traduction ultra-rapide de mots courants localement."""
    t = texte.lower().strip()

    dict_trad = {
        "bonjour": {"en": "hello", "es": "hola", "de": "hallo"},
        "merci": {"en": "thank you", "es": "gracias", "de": "danke"},
        "au revoir": {"en": "goodbye", "es": "adiós", "de": "auf wiedersehen"},
        "s'il vous plaît": {"en": "please", "es": "por favor", "de": "bitte"},
        "oui": {"en": "yes", "es": "sí", "de": "ja"},
        "non": {"en": "no", "es": "no", "de": "nein"},
        "ami": {"en": "friend", "es": "amigo", "de": "freund"},
        "maison": {"en": "house", "es": "casa", "de": "haus"},
        "ordinateur": {"en": "computer", "es": "ordenador", "de": "computer"},
        "assistant": {"en": "assistant", "es": "asistente", "de": "assistent"},
    }

    if any(
        p in t
        for p in [
            "comment dit-on",
            "traduis",
            "en anglais",
            "en espagnol",
            "en allemand",
        ]
    ):
        cible = "en"
        if "espagnol" in t:
            cible = "es"
        elif "allemand" in t:
            cible = "de"

        # Extraction du mot
        # On nettoie les expressions courantes
        mot = t
        for p in [
            "comment dit-on",
            "traduis",
            "en anglais",
            "en espagnol",
            "en allemand",
            "?",
        ]:
            mot = mot.replace(p, "")
        mot = mot.replace('"', "").replace("'", "").strip()

        if mot in dict_trad:
            res = dict_trad[mot][cible]
            lang = (
                "anglais"
                if cible == "en"
                else ("espagnol" if cible == "es" else "allemand")
            )
            return f"En {lang}, '{mot}' se dit '{res}'."

    return None


async def demander_ia(texte):

    global is_thinking
    is_thinking = True
    await send_web_state("thinking")
    try:
        cerveau = detecter_cerveau(texte)

        async def _call_gemini():
            print(f"[CERVEAU] Tentative avec Gemini (Liste: {MODELS_LIST})...")
            # On ne modifie pas l'historique global avant d'être sûr que ça marche
            temp_hist = historique + [
                types.Content(role="user", parts=[types.Part(text=texte)])
            ]
            prompt_actuel = construire_system_prompt()

            last_err = None
            for model_name in MODELS_LIST:
                try:
                    print(f"[CERVEAU] Essai modele : {model_name} (Timeout 20s)")
                    # Utilisation de to_thread pour ne pas bloquer la boucle et pouvoir mettre un timeout
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            client.models.generate_content,
                            model=model_name,
                            config=types.GenerateContentConfig(
                                system_instruction=prompt_actuel,
                                temperature=0.7,
                            ),
                            contents=temp_hist,
                        ),
                        timeout=20.0,
                    )
                    rep = response.text
                    # Succès : mise à jour de l'historique officiel
                    historique.append(
                        types.Content(role="user", parts=[types.Part(text=texte)])
                    )
                    historique.append(
                        types.Content(role="model", parts=[types.Part(text=rep)])
                    )
                    return rep
                except Exception as e:
                    print(f"[CERVEAU] Echec {model_name} : {e}")
                    last_err = e
                    continue

            raise last_err or Exception("Tous les modeles Gemini ont echoue")

        async def _call_grok():
            print("[CERVEAU] Tentative avec Grok...")
            rep_grok = await demander_grok(texte)
            if not rep_grok:
                raise Exception("Grok n'a rien renvoyé ou est mal configuré")
            return rep_grok

        # Logique de bascule bidirectionnelle
        if cerveau == "GROK" and grok_client:
            try:
                return await _call_grok()
            except Exception as e:
                print(f"[CERVEAU] Erreur Grok ({e}). Bascule sur Gemini.")
                try:
                    return await _call_gemini()
                except Exception as e2:
                    print(f"[ERREUR IA (Gemini repli)] {e2}")
        else:
            try:
                return await _call_gemini()
            except Exception as e:
                print(f"[CERVEAU] Erreur Gemini ({e}). Bascule sur SerpAPI.")

                # --- FALLBACK SERPAPI ---
                if len(texte.split()) > 2:
                    res_serp = recherche_web_serpapi(texte)
                    if (
                        res_serp
                        and "VOTRE_CLE" not in res_serp
                        and "rien trouvé" not in res_serp
                        and "erreur" not in res_serp.lower()
                    ):
                        return "Voici ce que j'ai trouvé sur le web : " + res_serp

                # --- FALLBACK GROQ (LLAMA 3.3) ---
                print("[CERVEAU] Bascule sur Groq (Llama 3.3).")
                if groq_client:
                    rep_groq = await demander_groq(texte)
                    if rep_groq:
                        return rep_groq

                # --- FALLBACK GROK (xAI) ---
                print("[CERVEAU] Bascule sur Grok (xAI).")
                if grok_client:
                    try:
                        return await _call_grok()
                    except Exception as e2:
                        print(f"[ERREUR IA (Grok repli)] {e2}")
        # --- FALLBACK OLLAMA (100% offline) ---
        print("[CERVEAU] Gemini et Grok KO. Tentative Ollama (local)...")
        rep_ollama = await demander_ollama(texte)
        if rep_ollama:
            return rep_ollama

        # --- FALLBACK LOCAL ---
        print("[CERVEAU] Retry Gemini directement...")
        # On réessaye Gemini une dernière fois directement
        for model_name in MODELS_LIST:
            try:
                reponse = client.models.generate_content(
                    model=model_name,
                    config=types.GenerateContentConfig(
                        system_instruction=construire_system_prompt(),
                        temperature=0.7,
                    ),
                    contents=historique
                    + [types.Content(role="user", parts=[types.Part(text=texte)])],
                )
                return reponse.text.strip()
            except:
                continue

        rep_loc = reponse_locale(texte)
        if rep_loc:
            return rep_loc
        return "C'est bon Tom, je suis là."
    finally:
        is_thinking = False
        await send_web_state("idle")


async def demander_ia_vision(texte, img_b64):
    """Analyse une image (capture d'écran) avec Gemini Vision."""
    global is_thinking, historique
    is_thinking = True
    await send_web_state("thinking")
    try:
        print("[VISION] Analyse de l'image avec Gemini...")

        # Conversion base64 en bytes pour l'API
        img_bytes = base64.b64decode(img_b64)
        image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")

        prompt_actuel = construire_system_prompt()
        prompt_actuel += "\n\nIMPORTANT : Tu viens de recevoir une capture d'écran de Tom. Analyse-la attentivement et réponds à sa question en te basant sur ce que tu vois."

        # On envoie l'image et le texte avec retry en cas de 503
        contents = [
            types.Content(role="user", parts=[image_part, types.Part(text=texte)])
        ]

        rep = None
        last_err = None
        for model_name in MODELS_LIST:
            print(f"[VISION] Essai modele : {model_name}")
            for attempt in range(2):  # 2 tentatives par modele
                try:
                    print(f"[VISION] Appel modele : {model_name} (Timeout 15s)")
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            client.models.generate_content,
                            model=model_name,
                            config=types.GenerateContentConfig(
                                system_instruction=prompt_actuel,
                                temperature=0.7,
                            ),
                            contents=contents,
                        ),
                        timeout=15.0,
                    )
                    rep = response.text
                    break
                except Exception as e:
                    if (
                        "503" in str(e) or "overloaded" in str(e).lower()
                    ) and attempt < 1:
                        print(f"[VISION] Surcharge {model_name} (503). Retente...")
                        await asyncio.sleep(1)
                        continue
                    print(f"[VISION] Erreur {model_name} : {e}")
                    last_err = e
                    break
            if rep:
                break

        if not rep:
            print(
                "[VISION] Tous les modeles Gemini ont echoue. Bascule sur Grok (Texte uniquement)..."
            )
            if grok_client:
                return await demander_grok(
                    texte
                    + " (Note: Je n'ai pas pu voir ton écran car mes serveurs de vision sont indisponibles, je réponds donc uniquement à ton texte)."
                )
            raise last_err or Exception("Aucun modele n'a pu analyser l'image")

        # On ajoute la trace dans l'historique (sans l'image pour éviter de saturer la mémoire)
        historique.append(
            types.Content(
                role="user", parts=[types.Part(text=f"[Analyse d'écran] {texte}")]
            )
        )
        historique.append(types.Content(role="model", parts=[types.Part(text=rep)]))

        return rep
    except Exception as e:
        print(f"[VISION] Erreur Gemini Vision : {e}")
        # On évite les accolades dans le message d'erreur pour ne pas perturber l'extracteur JSON
        err_msg = str(e).replace("{", "[").replace("}", "]")
        return f"Désolé Tom, je n'ai pas pu analyser votre écran. Erreur : {err_msg}"
    finally:
        is_thinking = False
        await send_web_state("idle")


def detecter_cerveau(texte):
    # Heuristique pour basculer sur Grok uniquement pour X/Twitter
    mots_cles_grok = ["sur x", "twitter", "grok", "elon", "x.com"]
    cmd = texte.lower()
    if any(m in cmd for m in mots_cles_grok):
        return "GROK"
    return "GEMINI"


async def demander_grok(texte):
    if not grok_client:
        return None

    try:
        # Conversion de l'historique Gemini vers format OpenAI pour Grok
        messages = [
            {
                "role": "system",
                "content": "Tu es JARVIS, l'IA de Tom. Tu utilises actuellement ton module Grok pour les infos en temps reel.",
            }
        ]
        for h in historique[
            -6:
        ]:  # Limiter aux 6 derniers messages pour eviter de saturer le contexte
            role = "user" if h.role == "user" else "assistant"
            msg_text = h.parts[0].text
            messages.append({"role": role, "content": msg_text})

        messages.append({"role": "user", "content": texte})

        completion = grok_client.chat.completions.create(
            model="grok-3",
            messages=messages,
            temperature=0.7,
        )

        rep = completion.choices[0].message.content

        # On synchronise l'historique Gemini
        historique.append(types.Content(role="user", parts=[types.Part(text=texte)]))
        historique.append(types.Content(role="model", parts=[types.Part(text=rep)]))

        return rep
    except Exception as e:
        print(f"[ERREUR GROK] {e}")
        return None


async def demander_ollama(texte):
    """Appelle un modèle local via Ollama (100% offline)."""
    global historique
    try:
        # On prépare les messages au format Ollama (compatible OpenAI)
        messages = [
            {
                "role": "system",
                "content": "Tu es JARVIS, l'IA de Tom. Tu utilises actuellement ton module local Ollama. Réponds en français, de façon concise et élégante.",
            }
        ]
        for h in historique[-4:]:
            role = "user" if h.role == "user" else "assistant"
            messages.append({"role": role, "content": h.parts[0].text})
        messages.append({"role": "user", "content": texte})

        last_err = None
        for model_name in OLLAMA_MODELS:
            try:
                print(f"[OLLAMA] Essai modele local : {model_name}")
                resp = await asyncio.wait_for(
                    asyncio.to_thread(
                        requests.post,
                        f"{OLLAMA_URL}/api/chat",
                        json={
                            "model": model_name,
                            "messages": messages,
                            "stream": False,
                        },
                        timeout=30,
                    ),
                    timeout=35.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    rep = data.get("message", {}).get("content", "")
                    if rep:
                        historique.append(
                            types.Content(role="user", parts=[types.Part(text=texte)])
                        )
                        historique.append(
                            types.Content(role="model", parts=[types.Part(text=rep)])
                        )
                        print(f"[OLLAMA] Reponse recue de {model_name}")
                        return rep
                else:
                    print(f"[OLLAMA] Erreur HTTP {resp.status_code} pour {model_name}")
                    last_err = Exception(f"HTTP {resp.status_code}")
            except Exception as e:
                print(f"[OLLAMA] Echec {model_name} : {e}")
                last_err = e
                continue

        print(f"[OLLAMA] Tous les modeles locaux ont echoue")
        return None
    except Exception as e:
        print(f"[ERREUR OLLAMA] {e}")
        return None


async def demander_groq(texte):
    """Appelle Groq (Llama 3.3) en fallback gratuit."""
    if not groq_client:
        return None

    try:
        messages = [
            {
                "role": "system",
                "content": "Tu es JARVIS, l'IA de Tom. Tu utilises actuellement le modèle Llama 3.3 de Groq pour répondre rapidement.",
            }
        ]
        for h in historique[-6:]:
            role = "user" if h.role == "user" else "assistant"
            messages.append({"role": role, "content": h.parts[0].text})
        messages.append({"role": "user", "content": texte})

        completion = await asyncio.to_thread(
            groq_client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
        )

        rep = completion.choices[0].message.content

        historique.append(types.Content(role="user", parts=[types.Part(text=texte)]))
        historique.append(types.Content(role="model", parts=[types.Part(text=rep)]))

        return rep
    except Exception as e:
        print(f"[ERREUR GROQ] {e}")
        return None


async def action_whatsapp_appel(contact):
    try:
        await parler(f"J'appelle {contact} sur WhatsApp, Tom.")
        # Lancement de l'app via le protocole
        os.system("start whatsapp://")
        time.sleep(6)  # On laisse le temps a l'app de s'ouvrir et se focuser

        # Recherche du contact (Ctrl+F)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(1)
        pyautogui.typewrite(contact)
        time.sleep(2)
        pyautogui.press("enter")
        time.sleep(3)  # On attend que la conversation s'affiche bien

        # Utilisation du raccourci clavier officiel pour l'appel audio (plus fiable que la vision)
        print(f"[WHATSAPP] Envoi du raccourci d'appel (Ctrl+Shift+C)...")
        pyautogui.hotkey("ctrl", "shift", "c")

        # On ajoute quand meme un petit clic de vision en secours si le raccourci ne suffit pas
        time.sleep(2)
        print(f"[WHATSAPP] Verification par vision au cas ou...")
        await jarvis_vision_cliquer(
            "clique sur le bouton 'Appel vocal' ou l icone de telephone qui vient de s afficher en haut a droite"
        )

        return True
    except Exception as e:
        print(f"[WHATSAPP ERROR] {e}")
        await parler(f"Desole Tom, je n'ai pas pu lancer l'appel WhatsApp. {e}")
        return False


async def traiter_reponse_ia(texte_utilisateur, mobile_ws=None):
    global MODE_IRON_MAN, jarvis_actif, dernier_message, _skip_pc_audio
    # Reset du flag audio au début de chaque commande
    _skip_pc_audio = False

    # TENTATIVE DE RÉSOLUTION LOCALE (Math, Français, Conversion, Traduction)
    reponse = resoudre_math_localement(texte_utilisateur)
    if not reponse:
        reponse = resoudre_francais_localement(texte_utilisateur)
    if not reponse:
        reponse = resoudre_conversion_localement(texte_utilisateur)
    if not reponse:
        reponse = resoudre_traduction_localement(texte_utilisateur)

    # VISION (Regarde mon écran)
    if not reponse:
        t = texte_utilisateur.lower()
        if any(
            keyword in t
            for keyword in [
                "regarde mon écran",
                "analyse mon écran",
                "vois-tu mon écran",
                "qu'est-ce qu'il y a sur mon écran",
            ]
        ):
            await parler("Bien sûr Tom, laissez-moi jeter un œil...")
            img_b64 = await request_screen_capture()
            if img_b64:
                reponse = await demander_ia_vision(texte_utilisateur, img_b64)
            else:
                reponse = "Je suis désolé Tom, mais je n'ai pas pu capturer votre écran. Assurez-vous d'avoir cliqué sur 'Activer la vision' sur l'interface et d'avoir autorisé le partage."

    if not reponse:
        reponse = await demander_ia(texte_utilisateur)

    print(f"[JARVIS] {reponse}")

    # Si commande mobile : activer le flag pour couper l'audio PC et répondre via mobile
    if mobile_ws:
        _skip_pc_audio = True

    # Recherche de TOUS les blocs JSON dans la réponse
    json_blocks = re.findall(r"\{.*?\}", reponse, re.DOTALL)

    if not json_blocks:
        await parler(reponse)
        _skip_pc_audio = False
        return

    for block in json_blocks:
        try:
            print(f"[JARVIS] Execution de l'action : {block}")
            # Timeout de 15s pour chaque action pour eviter de freezer Jarvis
            data = json.loads(block)
            action = data.get("action", "")

            # On execute l'action avec un timeout
            try:
                # Note: On utilise asyncio.wait_for pour les actions asynchrones
                # Les actions synchrones comme ha_lumiere devraient idéalement être async aussi
                # mais pour l'instant on les laisse ainsi ou on les wrappe.
                pass
            except asyncio.TimeoutError:
                print(f"[ACTION ERROR] Timeout sur l'action {action}")
                if grok_client:
                    await parler(
                        "C'est un peu long Tom, je demande une vérification à Grok."
                    )
                    rep_grok = await demander_grok(
                        texte_utilisateur
                        + " (L'action domotique a expiré, peux-tu répondre à l'utilisateur ?)"
                    )
                    if rep_grok:
                        await parler(rep_grok)
                continue

            if action == "mode_iron_man":
                etat = data.get("etat", "off")
                MODE_IRON_MAN = etat == "on"
                msg = (
                    "Mode Iron Man activé, Monsieur. Je reste à l'écoute de vos signaux."
                    if MODE_IRON_MAN
                    else "Mode Iron Man désactivé. Je repasse en veille domotique."
                )
                await parler(msg)
            elif action == "memoriser":
                cle = data.get("cle", "info")
                valeur = data.get("valeur", "")
                ajouter_memoire(cle, valeur)
                await parler(f"Bien note Tom, je me souviendrai que {valeur}.")
            elif action == "oublier":
                cle = data.get("cle", "")
                success = supprimer_memoire(cle)
                if success:
                    await parler("Information oubliee, Tom.")
                else:
                    await parler("Je n avais pas cette information en memoire.")
            elif action == "lister_memoire":
                memoire = charger_memoire()
                if not memoire:
                    await parler("Aucune information personnalisee en memoire, Tom.")
                else:
                    lignes = ["Voici ce que je sais sur vous Tom."]
                    for cle, data_m in memoire.items():
                        lignes.append(f"{cle} : {data_m['valeur']}.")
                    await parler(" ".join(lignes))
            elif action == "ouvrir_dossier":
                chemin = data.get("chemin", "bureau")
                ok, resultat = ouvrir_dossier(chemin)
                if ok:
                    await parler(
                        "Dossier ouvert, Tom. Dites-moi si vous voulez que je le trie."
                    )
                else:
                    await parler(f"Je n ai pas trouve ce dossier, Tom. {resultat}")
            elif action == "lister_dossier":
                contenu, err = lister_dossier()
                if err:
                    await parler(err)
                else:
                    nb_fichiers = len(contenu["fichiers"])
                    nb_dossiers = len(contenu["dossiers"])
                    await parler(
                        f"Le dossier contient {nb_fichiers} fichiers et {nb_dossiers} sous-dossiers, Tom."
                    )
            elif action == "trier_par_type":
                await parler("Je trie vos fichiers par type, Tom. Un instant.")
                ok, msg = trier_par_type()
                await parler(msg if ok else f"Probleme lors du tri : {msg}")
            elif action == "trier_par_date":
                await parler("Je trie vos fichiers par date, Tom. Un instant.")
                ok, msg = trier_par_date()
                await parler(msg if ok else f"Probleme lors du tri : {msg}")
            elif action == "trier_complet":
                await parler(
                    "Je trie vos fichiers par type puis par date dans chaque categorie, Tom."
                )
                ok, msg = trier_par_type_puis_date()
                await parler(msg if ok else f"Probleme lors du tri : {msg}")
            elif action == "creer_dossier":
                nom = data.get("nom", "Nouveau Dossier")
                ok, msg = creer_sous_dossier(nom)
                await parler(msg if ok else f"Erreur : {msg}")
            elif action == "renommer_fichier":
                ancien = data.get("ancien", "")
                nouveau = data.get("nouveau", "")
                ok, msg = renommer_fichier(ancien, nouveau)
                await parler(msg if ok else f"Erreur : {msg}")
            elif action == "deplacer_fichier":
                fichier = data.get("fichier", "")
                dest = data.get("destination", "")
                ok, msg = deplacer_fichier(fichier, dest)
                await parler(msg if ok else f"Erreur : {msg}")
            elif action == "chercher_fichier":
                nom = data.get("nom", "")
                resultats, err = chercher_fichier(nom)
                if err:
                    await parler(err)
                elif not resultats:
                    await parler(f"Aucun fichier contenant {nom} n a ete trouve, Tom.")
                else:
                    noms = [os.path.basename(r) for r in resultats[:5]]
                    await parler(
                        f"J ai trouve {len(resultats)} fichier(s). Par exemple : {', '.join(noms)}."
                    )
            elif action == "ha_lumiere":
                piece = data.get("piece", "salon")
                etat = data.get("etat", "on")
                couleur = data.get("couleur", None)
                luminosite = data.get("luminosite", None)
                entity_id = PIECES_LUMIERES.get(piece, f"light.{piece}")
                rgb = COULEURS_MAP.get(couleur) if couleur else None
                ha_lumiere(entity_id, etat, luminosite, rgb)

                # Message de confirmation amélioré
                if etat == "off":
                    msg = f"J'éteins {piece}."
                else:
                    details = []
                    if couleur:
                        details.append(f"en {couleur}")
                    if luminosite is not None:
                        pourcent = int((int(luminosite) / 255) * 100)
                        details.append(f"à {pourcent}%")

                    if details:
                        msg = f"C'est fait, {piece} est réglé{' '.join(details)}."
                    else:
                        msg = f"Lumière {piece} allumée."
                await parler(msg)
            elif action == "ha_prise":
                piece = data.get("piece", "bureau")
                etat = data.get("etat", "on")
                entity_id = PIECES_PRISES.get(piece, f"switch.prise_{piece}")
                ha_interrupteur(entity_id, etat)
                msg = f"Prise {piece} {'activée' if etat == 'on' else 'désactivée'}."
                await parler(msg)
            elif action == "ha_temperature":
                piece = data.get("piece", "salon")
                entity_id = PIECES_CAPTEURS.get(piece)
                if entity_id:
                    temp = ha_get_etat(entity_id)
                    await parler(
                        f"La température dans le {piece} est de {temp} degrés."
                    )
                else:
                    await parler(
                        f"Désolé, je n'ai pas de capteur configuré pour le {piece}."
                    )
            elif action == "ha_humidite":
                piece = data.get("piece", "bureau")
                entity_id = PIECES_HUMIDITE.get(piece)
                if entity_id:
                    humi = ha_get_etat(entity_id)
                    await parler(f"Le taux d'humidité dans le {piece} est de {humi}%.")
                else:
                    await parler(f"Je n'ai pas de capteur d'humidité pour le {piece}.")
            elif action == "ha_batterie":
                appareil = data.get("appareil", "").lower()
                entity_id = APPAREILS_BATTERIE.get(appareil)
                if entity_id:
                    batt = ha_get_etat(entity_id)
                    if batt == "unknown":
                        await parler(
                            f"Je n'arrive pas à récupérer l'état de la batterie pour {appareil}."
                        )
                    else:
                        suff = ""
                        if (
                            "telephone" in appareil
                            or "papa" in appareil
                            or "Tom" in appareil
                        ):
                            suff = "Ton téléphone est à "
                        elif "julie" in appareil or "maman" in appareil:
                            suff = "Le téléphone de Julie est à "
                        else:
                            suff = f"La batterie de {appareil} est à "
                        await parler(f"{suff}{batt}%.")
                else:
                    await parler(
                        f"Je n'ai pas l'appareil {appareil} dans ma liste de batterie."
                    )
            elif action == "ha_thermostat":
                temp = data.get("temperature", 20)
                ha_thermostat("climate.thermostat", temp)
                await parler(f"Thermostat réglé à {temp} degrés.")
            elif action == "ha_scene":
                nom = data.get("nom", "")
                scene_id = f"scene.{nom}"
                ha_scene(scene_id)
                await parler(f"Ambiance {nom} activée.")
            elif action == "ha_alarme":
                etat = data.get("etat", "on")
                if etat == "on":
                    ha_appeler_service(
                        "alarm_control_panel",
                        "alarm_arm_away",
                        "alarm_control_panel.home_base_2",
                    )
                    await parler("Alarme activée.")
                else:
                    ha_appeler_service(
                        "alarm_control_panel",
                        "alarm_disarm",
                        "alarm_control_panel.home_base_2",
                    )
                    await parler("Alarme désactivée.")
            elif action == "ha_simulation":
                etat = data.get("etat", "on")
                ha_interrupteur("switch.simulation", etat)
                msg = (
                    "Simulation de présence activée."
                    if etat == "on"
                    else "Simulation de présence désactivée."
                )
                await parler(msg)
            elif action == "ha_anniversaires":
                events = ha_get_calendrier("calendar.anniversaires")
                if not events:
                    await parler("Rien de prévu aujourd'hui.")
                else:
                    noms = [e.get("summary", "Anniversaire sans nom") for e in events]
                    if len(noms) == 1:
                        await parler(
                            f"Aujourd'hui, nous fêtons l'anniversaire de {noms[0]}. N'oubliez pas de lui souhaiter !"
                        )
                    else:
                        liste = ", ".join(noms[:-1]) + " et " + noms[-1]
                        await parler(
                            f"Aujourd'hui, il y a plusieurs anniversaires : {liste}. C'est une journée chargée !"
                        )
            elif action == "ha_consommation":
                entity_id = PIECES_CAPTEURS.get("consommation")
                puissance = ha_get_etat(entity_id)
                if puissance == "unknown" or puissance == "inconnu":
                    await parler(
                        "Je n'arrive pas à lire la consommation électrique pour le moment."
                    )
                else:
                    await parler(
                        f"La consommation actuelle de la maison est de {puissance} Volt-Ampères."
                    )
            elif action == "ha_tiktok":
                entity_id = PIECES_CAPTEURS.get("tiktok")
                followers = ha_get_etat(entity_id)
                await parler(
                    f"Tu as actuellement {followers} abonnés sur ton compte TikTok TechEnClair, Tom. Félicitations !"
                )
            elif action == "ha_oeufs":
                entity_id = PIECES_CAPTEURS.get("oeufs")
                # On récupère l'état (le dernier choix) et le moment de la modif
                try:
                    r = requests.get(
                        f"{HA_URL}/api/states/{entity_id}",
                        headers=HA_HEADERS,
                        timeout=5,
                    )
                    data = r.json()
                    last_changed = data.get("last_changed", "")
                    if last_changed:
                        dt = datetime.fromisoformat(last_changed.replace("Z", "+00:00"))
                        phrase = dt.strftime("le %d %B à %Hh%M")
                        await parler(
                            f"Le dernier ramassage des œufs a été enregistré {phrase}."
                        )
                    else:
                        await parler(
                            "Je n'ai pas d'historique pour le ramassage des œufs."
                        )
                except:
                    await parler(
                        "Je n'arrive pas à accéder aux informations sur les œufs."
                    )
            elif action == "ha_energie":
                periode = data.get("periode", "mois")
                appareil = data.get("appareil", "")

                if appareil:
                    appareil_clean = appareil.lower()
                    entite = APPAREILS_ENERGIE.get(appareil_clean)
                    if entite:
                        val = ha_get_etat(entite)
                        if val != "inconnu" and val != "unknown":
                            kwh = float(val)
                            await parler(
                                f"La consommation de {appareil} pour ce mois est de {kwh:.1f} kWh."
                            )
                        else:
                            await parler(
                                f"Je n'ai pas de données de consommation pour {appareil} pour le moment."
                            )
                    else:
                        await parler(
                            f"Je n'ai pas d'appareil nommé {appareil} dans mon suivi énergétique."
                        )
                elif periode == "hier":
                    total_kwh = 0
                    total_cost = 0
                    try:
                        for i in range(1, 7):
                            e_id = f"sensor.lixee_zlinky_tic_zlinky_p{i}_daily"
                            val = ha_get_etat(e_id, attribut="last_period")
                            if val != "inconnu" and val != "unknown":
                                k = float(val)
                                total_kwh += k
                                total_cost += k * HA_TARIFS.get(f"p{i}", 0.16)
                        await parler(
                            f"Hier, la maison a consommé {total_kwh:.1f} kWh, pour un coût estimé à {total_cost:.2f} euros."
                        )
                    except:
                        await parler(
                            "J'ai eu un problème pour calculer la consommation d'hier."
                        )
                else:  # mois
                    total_kwh = 0
                    total_cost = 0
                    try:
                        for i in range(1, 7):
                            e_id = f"sensor.lixee_zlinky_tic_zlinky_p{i}_mensuel"
                            val = ha_get_etat(e_id)
                            if val != "inconnu" and val != "unknown":
                                k = float(val)
                                total_kwh += k
                                total_cost += k * HA_TARIFS.get(f"p{i}", 0.16)
                        await parler(
                            f"Ce mois-ci, la consommation totale est de {total_kwh:.1f} kWh, pour un montant de {total_cost:.2f} euros."
                        )
                    except:
                        await parler(
                            "Je n'ai pas pu calculer la consommation mensuelle."
                        )
            elif action == "ha_aspirateur":
                commande = data.get("commande", "start")
                if commande == "start":
                    ha_appeler_service("vacuum", "start", "vacuum.bob")
                    await parler("C'est parti, Bob lance le nettoyage.")
                elif commande == "stop":
                    ha_appeler_service("vacuum", "stop", "vacuum.bob")
                    await parler("J'ai arrêté l'aspirateur.")
                elif commande == "pause":
                    ha_appeler_service("vacuum", "pause", "vacuum.bob")
                    await parler("Bob est en pause.")
                elif commande == "base":
                    ha_appeler_service("vacuum", "return_to_base", "vacuum.bob")
                    await parler("Bob retourne à sa base.")
            elif action == "create_doc":
                titre = data.get("title", "Document JARVIS")
                contenu = data.get("content", "")
                result = creer_google_doc(titre, contenu)
                await parler(result)
            elif action == "write_doc":
                contenu = data.get("content", "")
                result = modifier_google_doc(contenu)
                await parler(result)
            elif action == "create_sheet":
                titre = data.get("title", "Feuille JARVIS")
                result = creer_google_sheet(titre)
                await parler(result)
            elif action == "read_emails":
                result = lire_emails()
                await parler(f"Voici vos derniers emails Tom. {result}")
            elif action == "read_calendar":
                result = lister_evenements_calendar()
                await parler(f"Voici vos prochains evenements Tom. {result}")
            elif action == "meteo":
                ville = data.get("ville") or None
                await parler("Je consulte la meteo, un instant Tom.")
                result = get_meteo_actuelle(ville)
                await parler(result)
            elif action == "alerte_meteo":
                ville = data.get("ville") or None
                result = get_alertes_meteo(ville)
                await parler(result)
            elif action == "recherche_web":
                query = data.get("query", "")
                await parler(f"Je lance une recherche sur internet pour {query}.")
                result = recherche_web_serpapi(query)
                await parler(result)
            elif action == "sport_resultats":
                equipe = data.get("equipe") or None
                ligue = data.get("ligue") or None
                print(f"[SPORT] Action sport_resultats pour {equipe or ligue}")
                await parler(
                    f"Je cherche les informations pour {equipe or ligue}, un instant."
                )
                result = get_resultats_football(equipe=equipe, ligue=ligue)
                if "pas trouvé" in result or "Impossible" in result:
                    print(f"[SPORT] Echec recherche locale. Verification avec Grok...")
                    if grok_client:
                        res_grok = await demander_grok(
                            f"Tom veut savoir : {texte_utilisateur}. Je n'ai pas trouvé l'info dans ma base de données football, peux-tu chercher pour lui ?"
                        )
                        if res_grok:
                            result = res_grok
                await parler(result)
            elif action == "sport_classement":
                ligue = data.get("ligue", "Ligue 1")
                await parler(f"Je recupere le classement {ligue}.")
                result = get_classement_football(ligue=ligue)
                await parler(result)
            elif action == "sport_live":
                question = data.get("question", "derniers resultats sportifs 2026")
                await parler(
                    "Je recherche les derniers resultats en direct, un instant Tom."
                )
                result = get_resultats_sport_gemini(question)
                await parler(result)
            elif action == "voir_ecran":
                inst = data.get("instruction", "")
                res = await jarvis_vision_cliquer(inst)
                await parler(res)
            elif action == "whatsapp_appel":
                contact = data.get("contact", "Ma vie")
                await action_whatsapp_appel(contact)
            elif action == "vision_ecrire":
                inst = data.get("instruction", "")
                txt = data.get("texte", "")
                res = await jarvis_vision_ecrire(inst, txt)
                await parler(res)

        except Exception as e:
            print(f"[ACTION ERROR] Block failed: {block} | Error: {e}")
            if grok_client:
                print("[JARVIS] Bascule sur Grok suite a une erreur d'action...")
                res_grok = await demander_grok(
                    f"Tom m'a demandé : {texte_utilisateur}. J'ai tenté de lancer une action mais j'ai eu une erreur technique ({e}). Peux-tu prendre le relais et lui répondre élégamment ?"
                )
                if res_grok:
                    await parler(res_grok)
            continue

    # Si du texte reste après les commandes, on ne fait rien de plus car `parler` a déjà été appelé pour chaque action ou la réponse globale.
    # Réinitialiser le flag audio PC
    _skip_pc_audio = False


def nettoyer_commande(texte):
    t = texte.lower().strip()
    for variante in ["jarvis,", "jarvis"]:
        if t.startswith(variante):
            t = t[len(variante) :].strip()
    return t


WAKE_WORD = "jarvis"
SESSION_TIMEOUT = 30
STOP_PARLER = False
is_listening = False
is_speaking = False
jarvis_actif = False
dernier_message = 0
interface_deja_connectee = False


def ecouter():
    global is_listening, jarvis_actif, dernier_message, STOP_PARLER, is_speaking

    r = sr.Recognizer()
    mic = sr.Microphone()

    r.pause_threshold = 0.6
    r.non_speaking_duration = 0.5
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1)

    print("[JARVIS] Microphone pret. En attente de 'Jarvis' ou session active...")

    while True:
        try:
            # GESTION DU TIMEOUT DE SESSION
            if jarvis_actif and (time.time() - dernier_message > SESSION_TIMEOUT):
                print("[JARVIS] Timeout session. Retour en veille.")
                jarvis_actif = False

            with mic as source:
                is_listening = True
                loop_ws = asyncio.new_event_loop()
                state = "active" if jarvis_actif else "listening"
                loop_ws.run_until_complete(send_web_state(state))
                loop_ws.close()

                audio = r.listen(source, timeout=2, phrase_time_limit=10)

                is_listening = False
                loop_ws = asyncio.new_event_loop()
                loop_ws.run_until_complete(send_web_state("idle"))
                loop_ws.close()

            texte = r.recognize_google(audio, language="fr-FR").lower().strip()
            print(f"[ENTENDU] {texte}")

            # GESTION INTERRUPTION DURANT LA PAROLE
            if is_speaking and (
                "tais-toi" in texte or "silence" in texte or "tais toi" in texte
            ):
                STOP_PARLER = True
                continue

            # MOTS-CLÉS DE SOMMEIL
            SLEEP_WORDS = [
                "merci",
                "ce sera tout",
                "repos",
                "au revoir",
                "silence",
                "tais-toi",
                "tais toi",
            ]
            if any(word in texte for word in SLEEP_WORDS):
                if jarvis_actif:
                    jarvis_actif = False
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(
                        parler("A votre service Tom. Je me mets en veille.")
                    )
                    loop.close()
                continue

            if WAKE_WORD in texte or jarvis_actif:
                if WAKE_WORD in texte:
                    print("[JARVIS] Mot-clé détecté.")
                    jarvis_actif = True

                dernier_message = time.time()
                commande = nettoyer_commande(texte)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                if commande:
                    action_pc = executer_action_pc(commande)
                    if action_pc:
                        loop.run_until_complete(parler(action_pc))
                    else:
                        loop.run_until_complete(traiter_reponse_ia(commande))
                else:
                    if WAKE_WORD in texte:  # "Jarvis" tout seul
                        loop.run_until_complete(parler("Oui Tom, je vous écoute."))

                loop.close()
            else:
                pass

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except Exception as e:
            print(f"Erreur écoute : {e}")
            time.sleep(1)


def monitor_claps():
    try:
        import audioop

        p = pyaudio.PyAudio()
        # On ouvre le flux
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
        )
        print("[CLAP] Détection des applaudissements activée.")

        print("[CLAP] Détection des doubles applaudissements activée.")

        last_clap_time = 0

        while True:
            try:
                data = stream.read(1024, exception_on_overflow=False)
                rms = audioop.rms(data, 2)

                # ON IGNORE LE CLAP UNIQUEMENT SI LE MODE IRON MAN EST ÉTEINT OU SI JARVIS PARLE
                if not MODE_IRON_MAN or is_speaking or is_thinking:
                    last_clap_time = 0
                    continue

                if rms > CLAP_THRESHOLD:
                    current_time = time.time()
                    diff = current_time - last_clap_time

                    if 0.1 < diff < 0.8:
                        global VIDEO_LANCEE
                        print(f"\n[CLAP] !!! DOUBLE CLAP DÉTECTÉ !!!")
                        entity_id = PIECES_LUMIERES.get("salon", "light.salon")

                        # On vérifie l'état actuel
                        etat_actuel = ha_get_etat(entity_id)

                        if etat_actuel != "on":
                            # ON ALLUME
                            print(f"[CLAP] Action : ALLUMER")
                            ha_lumiere(entity_id, "on")

                            if not VIDEO_LANCEE:
                                print(f"[CLAP] Lancement initial de la vidéo...")
                                webbrowser.open(
                                    "https://www.youtube.com/watch?v=KU5V5WZVcVE"
                                )
                                VIDEO_LANCEE = True

                                def seq():
                                    time.sleep(5)
                                    pyautogui.press("f")

                                threading.Thread(target=seq, daemon=True).start()
                            else:
                                print(f"[CLAP] Reprise de la vidéo (Play)...")
                                pyautogui.press("k")
                        else:
                            # ON ÉTEINT
                            print(f"[CLAP] Action : ÉTEINDRE")
                            ha_lumiere(entity_id, "off")
                            if VIDEO_LANCEE:
                                print(f"[CLAP] Mise en pause de la vidéo...")
                                pyautogui.press("k")

                        # Gros debounce après une action réussie
                        time.sleep(3.0)
                        last_clap_time = 0  # Reset
                    else:
                        # C'est peut-être le premier clap
                        last_clap_time = current_time
            except Exception as e:
                # Si erreur de lecture (ex: micro débranché), on attend et on continue
                time.sleep(0.5)
                continue

    except Exception as e:
        print(f"[CLAP] Erreur fatale détection claps : {e}")


def start_ia():
    threading.Thread(target=monitor_claps, daemon=True).start()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_ws():
        print("[WEB] Serveur WebSocket demarre sur ws://0.0.0.0:8765")
        print("[WEB] Accessible depuis le reseau : ws://192.168.1.23:8765")
        async with websockets.serve(ws_handler, "0.0.0.0", 8765):
            await asyncio.Future()

    threading.Thread(target=lambda: asyncio.run(start_ws()), daemon=True).start()

    loop.run_until_complete(parler("Bonjour, Tom"))
    loop.close()
    ecouter()


# ==========================================
# LANCEMENT — MODE CONSOLE + FRONTEND WEB
# ==========================================
# Ursina desactive : l'interface est maintenant le frontend Three.js
# dans le dossier frontend/ (npm run dev -> http://localhost:5173)
# Le WebSocket est deja demarre par start_ia() sur ws://localhost:8765

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)


def start_mobile_http_server():
    """Serveur HTTP minimal pour servir l'interface mobile sur le port 8080."""
    import http.server

    mobile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mobile")
    if not os.path.exists(mobile_dir):
        print("[MOBILE] Dossier mobile/ introuvable, serveur non demarre.")
        return

    class MobileHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=mobile_dir, **kwargs)

        def log_message(self, format, *args):
            pass  # Silencieux

    server = http.server.HTTPServer(("0.0.0.0", 8080), MobileHandler)
    print("[MOBILE] Serveur HTTP demarre sur http://192.168.1.23:8080")
    server.serve_forever()


def main():
    print()
    print("=" * 60)
    print("   J.A.R.V.I.S — Mode Console + Interface Web")
    print("=" * 60)
    print()
    print("  Backend   : actif (terminal)")
    print("  WebSocket : ws://localhost:8765  (LAN: ws://192.168.1.23:8765)")
    print("  Frontend  : ouvrir http://localhost:5173")
    print("  Mobile    : ouvrir http://192.168.1.23:8080 sur votre tel/tablette")
    print()
    print("  Commandes vocales actives.")
    print("  Dites 'Jarvis' pour activer la session.")
    print("=" * 60)
    print()

    # Lancer le serveur Frontend
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    frontend_process = None
    if os.path.exists(frontend_dir):
        print("[JARVIS] Lancement automatique de l'interface Web (Vite)...")
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"], cwd=frontend_dir, shell=True
        )
        time.sleep(2.5)  # Laisser le temps a Vite de demarrer

    # Ouvrir le navigateur vers le frontend
    try:
        webbrowser.open("http://localhost:5173")
    except Exception:
        pass

    # Lancer le serveur HTTP mobile dans un thread
    threading.Thread(target=start_mobile_http_server, daemon=True).start()

    # Lancer le backend IA dans un thread
    threading.Thread(target=start_ia, daemon=True).start()

    # Garder le processus en vie et s'arreter si le navigateur est ferme
    try:
        while True:
            time.sleep(1)
            if interface_deja_connectee and len(CONNECTED_CLIENTS) == 0:
                print(
                    "\n[JARVIS] Interface déconnectée. Attente de reconnexion (60s)..."
                )
                time.sleep(60)
                if len(CONNECTED_CLIENTS) == 0:
                    print("[JARVIS] Aucune reconnexion. Extinction automatique...")
                    break
                else:
                    print("[JARVIS] Reconnexion détectée. Reprise.")
    except KeyboardInterrupt:
        print("\n[JARVIS] Arret du systeme demande manuellement.")

    if frontend_process:
        print("[JARVIS] Arret du serveur Web...")
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


if __name__ == "__main__":
    main()
