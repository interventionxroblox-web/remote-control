import socketio
import mss
import base64
import uuid
import platform
from PIL import Image
import io
from pynput import mouse, keyboard

# Configuration
SERVER_URL = 'https://remote-control-production-e384.up.railway.app'
MACHINE_ID = str(uuid.uuid4())
MACHINE_NOM = platform.node()

sio = socketio.Client()

def capturer_ecran():
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[1])
        img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        img = img.resize((1280, 720))
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=50)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

@sio.event
def connect():
    print('✅ Connecté au serveur !')
    sio.emit('enregistrer', {'id': MACHINE_ID, 'nom': MACHINE_NOM})

@sio.event
def demande_autorisation():
    print('⚠️ Demande de connexion reçue !')
    reponse = input('Autoriser le contrôle à distance ? (oui/non) : ')
    accepte = reponse.lower() == 'oui'
    sio.emit('reponse_autorisation', {'id': MACHINE_ID, 'accepte': accepte})
    if accepte:
        print('✅ Accès accordé ! Envoi de l\'écran...')
        envoyer_ecran()

@sio.event
def commande(data):
    if data['type'] == 'souris':
        import pyautogui
        x = int(data['x'] * 1920)
        y = int(data['y'] * 1080)
        pyautogui.moveTo(x, y)
    elif data['type'] == 'clavier':
        import pyautogui
        pyautogui.press(data['key'])

def envoyer_ecran():
    import threading
    def loop():
        while sio.connected:
            image = capturer_ecran()
            sio.emit('screenshot', {'id': MACHINE_ID, 'image': image})
            sio.sleep(0.1)
    threading.Thread(target=loop, daemon=True).start()

@sio.event
def disconnect():
    print('❌ Déconnecté du serveur')

print('🚀 Démarrage de l\'agent...')
print('ID de cette machine : ' + MACHINE_ID)
sio.connect(SERVER_URL)
sio.wait()