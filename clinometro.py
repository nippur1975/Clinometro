# Importamos las bibliotecas necesarias
import pygame
import math
import os
import serial
import json
from serial.tools.list_ports import comports
from pygame.locals import *
import requests
import csv
from datetime import datetime, timedelta, timezone
import threading
from PIL import Image
import pystray
import time
import sys # Necesario para sys._MEIPASS
import pyodbc
import base64

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

# Función para obtener la ruta correcta a los recursos (para PyInstaller)
# ESTA ES LA UBICACIÓN CORRECTA, AL PRINCIPIO
def resource_path(relative_path):
  
    try:
        base_path = sys._MEIPASS  # carpeta temporal de PyInstaller
    except Exception:
        # Cuando se ejecuta como script normal
        base_path = os.path.dirname(os.path.abspath(__file__))

    full_path = os.path.join(base_path, relative_path)

    # Verificación opcional (muy útil para depurar)
    if not os.path.exists(full_path):
        print(f"⚠️  Archivo no encontrado: {full_path}")
    return full_path

def get_persistent_data_path(filename: str) -> str:
    """
    Get absolute path to a data file that needs to persist.
    Works for dev (saves next to .py file) and for PyInstaller (saves next to executable).
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle (frozen)
        application_path = os.path.dirname(sys.executable)
        # print(f"INFO: Running in PyInstaller mode (get_persistent_data_path), application_path: {application_path}") # Opcional: para depuración
    else:
        # Running in a normal Python environment (development)
        application_path = os.path.dirname(os.path.abspath(__file__))
        
    return os.path.join(application_path, filename)

def on_open(icon, item):
    """Muestra la ventana principal."""
    global window_visible
    window_visible = True

def on_exit(icon, item):
    """Cierra la aplicación."""
    global running
    running = False
    icon.stop()

def setup_tray_icon():
    """Configura y corre el ícono de la bandeja del sistema."""
    image = Image.open(resource_path("barco.png"))
    menu = (pystray.MenuItem('Abrir', on_open), pystray.MenuItem('Salir', on_exit))
    icon = pystray.Icon("Lalito", image, "Lalito Clinometer", menu)
    icon.run()

# Definimos colores base
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
VERDE = (0, 255, 0)
ROJO = (255, 0, 0)
AZUL = (0, 0, 255)

# Constantes globales
ALTURA_BARRA_HERRAMIENTAS = 30
IDIOMA = "es"  # Por defecto en español ("es" o "en")
CURSOR_BLINK_INTERVAL = 500 # milisegundos, para el cursor en el campo de activación

# Diccionarios de textos para multiidioma
TEXTOS = {
    "es": {
        "titulo_ventana": "Lalito",
        "menu_config": "CONFIG. PUERTO",
        "menu_alarma": "CONFIG. ALARMAS",
        "menu_idioma": "IDIOMA",
        "menu_acerca": "ACERCA DE",
        "menu_mode": "MODO",
        "lat_lon": "LAT / LON",
        "actitud": "CABECEO",
        "rumbo": "RUMBO         ",
        "velocidad": "VELOCIDAD",
        "pitch": "PITCH",
        "roll": "ROLL ",
        "altitud": "ALTITUD",
        "no_datos": "NO HAY DATOS NMEA",
        "desconectado": "Puerto NMEA desconectado",
        "titulo_config": "Configuración Puerto",
        "etiqueta_puerto": "Puerto:",
        "etiqueta_baudios": "Baudios:",
        "boton_guardar": "Guardar",
        "titulo_alarma": "Configuración de Alarmas",
        "pitch_rango": "Pitch (5 a 30):",
        "roll_rango": "Roll (5 a 30):",
        "boton_salir": "Salir",
        "titulo_acerca": "Acerca de Lalito",
        "boton_cerrar": "Cerrar",
        "menu_servicio_datos": "ELEGIR SERVICIO",
        "titulo_servicio_datos": "Configurar Servicio de Datos",
        "etiqueta_servicio": "Servicio:",
        "opcion_thingspeak": "ThingSpeak",
        "opcion_google_cloud": "Azure SQL",
        "etiqueta_apikey_thingspeak": "API Key ThingSpeak:",
        "etiqueta_apikey_google_cloud": "Nombre del Barco:",
        "etiqueta_password_azure": "Contraseña:",
        "titulo_password_servicio": "Ingrese Contraseña",
        "etiqueta_password": "Contraseña:",
        "boton_entrar": "Entrar",
        "password_incorrecta": "Contraseña incorrecta!",
        "boton_mostrar_consola": "Mostrar Consola",
        "boton_test": "Test",
        "about_title": "Acerca de Lalito",
        "about_line1": "NMEA Data Reader Program",
        "about_line2": "Versión: 1.0",
        "about_line3": "Realizado por: Hdelacruz",
        "about_line4": "Email: hugo_delacruz@hotmail.com",
        "about_line5": "2025",
        "rot": "ROT",
        "sentina1": "Sentina 1",
        "sentina2": "Sentina 2",
        "port_label": "BABOR",
        "stbd_label": "ESTRIBOR",
    },
    "en": {
        "titulo_ventana": "Lalito",
        "menu_config": "SERIAL CONFIG",
        "menu_alarma": "ALARM SETTINGS",
        "menu_idioma": "LANGUAGE",
        "menu_acerca": "ABOUT",
        "menu_mode": "MODE",
        "lat_lon": "LAT / LON",
        "actitud": "ATTITUDE",
        "rumbo": "HEADING",
        "velocidad": "SPEED     ",
        "pitch": "PITCH",
        "roll": "ROLL ",
        "altitud": "ALTITUDE",
        "no_datos": "NO NMEA DATA",
        "desconectado": "NMEA port disconnected",
        "titulo_config": "Serial Settings",
        "etiqueta_puerto": "Port:",
        "etiqueta_baudios": "Baud rate:",
        "boton_guardar": "Save",
        "titulo_alarma": "Alarm Settings",
        "pitch_rango": "Pitch (5 to 30):",
        "roll_rango": "Roll (5 to 30):",
        "boton_salir": "Exit",
        "titulo_acerca": "About Lalito",
        "boton_cerrar": "Close",
        "menu_servicio_datos": "CHOOSE SERVICE",
        "titulo_servicio_datos": "Data Service Settings",
        "etiqueta_servicio": "Service:",
        "opcion_thingspeak": "ThingSpeak",
        "opcion_google_cloud": "Azure SQL",
        "etiqueta_apikey_thingspeak": "ThingSpeak API Key:",
        "etiqueta_apikey_google_cloud": "Ship Name:",
        "etiqueta_password_azure": "Password:",
        "titulo_password_servicio": "Enter Password",
        "etiqueta_password": "Password:",
        "boton_entrar": "Enter",
        "password_incorrecta": "Incorrect Password!",
        "boton_mostrar_consola": "Show Console",
        "boton_test": "Test",
        "about_title": "About Lalito",
        "about_line1": "NMEA Data Reader Program",
        "about_line2": "Version: 1.0",
        "about_line3": "Made by: Hdelacruz",
        "about_line4": "Email: hugo_delacruz@hotmail.com",
        "about_line5": "2025",
        "rot": "ROT",
        "sentina1": "Bilge 1",
        "sentina2": "Bilge 2",
        "port_label": "PORT",
        "stbd_label": "STBD",
    }
}

# Configuración para logging y ThingSpeak
API_KEY_THINGSPEAK = "5TRR6EXF6N5CZF54"
THINGSPEAK_URL = "https://api.thingspeak.com/update"

# Configuración para Azure SQL
AZURE_SQL_SERVER = "srv-db-east-us-estabilidadep.database.windows.net"
AZURE_SQL_DATABASE = "db_estabilidadep_prd"
AZURE_SQL_USER = "svc_writer_ep"
AZURE_SQL_PASSWORD = "" # El usuario final anadira la contrasena aqui

# Configuración para logging y ThingSpeak
API_KEY_THINGSPEAK = "5TRR6EXF6N5CZF54"
THINGSPEAK_URL = "https://api.thingspeak.com/update"



# Añade estas nuevas definiciones:
CSV_FILENAME = get_persistent_data_path("nmea_log.csv") # MODIFICADO
ALARM_LOG_FILENAME = get_persistent_data_path("alarm_log.csv") # MODIFICADO

INTERVALO_ENVIO_DATOS_S = 15
INTERVALO_REPETICION_ALARMA_ROLL_S = 5
INTERVALO_REPETICION_ALARMA_PITCH_S = 5

ARCHIVO_CONFIG_SERIAL = get_persistent_data_path("config_serial.json") # MODIFICADO
ARCHIVO_CONFIG_ALARMA = get_persistent_data_path("config_alarma.json") # MODIFICADO
FIRST_RUN_FILE = get_persistent_data_path("first_run.json")

# Variables globales
network_available = True
last_network_check_time = 0
valores_alarma = {
    "max_pitch_pos": "15", 
    "min_pitch_neg": "-15",
    "max_roll_pos": "15",
    "min_roll_neg": "-15"
}

valores_ui_input_alarma = {"pitch": "15", "roll": "15"}
lista_puertos_detectados = []
ultimo_intento_reconeccion_tiempo = 0 # Inicializada globalmente
INTERVALO_RECONECCION_MS = 5000
ultima_vez_datos_recibidos = 0 # Se inicializará después de pygame.init() o globalmente
UMBRAL_SIN_DATOS_MS = 3000

# Variables para datos de ThingSpeak
ts_pitch_float = 0.0
ts_roll_float = 0.0
ts_lat_decimal = 0.0
ts_lon_decimal = 0.0
ts_speed_float = 0.0
ts_heading_float = 0.0
ts_timestamp_str = "N/A"
altitude_str = "N/A" # Nueva variable para altitud
ts_altitude_float = 0.0 # Nueva variable para altitud numérica para ThingSpeak
ultima_vez_envio_datos = 0

# Variables para ROT y sentinas
rot_float = 0.0
switch1_status = "N/A"
switch2_status = "N/A"

# Variables de estado de alarmas
alarma_roll_babor_activa = False
alarma_roll_estribor_activa = False
ultima_reproduccion_alarma_babor_tiempo = 0.0
ultima_reproduccion_alarma_estribor_tiempo = 0.0
alarma_pitch_sentado_activa = False
alarma_pitch_encabuzado_activa = False
ultima_reproduccion_alarma_sentado_tiempo = 0.0
ultima_reproduccion_alarma_encabuzado_tiempo = 0.0

# Variables para control de sonidos
sonido_alarma_actualmente_reproduciendo = None
tiempo_ultimo_sonido_iniciado = 0.0
INDICE_PROXIMA_ALARMA_A_SONAR = 0
PAUSA_ENTRE_SONIDOS_ALTERNADOS_S = 1.0

# Variables para selección de servicio de datos y API Keys
SERVICIO_DATOS_ACTUAL = "thingspeak"  # Por defecto "thingspeak" o "google_cloud"
API_KEY_GOOGLE_CLOUD = ""  # Para almacenar la API Key de Google Cloud
# Variables para los campos de texto en la ventana de configuración del servicio
input_api_key_thingspeak_str = API_KEY_THINGSPEAK # Se inicializará desde config o default
input_api_key_google_cloud_str = "" # Se inicializará desde config o default
input_password_azure_str = "" # Para el campo de contraseña de Azure

# Variables para la ventana de contraseña del servicio de datos
CLAVE_ACCESO_SERVICIO = "29121975"
mostrar_ventana_password_servicio = False
input_password_str = ""
intento_password_fallido = False

# Variables para la ventana de Test de datos del puerto serie
mostrar_ventana_test_serial = False
datos_test_serial_buffer = []
MAX_LINEAS_TEST_SERIAL = 100

# Buffer para reensamblar tramas NMEA fragmentadas
nmea_buffer = ""

# Inicialización de Pygame
pygame.init()
pygame.mixer.init()
# script_dir = os.path.dirname(os.path.abspath(__file__)) # Comentado, resource_path se usa para assets

# Cargar sonidos de alarma según idioma
try:
    # Sonidos en español
    sonidos_es = {
        'babor': pygame.mixer.Sound(resource_path("alarma_babor.mp3")),
        'estribor': pygame.mixer.Sound(resource_path("alarma_estribor.mp3")),
        'sentado': pygame.mixer.Sound(resource_path("alarma_sentado.mp3")),
        'encabuzado': pygame.mixer.Sound(resource_path("alarma_encabuzado.mp3"))
    }
    
    # Sonidos en inglés (equivalentes)
    sonidos_en = {
        'babor': pygame.mixer.Sound(resource_path("port_alarm.mp3")),
        'estribor': pygame.mixer.Sound(resource_path("starboard_alarm.mp3")),
        'sentado': pygame.mixer.Sound(resource_path("stern_alarm.mp3")),
        'encabuzado': pygame.mixer.Sound(resource_path("head_alarm.mp3"))
    }
    
    # Ajustar volumen de los sonidos
    for sonido in sonidos_es.values():
        if sonido:
            sonido.set_volume(0.7)
    for sonido in sonidos_en.values():
        if sonido:
            sonido.set_volume(0.7)
            
except pygame.error as e:
    print(f"ERROR CRÍTICO: No se pudieron cargar algunos o todos los archivos de sonido: {e}")
    print("Por favor, asegúrese de que los archivos .mp3 de alarma (alarma_babor.mp3, alarma_estribor.mp3, etc., y sus equivalentes en inglés si se usan) estén presentes en el directorio correcto.")
    print("La funcionalidad de alarma sonora podría estar limitada.")
    # Se mantiene la asignación a None para que el programa pueda continuar sin los sonidos.
    sonidos_es = {'babor': None, 'estribor': None, 'sentado': None, 'encabuzado': None}
    sonidos_en = {'babor': None, 'estribor': None, 'sentado': None, 'encabuzado': None}

# Función para reproducir alarmas según idioma
def reproducir_alarma(tipo_alarma):
    """Reproduce la alarma correspondiente según el idioma actual"""
    global sonido_alarma_actualmente_reproduciendo, tiempo_ultimo_sonido_iniciado
    
    # Detener alarma actual si está sonando
    if sonido_alarma_actualmente_reproduciendo:
        sonido_alarma_actualmente_reproduciendo.stop()
    
    # Seleccionar diccionario de sonidos según idioma
    sonidos = sonidos_en if IDIOMA == "en" else sonidos_es
    
    # Mapeo de tipos de alarma
    mapeo_alarmas = {
        'roll_babor': 'babor',
        'roll_estribor': 'estribor',
        'pitch_sentado': 'sentado',
        'pitch_encabuzado': 'encabuzado'
    }
    
    # Obtener y reproducir el sonido adecuado
    clave_sonido = mapeo_alarmas.get(tipo_alarma)
    if clave_sonido:
        sonido = sonidos.get(clave_sonido)
        if sonido:
            sonido.play()
            sonido_alarma_actualmente_reproduciendo = sonido
            tiempo_ultimo_sonido_iniciado = time.time()
            return True
    return False

# Funciones de configuración
def cargar_configuracion_serial():
    global IDIOMA, SERVICIO_DATOS_ACTUAL, API_KEY_THINGSPEAK, API_KEY_GOOGLE_CLOUD, AZURE_SQL_PASSWORD
    global input_api_key_thingspeak_str, input_api_key_google_cloud_str, input_password_azure_str
    try:
        with open(ARCHIVO_CONFIG_SERIAL, 'r') as f:
            encoded_config_str = f.read()
        
        # Decodificar la cadena Base64
        decoded_config_bytes = base64.b64decode(encoded_config_str.encode('utf-8'))
        config_str = decoded_config_bytes.decode('utf-8')
        config = json.loads(config_str)
        
        IDIOMA = config.get('idioma', 'es')
        
        # Cargar configuración del servicio de datos
        SERVICIO_DATOS_ACTUAL = config.get('servicio_datos', 'thingspeak')
        API_KEY_THINGSPEAK = config.get('api_key_thingspeak', API_KEY_THINGSPEAK)
        API_KEY_GOOGLE_CLOUD = config.get('api_key_google_cloud', '')
        AZURE_SQL_PASSWORD = config.get('password_azure', '') # Cargar la contraseña
        
        # Inicializar los strings de input para la UI
        input_api_key_thingspeak_str = API_KEY_THINGSPEAK
        input_api_key_google_cloud_str = API_KEY_GOOGLE_CLOUD
        input_password_azure_str = AZURE_SQL_PASSWORD # Asignar a la variable del input
        
        return config.get('puerto', 'COM9'), int(config.get('baudios', 9600))
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        IDIOMA = 'es'
        SERVICIO_DATOS_ACTUAL = 'thingspeak'
       
        input_api_key_thingspeak_str = API_KEY_THINGSPEAK
        API_KEY_GOOGLE_CLOUD = ''
        input_api_key_google_cloud_str = ''
        AZURE_SQL_PASSWORD = ''
        input_password_azure_str = ''
        return 'COM9', 9600

def guardar_configuracion_serial(puerto, baudios):
    # Los valores de SERVICIO_DATOS_ACTUAL, input_api_key_thingspeak_str, 
    # y input_api_key_google_cloud_str se actualizan directamente 
    # desde la UI antes de llamar a esta función.
    config = {
        'puerto': puerto, 
        'baudios': int(baudios),
        'idioma': IDIOMA,
        'servicio_datos': SERVICIO_DATOS_ACTUAL,
        'api_key_thingspeak': input_api_key_thingspeak_str, # Guardar el valor del input
        'api_key_google_cloud': input_api_key_google_cloud_str, # Guardar el valor del input
        'password_azure': input_password_azure_str # Guardar la contraseña
    }
    try:
        # Convertir el diccionario a una cadena JSON
        config_str = json.dumps(config, indent=4)
        # Codificar la cadena en Base64
        encoded_config_bytes = base64.b64encode(config_str.encode('utf-8'))
        encoded_config_str = encoded_config_bytes.decode('utf-8')
        
        with open(ARCHIVO_CONFIG_SERIAL, 'w') as f: 
            f.write(encoded_config_str)
        return True
    except IOError as e:
        print(f"ERROR: No se pudo guardar la configuración: {e}")
        return False

def cargar_configuracion_alarma():
    global valores_alarma, valores_ui_input_alarma
    try:
        with open(ARCHIVO_CONFIG_ALARMA, 'r') as f: 
            config = json.load(f)
        valores_alarma["max_pitch_pos"] = str(config.get('max_pitch_pos', "15"))
        valores_alarma["min_pitch_neg"] = str(config.get('min_pitch_neg', "-15"))
        valores_alarma["max_roll_pos"] = str(config.get('max_roll_pos', "15"))
        valores_alarma["min_roll_neg"] = str(config.get('min_roll_neg', "-15"))
        
        valores_ui_input_alarma["pitch"] = str(abs(int(float(valores_alarma["max_pitch_pos"]))))
        valores_ui_input_alarma["roll"] = str(abs(int(float(valores_alarma["max_roll_pos"]))))
    except: 
        valores_alarma = {"max_pitch_pos": "15", "min_pitch_neg": "-15", "max_roll_pos": "15", "min_roll_neg": "-15"}
        valores_ui_input_alarma = {"pitch": "15", "roll": "15"}

def guardar_configuracion_alarma(): 
    global valores_alarma, valores_ui_input_alarma
    try:
        pitch_val_ui = int(valores_ui_input_alarma["pitch"])
        roll_val_ui = int(valores_ui_input_alarma["roll"])
        if not (5 <= pitch_val_ui <= 30): pitch_val_ui = 15 
        if not (5 <= roll_val_ui <= 30): roll_val_ui = 15 
        
        valores_ui_input_alarma["pitch"] = str(pitch_val_ui)
        valores_ui_input_alarma["roll"] = str(roll_val_ui)
        valores_alarma["max_pitch_pos"] = str(pitch_val_ui)
        valores_alarma["min_pitch_neg"] = str(-pitch_val_ui)
        valores_alarma["max_roll_pos"] = str(roll_val_ui)
        valores_alarma["min_roll_neg"] = str(-roll_val_ui)
        
        with open(ARCHIVO_CONFIG_ALARMA, 'w') as f: 
            json.dump(valores_alarma, f, indent=4) 
        return True
    except (IOError, ValueError) as e:
        print(f"Error al guardar configuración de alarma: {e}")
        return False

# Funciones de parseo NMEA
def parse_pfec_gpatt(sentence):
    global att_heading_str, att_pitch_str, att_roll_str, ultima_vez_datos_recibidos, ts_pitch_float, ts_roll_float
    try:
        parts = sentence.split(',')
        
        # Determinar los índices correctos basados en si la trama es 'GPatt' o 'GP'
        if len(parts) >= 5 and parts[1] == "GPatt":
            # Formato largo: $PFEC,GPatt,heading,pitch,roll*CS
            h_idx, p_idx, r_idx = 2, 3, 4
        elif len(parts) >= 4 and parts[1] == "GP":
             # Formato corto: $PFEC,GP,heading,pitch,roll*CS
            h_idx, p_idx, r_idx = 2, 3, 4 # Los índices de datos son los mismos, solo cambia la validación
        else:
            return # No es una trama que podamos parsear

        att_heading_str = parts[h_idx] if parts[h_idx] else "N/A"
        raw_pitch = parts[p_idx]
        att_pitch_str = raw_pitch if raw_pitch else "N/A"
        
        try:
            ts_pitch_float = float(raw_pitch)
        except (ValueError, IndexError):
            ts_pitch_float = 0.0
            
        raw_roll_part = parts[r_idx].split('*')[0]
        att_roll_str = raw_roll_part if raw_roll_part else "N/A"
        
        try:
            ts_roll_float = float(raw_roll_part)
        except (ValueError, IndexError):
            ts_roll_float = 0.0
            
        ultima_vez_datos_recibidos = pygame.time.get_ticks()

    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia PFEC: {e}. Sentencia: {sentence}")
    except Exception as e:
        print(f"Error inesperado en parse_pfec_gpatt: {e}. Sentencia: {sentence}")

def convertir_coord(coord_str, direccion, is_longitude=False):
    try:
        idx_punto = coord_str.find('.')
        if idx_punto == -1 or not coord_str or not direccion: 
            return 0.0 
        min_start_index = idx_punto - 2
        if min_start_index < 0: 
            return 0.0
        grados_str = coord_str[:min_start_index]
        minutos_str = coord_str[min_start_index:] 
        if not grados_str: 
            return 0.0
        grados = int(grados_str)
        minutos = float(minutos_str)
        decimal = grados + minutos / 60.0
        if direccion in ['S', 'W']: 
            decimal *= -1
        return round(decimal, 6)
    except: 
        return 0.0 
    


def parse_gll(sentence):
    global ultima_vez_datos_recibidos
    try:
        # Modificación: Aceptar $GPGLL, $GNGLL, u otros comunes para GLL
        if not (sentence.startswith('$GPGLL') or sentence.startswith('$GNGLL') or \
                sentence.startswith('$GAGLL') or sentence.startswith('$GLGLL')): # Añadir otros si es necesario
            return
            
        parts = sentence.split(',')
        
        # Validación más robusta (6 campos mínimos + checksum)
        if len(parts) < 7:
            return
            
        # Extraer el estado del campo parts[6]
        status_field = parts[6] 
        if not status_field: # Si el campo de estado está vacío
            return

        actual_status = status_field[0] # El estado es el primer carácter

        # Verificar que los datos son válidos (estado == 'A') y que los campos de lat/lon no están vacíos
        if actual_status != 'A' or not parts[1] or not parts[3]:
            return
            
        lat_raw_val = parts[1]
        lat_dir = parts[2]
        lon_raw_val = parts[3]
        lon_dir = parts[4]
        
        global latitude_str, longitude_str, ts_lat_decimal, ts_lon_decimal
        latitude_str_temp, longitude_str_temp = "N/A", "N/A"
        ts_lat_decimal_temp, ts_lon_decimal_temp = 0.0, 0.0
        
        # Procesamiento de latitud (igual que antes)
        if lat_raw_val and lat_dir and len(lat_raw_val) >= 2:
            lat_deg_ui = lat_raw_val[:2]
            lat_min_full_ui = lat_raw_val[2:]
            try: 
                lat_min_formatted_ui = f"{float(lat_min_full_ui):.3f}"
            except: 
                lat_min_formatted_ui = lat_min_full_ui 
            latitude_str_temp = f"{lat_deg_ui}° {lat_min_formatted_ui}' {lat_dir}"
            ts_lat_decimal_temp = convertir_coord(lat_raw_val, lat_dir, is_longitude=False)
        
        # Procesamiento de longitud (simplificado y corregido)
        if lon_raw_val and lon_dir:
            idx_punto_lon = lon_raw_val.find('.')
            # Longitud es DDDMM.MMMM o DDMM.MMMM, los minutos siempre empiezan 2 pos a la izquierda del punto
            if idx_punto_lon > 2:
                min_start_idx_lon = idx_punto_lon - 2
                lon_deg_ui = lon_raw_val[:min_start_idx_lon]
                lon_min_full_ui = lon_raw_val[min_start_idx_lon:]
                
                try: 
                    lon_min_formatted_ui = f"{float(lon_min_full_ui):.3f}"
                except: 
                    lon_min_formatted_ui = lon_min_full_ui
                
                longitude_str_temp = f"{lon_deg_ui}° {lon_min_formatted_ui}' {lon_dir}"
                ts_lon_decimal_temp = convertir_coord(lon_raw_val, lon_dir, is_longitude=True)
        
        latitude_str, longitude_str = latitude_str_temp, longitude_str_temp
        ts_lat_decimal, ts_lon_decimal = ts_lat_decimal_temp, ts_lon_decimal_temp
        ultima_vez_datos_recibidos = pygame.time.get_ticks()
        
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia GLL: {e}. Sentencia: {sentence}")
    except Exception as e:
        print(f"Error inesperado en parse_gll: {e}. Sentencia: {sentence}")

    

def parse_gga(sentence):
    global ultima_vez_datos_recibidos, altitude_str, ts_altitude_float # Añadir ts_altitude_float
    try:
        parts = sentence.split(',')
       
        if len(parts) > 10 and parts[9]: # Verificar que el campo de altitud y su unidad existan
            lat_raw_val = parts[2]
            lat_dir = parts[3]
            lon_raw_val = parts[4]
            lon_dir = parts[5]
            
            # Procesar Altitud
            alt_val_str = parts[9]
            alt_unit_str = parts[10] if parts[10] else "M" # Asumir Metros si la unidad está vacía pero el valor existe

            if alt_val_str: # Si hay un valor de altitud
                try:
                    ts_altitude_float = float(alt_val_str) # Convertir a float para ThingSpeak
                    altitude_str = f"{alt_val_str} {alt_unit_str}"
                    ultima_vez_datos_recibidos = pygame.time.get_ticks() # Actualizar si obtenemos altitud
                except ValueError:
                    altitude_str = "N/A"
                    ts_altitude_float = 0.0 # Valor por defecto si no es un número válido
            else:
                altitude_str = "N/A"
                ts_altitude_float = 0.0

            global latitude_str, longitude_str, ts_lat_decimal, ts_lon_decimal
            latitude_str_temp, longitude_str_temp = "N/A", "N/A"
            ts_lat_decimal_temp, ts_lon_decimal_temp = 0.0, 0.0
            
            if lat_raw_val and lat_dir and len(lat_raw_val) >=2:
                lat_deg_ui = lat_raw_val[:2]
                lat_min_full_ui = lat_raw_val[2:]
                try: 
                    lat_min_formatted_ui = f"{float(lat_min_full_ui):.3f}"
                except: 
                    lat_min_formatted_ui = lat_min_full_ui 
                latitude_str_temp = f"{lat_deg_ui}° {lat_min_formatted_ui}' {lat_dir}"
                ts_lat_decimal_temp = convertir_coord(lat_raw_val, lat_dir, is_longitude=False)
            
            if lon_raw_val and lon_dir:
                idx_punto_lon = lon_raw_val.find('.')
                if idx_punto_lon > 2:
                    min_start_idx_lon = idx_punto_lon - 2
                    lon_deg_ui = lon_raw_val[:min_start_idx_lon]
                    lon_min_full_ui = lon_raw_val[min_start_idx_lon:]
                    try:
                        lon_min_formatted_ui = f"{float(lon_min_full_ui):.3f}"
                    except:
                        lon_min_formatted_ui = lon_min_full_ui
                    longitude_str_temp = f"{lon_deg_ui}° {lon_min_formatted_ui}' {lon_dir}"
                    ts_lon_decimal_temp = convertir_coord(lon_raw_val, lon_dir, is_longitude=True)
            
            latitude_str, longitude_str = latitude_str_temp, longitude_str_temp
            ts_lat_decimal, ts_lon_decimal = ts_lat_decimal_temp, ts_lon_decimal_temp
            ultima_vez_datos_recibidos = pygame.time.get_ticks()
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia GGA: {e}. Sentencia: {sentence}")
    except Exception as e:
        print(f"Error inesperado en parse_gga: {e}. Sentencia: {sentence}")

def parse_rmc(sentence):
    global ultima_vez_datos_recibidos
    try:
        parts = sentence.split(',')
        if len(parts) > 6 and parts[3] and parts[4] and parts[5] and parts[6]: 
            lat_raw_val = parts[3]
            lat_dir = parts[4]
            lon_raw_val = parts[5]
            lon_dir = parts[6]
            
            global latitude_str, longitude_str, ts_lat_decimal, ts_lon_decimal
            latitude_str_temp, longitude_str_temp = "N/A", "N/A"
            ts_lat_decimal_temp, ts_lon_decimal_temp = 0.0, 0.0
            
            if lat_raw_val and lat_dir and len(lat_raw_val) >=2:
                lat_deg_ui = lat_raw_val[:2]
                lat_min_full_ui = lat_raw_val[2:]
                try: 
                    lat_min_formatted_ui = f"{float(lat_min_full_ui):.3f}"
                except: 
                    lat_min_formatted_ui = lat_min_full_ui 
                latitude_str_temp = f"{lat_deg_ui}° {lat_min_formatted_ui}' {lat_dir}"
                ts_lat_decimal_temp = convertir_coord(lat_raw_val, lat_dir, is_longitude=False)
            
            if lon_raw_val and lon_dir:
                idx_punto_lon = lon_raw_val.find('.')
                if idx_punto_lon > 2:
                    min_start_idx_lon = idx_punto_lon - 2
                    lon_deg_ui = lon_raw_val[:min_start_idx_lon]
                    lon_min_full_ui = lon_raw_val[min_start_idx_lon:]
                    try:
                        lon_min_formatted_ui = f"{float(lon_min_full_ui):.3f}"
                    except:
                        lon_min_formatted_ui = lon_min_full_ui
                    longitude_str_temp = f"{lon_deg_ui}° {lon_min_formatted_ui}' {lon_dir}"
                    ts_lon_decimal_temp = convertir_coord(lon_raw_val, lon_dir, is_longitude=True)
            
            latitude_str, longitude_str = latitude_str_temp, longitude_str_temp
            ts_lat_decimal, ts_lon_decimal = ts_lat_decimal_temp, ts_lon_decimal_temp
            ultima_vez_datos_recibidos = pygame.time.get_ticks()
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia RMC: {e}. Sentencia: {sentence}")
    except Exception as e:
        print(f"Error inesperado en parse_rmc: {e}. Sentencia: {sentence}")

def parse_vtg(sentence):
    global speed_str, ultima_vez_datos_recibidos, ts_speed_float
    try: 
        parts = sentence.split(',')
        speed_val_str_ui = "N/A"
        temp_speed_float = 0.0
        if len(parts) > 5 and parts[5]: 
            speed_val_str_ui = parts[5] 
            try: 
                temp_speed_float = float(speed_val_str_ui)
            except: 
                temp_speed_float = 0.0
        elif len(parts) > 7 and parts[7]: 
            speed_kmh_str = parts[7]
            try: 
                speed_kmh = float(speed_kmh_str)
                temp_speed_float = round(speed_kmh / 1.852, 1)
                speed_val_str_ui = str(temp_speed_float)
            except: 
                pass
        if speed_val_str_ui != "N/A": 
            speed_str = f"{speed_val_str_ui} Kt"
            ts_speed_float = temp_speed_float
            ultima_vez_datos_recibidos = pygame.time.get_ticks()
        else: 
            speed_str = "N/A Kt"
            ts_speed_float = 0.0
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia VTG: {e}. Sentencia: {sentence}")
    except Exception as e:
        print(f"Error inesperado en parse_vtg: {e}. Sentencia: {sentence}")

def parse_hdt(sentence):
    global heading_str, ultima_vez_datos_recibidos, ts_heading_float
    try: 
        parts = sentence.split(',') 
        if len(parts) > 1 and parts[1]: 
            heading_val_str = parts[1]
            try: 
                heading_val_float = float(heading_val_str)
                heading_str = f"{heading_val_float:.1f}°"
                ts_heading_float = heading_val_float      
            except: 
                heading_str = f"{heading_val_str}°"
                ts_heading_float = 0.0 
            ultima_vez_datos_recibidos = pygame.time.get_ticks()
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia HDT: {e}. Sentencia: {sentence}")
    except Exception as e:
        print(f"Error inesperado en parse_hdt: {e}. Sentencia: {sentence}")

def parse_hdg(sentence):
    global heading_str, ultima_vez_datos_recibidos, ts_heading_float
    try: 
        parts = sentence.split(',') 
        if len(parts) > 1 and parts[1]: 
            heading_val_str = parts[1] 
            try: 
                heading_val_float = float(heading_val_str)
                heading_str = f"{heading_val_float:.0f}°"
                ts_heading_float = heading_val_float      
            except: 
                heading_str = f"{heading_val_str}°"
                ts_heading_float = 0.0
            ultima_vez_datos_recibidos = pygame.time.get_ticks()
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia HDG: {e}. Sentencia: {sentence}")
    except Exception as e:
        print(f"Error inesperado en parse_hdg: {e}. Sentencia: {sentence}")

def parse_gpzda(sentence):
    global ts_timestamp_str 
    try:
        parts = sentence.split(',')
        if len(parts) >= 5: 
            time_utc_str = parts[1]
            day_str = parts[2]
            month_str = parts[3]
            year_str = parts[4]
            if '.' in time_utc_str: 
                time_utc_str = time_utc_str.split('.')[0]
            if len(time_utc_str) == 6 and day_str and month_str and year_str and len(year_str) == 4:
                h = time_utc_str[0:2]
                m = time_utc_str[2:4]
                s = time_utc_str[4:6]
                ts_timestamp_str = f"{year_str}-{month_str.zfill(2)}-{day_str.zfill(2)} {h}:{m}:{s}"
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia GPZDA/GNZDA: {e}. Sentencia: {sentence}")
    except Exception as e:
        print(f"Error inesperado en parse_gpzda: {e}. Sentencia: {sentence}")

def parse_phdl(sentence):
    """Parsea la sentencia propietaria $PHDL para el estado de las sentinas."""
    global switch1_status, switch2_status, ultima_vez_datos_recibidos
    try:
        parts = sentence.split(',')
        if len(parts) >= 6 and parts[0] == '$PHDL' and parts[1] == 'SWITCH':
            # Asumiendo que parts[2] es el índice y parts[3] es el estado
            if parts[2] == '1':
                switch1_status = parts[3].upper() # ON/OFF
            if parts[4] == '2':
                switch2_status = parts[5].split('*')[0].upper() # Limpiar checksum
            
            ultima_vez_datos_recibidos = pygame.time.get_ticks()
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia PHDL: {e}. Sentencia: {sentence}")

def parse_rot(sentence):
    """Parsea la sentencia GPROT para la tasa de giro."""
    global rot_float, ultima_vez_datos_recibidos
    try:
        parts = sentence.split(',')
        if len(parts) >= 2 and parts[0] == '$GPROT':
            rot_value_str = parts[1]
            if rot_value_str:
                rot_float = float(rot_value_str)
                ultima_vez_datos_recibidos = pygame.time.get_ticks()
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia GPROT: {e}. Sentencia: {sentence}")

def reset_ui_data():
    global latitude_str, longitude_str, speed_str, heading_str
    global att_pitch_str, att_roll_str, att_heading_str, altitude_str
    global ts_pitch_float, ts_roll_float, ts_lat_decimal, ts_lon_decimal
    global ts_speed_float, ts_heading_float, ts_timestamp_str, ts_altitude_float # Añadir ts_altitude_float
    global alarma_roll_babor_activa, alarma_roll_estribor_activa
    global alarma_pitch_sentado_activa, alarma_pitch_encabuzado_activa
    global ultima_reproduccion_alarma_babor_tiempo, ultima_reproduccion_alarma_estribor_tiempo
    global ultima_reproduccion_alarma_sentado_tiempo, ultima_reproduccion_alarma_encabuzado_tiempo
    global sonido_alarma_actualmente_reproduciendo, INDICE_PROXIMA_ALARMA_A_SONAR

    latitude_str = "N/A"
    longitude_str = "N/A"
    speed_str = "N/A Kt" 
    heading_str = "N/A°" 
    att_pitch_str = "N/A"
    att_roll_str = "N/A"
    att_heading_str = "N/A"
    altitude_str = "N/A" # Resetear altitude_str
    
    ts_pitch_float = 0.0
    ts_roll_float = 0.0
    ts_lat_decimal = 0.0
    ts_lon_decimal = 0.0
    ts_speed_float = 0.0
    ts_heading_float = 0.0
    ts_timestamp_str = "N/A"
    ts_altitude_float = 0.0 # Resetear ts_altitude_float

    # Resetear ROT y sentinas
    rot_float = 0.0
    switch1_status = "N/A"
    switch2_status = "N/A"

    # Resetear estados de alarma
    alarma_roll_babor_activa = False
    alarma_roll_estribor_activa = False
    alarma_pitch_sentado_activa = False
    alarma_pitch_encabuzado_activa = False

    # Resetear temporizadores de repetición de alarma
    ultima_reproduccion_alarma_babor_tiempo = 0.0
    ultima_reproduccion_alarma_estribor_tiempo = 0.0
    ultima_reproduccion_alarma_sentado_tiempo = 0.0
    ultima_reproduccion_alarma_encabuzado_tiempo = 0.0

    # Detener sonido de alarma actual y resetear gestor de sonido
    if sonido_alarma_actualmente_reproduciendo is not None:
        sonido_alarma_actualmente_reproduciendo.stop()
        sonido_alarma_actualmente_reproduciendo = None
    INDICE_PROXIMA_ALARMA_A_SONAR = 0

def init_csv():
    print(f"DEBUG: init_csv - Intentando inicializar/verificar: {CSV_FILENAME}")
    try:
        file_exists = os.path.exists(CSV_FILENAME)
        is_empty = False
        if file_exists:
            is_empty = os.path.getsize(CSV_FILENAME) == 0

        with open(CSV_FILENAME, 'a', newline='') as f: 
            if not file_exists or is_empty:
                writer = csv.writer(f)
                writer.writerow(["ShipID", "Pitch", "Roll", "Latitud", "Longitud", "Velocidad", "Rumbo", "ROT", "Switch1", "Switch2"])
                print(f"DEBUG: init_csv - Cabecera escrita en: {CSV_FILENAME}")
            else:
                print(f"DEBUG: init_csv - Archivo ya existe y no está vacío: {CSV_FILENAME}")
        print(f"DEBUG: init_csv - Finalizado para: {CSV_FILENAME}")
    except Exception as e:
        print(f"[ERROR] En init_csv para {CSV_FILENAME}: {e}")

# --- Función para añadir mensajes a la consola de datos ---
def agregar_a_consola(mensaje: str):
    """Añade un mensaje al buffer de la consola, manteniendo un tamaño máximo."""
    global datos_consola_buffer, MAX_LINEAS_CONSOLA
    if len(datos_consola_buffer) >= MAX_LINEAS_CONSOLA:
        datos_consola_buffer.pop(0) # Eliminar el mensaje más antiguo
    datos_consola_buffer.append(f"[{time.strftime('%H:%M:%S')}] {mensaje}")


def init_alarm_csv():
    print(f"DEBUG: init_alarm_csv - Intentando inicializar/verificar: {ALARM_LOG_FILENAME}")
    try:
        file_exists_before_open = os.path.exists(ALARM_LOG_FILENAME)
        is_empty = False
        if file_exists_before_open:
            is_empty = os.path.getsize(ALARM_LOG_FILENAME) == 0
        
        with open(ALARM_LOG_FILENAME, 'a', newline='') as f:
            if not file_exists_before_open or is_empty:
                writer = csv.writer(f)
                writer.writerow(["TimestampUTC", "TipoAlarma", "EstadoAlarma", "ValorActual", "UmbralConfigurado"])
                print(f"DEBUG: init_alarm_csv - Cabecera escrita en: {ALARM_LOG_FILENAME}")
            else:
                print(f"DEBUG: init_alarm_csv - Archivo ya existe y no está vacío: {ALARM_LOG_FILENAME}")
        print(f"DEBUG: init_alarm_csv - Finalizado para: {ALARM_LOG_FILENAME}")

    except FileExistsError: 
        print(f"DEBUG: init_alarm_csv - Archivo ya existe (manejado por FileExistsError): {ALARM_LOG_FILENAME}")
        pass 
    except Exception as e:
        print(f"[ERROR] En init_alarm_csv para {ALARM_LOG_FILENAME}: {e}")


def guardar_alarma_csv(timestamp, tipo_alarma, estado_alarma, valor_actual, umbral_configurado):
    print(f"DEBUG: guardar_alarma_csv - Intentando escribir en: {ALARM_LOG_FILENAME}")
    print(f"DEBUG: Datos a guardar: TS={timestamp}, Tipo={tipo_alarma}, Estado={estado_alarma}, Val={valor_actual}, Umbral={umbral_configurado}")
    try:
        with open(ALARM_LOG_FILENAME, 'a', newline='') as f: 
            writer = csv.writer(f)
            writer.writerow([timestamp, tipo_alarma, estado_alarma, valor_actual, umbral_configurado])
        print(f"DEBUG: guardar_alarma_csv - Escritura exitosa en: {ALARM_LOG_FILENAME}")
    except Exception as e:
        print(f"[ERROR] No se pudo escribir en {ALARM_LOG_FILENAME}: {e}")


def guardar_csv():
    try:
        with open(CSV_FILENAME, 'a', newline='') as f: 
            writer = csv.writer(f)
            writer.writerow([
                API_KEY_GOOGLE_CLOUD, # Nombre del barco
                ts_pitch_float, 
                ts_roll_float, 
                ts_lat_decimal, 
                ts_lon_decimal, 
                ts_speed_float, 
                ts_heading_float,
                rot_float,
                switch1_status,
                switch2_status
            ])
    except Exception as e:
        print(f"[ERROR] No se pudo escribir en {CSV_FILENAME} (guardar_csv): {e}")



def check_network_connection():
    """Verifica si hay conexión a internet haciendo una petición a Google."""
    global network_available
    try:
        # Usar un timeout bajo para no bloquear por mucho tiempo
        requests.get("https://www.google.com", timeout=5)
        print("INFO: Conexión de red restablecida.")
        agregar_a_consola("Red restablecida.")
        network_available = True
    except requests.exceptions.RequestException:
        print("INFO: Aún no hay conexión de red.")
        agregar_a_consola("Sin conexión de red.")
        network_available = False

def worker_enviar_thingspeak(payload):
    """Esta función se ejecuta en un hilo separado para no bloquear la UI."""
    global network_available
    try:
        r = requests.get(THINGSPEAK_URL, params=payload, timeout=10) 
        if r.status_code == 200: 
            # El timestamp puede no ser el actual, pero es una buena aproximación.
            msg_ts = f"ThingSpeak OK (desde hilo)"
            print(f"[OK] {msg_ts}")
            agregar_a_consola(msg_ts)
            network_available = True # Si tiene éxito, la red está disponible
        else: 
            msg_ts_err = f"ThingSpeak ERR: {r.status_code} - {r.text}"
            print(f"[ERROR] {msg_ts_err}")
            agregar_a_consola(msg_ts_err)
            # No asumimos pérdida de red por errores de la API, solo por excepciones de conexión
    except requests.exceptions.RequestException as e: 
        msg_ts_conn_err = f"ThingSpeak Conn. ERR: {e}"
        print(f"[ERROR] {msg_ts_conn_err}")
        agregar_a_consola(f"Sin red: {e}")
        network_available = False

def enviar_thingspeak():
    global PROGRAM_MODE
    if PROGRAM_MODE == "TRIAL_EXPIRED":
        print("INFO: Modo trial expirado. Envío a ThingSpeak deshabilitado.")
        return

    estado_alarma_para_thingspeak = "SIN ALARMA"
    if alarma_roll_babor_activa:
        estado_alarma_para_thingspeak = "ALARMA BABOR"
    elif alarma_roll_estribor_activa:
        estado_alarma_para_thingspeak = "ALARMA ESTRIBOR"
    
    if alarma_pitch_sentado_activa:
        estado_alarma_para_thingspeak += " Y SENTADO" if "ALARMA" in estado_alarma_para_thingspeak else "ALARMA SENTADO"
    elif alarma_pitch_encabuzado_activa:
        estado_alarma_para_thingspeak += " Y ENCABUZADO" if "ALARMA" in estado_alarma_para_thingspeak else "ALARMA ENCABUZADO"

    payload = {
        'api_key': API_KEY_THINGSPEAK, 
        'field1': ts_pitch_float, 
        'field2': ts_roll_float, 
        'field3': ts_lat_decimal, 
        'field4': ts_lon_decimal, 
        'field5': ts_speed_float, 
        'field6': ts_heading_float, 
        'field7': ts_altitude_float,
        'field8': rot_float,
        'status': f"Sentina1: {switch1_status}, Sentina2: {switch2_status}, Alarma: {estado_alarma_para_thingspeak}"
    }
    
    # Crear y lanzar el hilo
    thread = threading.Thread(target=worker_enviar_thingspeak, args=(payload,))
    thread.daemon = True # El hilo no impedirá que el programa se cierre
    thread.start()

def worker_enviar_sql(payload):
    """Esta función se ejecuta en un hilo separado para no bloquear la UI."""
    global network_available

    # --- Detección automática de Driver ODBC ---
    sql_server_driver = None
    try:
        available_drivers = pyodbc.drivers()
        # Palabras clave para buscar, en orden de preferencia (de más nuevo a más antiguo)
        preferred_keywords = ["ODBC Driver 18", "ODBC Driver 17", "Native Client", "SQL Server"]
        
        for keyword in preferred_keywords:
            for driver in available_drivers:
                if keyword in driver:
                    sql_server_driver = driver
                    break  # Encontramos el mejor driver posible, salir del bucle interno
            if sql_server_driver:
                break # Salir del bucle externo también
    
    except Exception as e:
        msg_sql_err = f"Azure SQL: Error al listar drivers ODBC: {e}"
        print(f"[ERROR] {msg_sql_err}")
        agregar_a_consola(msg_sql_err)
        network_available = False
        return

    if not sql_server_driver:
        msg_sql_err = "Azure SQL: No se encontró un driver ODBC para SQL Server."
        print(f"[ERROR] {msg_sql_err}")
        print(f"INFO: Drivers disponibles en el sistema: {available_drivers}")
        agregar_a_consola(msg_sql_err)
        agregar_a_consola(f"Drivers: {available_drivers}") # Añadir a la consola para depuración del usuario
        network_available = False
        return
    # --- Fin de la detección automática ---

    conn = None
    try:
        conn_str = (
            f"DRIVER={{{sql_server_driver}}};"
            f"SERVER={AZURE_SQL_SERVER};"
            f"DATABASE={AZURE_SQL_DATABASE};"
            f"UID={AZURE_SQL_USER};"
            f"PWD={AZURE_SQL_PASSWORD};"
        )
        print(f"INFO: Intentando conectar con el driver detectado: {sql_server_driver}")
        conn = pyodbc.connect(conn_str, timeout=10)
        print(f"✅ Conexión exitosa con el driver: {sql_server_driver}")
    
    except pyodbc.Error as ex:
        msg_sql_err = f"Azure SQL: Fallo la conexión con driver '{sql_server_driver}'."
        print(f"[ERROR] {msg_sql_err} - {ex}")
        agregar_a_consola(f"Azure SQL: Fallo conexión. Verifique red y contraseña.")
        network_available = False
        return # Salir si la conexión falla
    except Exception as e:
        # Captura de otros posibles errores en la conexión
        msg_sql_err = f"Azure SQL: Error inesperado al conectar: {e}"
        print(f"[ERROR] {msg_sql_err}")
        agregar_a_consola(msg_sql_err)
        network_available = False
        return

    try:
        with conn.cursor() as cursor:
            sql_insert = """
            INSERT INTO [dbo].[Sensor_Flota] 
            (ShipID, Date_event, Pitch, Roll, Latitud,Longitud , Velocidad, Rumbo, Rot, Sentina1, Sentina2) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql_insert, 
                           payload['ShipID'], 
                           payload['Date_event'], 
                           payload['Pitch'], 
                           payload['Roll'], 
                           payload['Latitud'], 
                           payload['Longitud'], 
                           payload['Velocidad'], 
                           payload['Rumbo'], 
                           payload['Rot'], 
                           payload['Sentina1'],
                           payload['Sentina2'],)
            conn.commit()
            msg_sql = "Azure SQL: Conexión OK y datos enviados."
            print(f"[OK] {msg_sql}")
            agregar_a_consola(msg_sql)
            network_available = True
    except pyodbc.Error as ex:
        print(f"❌ Error al interactuar con la base de datos: {ex}")
        msg_sql_err = f"Azure SQL: Error de base de datos - {ex}"
        print(f"[ERROR] {msg_sql_err}")
        agregar_a_consola(msg_sql_err)
        network_available = False
    except Exception as e:
        print(f"❌ Error inesperado de SQL: {e}")
        msg_sql_conn_err = f"Azure SQL: Error de conexión - {e}"
        print(f"[ERROR] {msg_sql_conn_err}")
        agregar_a_consola(msg_sql_conn_err)
        network_available = False
    finally:
        if conn:
            conn.close()

def enviar_y_guardar_datos_periodicamente():
    """Guarda en CSV y envía a servicios en la nube a intervalos regulares."""
    global ultima_vez_envio_datos

    if time.time() - ultima_vez_envio_datos < INTERVALO_ENVIO_DATOS_S:
        return

    # Solo proceder si hay datos válidos
    if not (serial_port_available and not nmea_data_stale):
        ultima_vez_envio_datos = time.time() # Resetear timer para no reintentar inmediatamente
        return

    # Preparar estado de alarma para logging y envío
    partes_alarma = []
    if alarma_roll_babor_activa: partes_alarma.append("B")
    if alarma_roll_estribor_activa: partes_alarma.append("E")
    if alarma_pitch_sentado_activa: partes_alarma.append("S")
    if alarma_pitch_encabuzado_activa: partes_alarma.append("EN")
    estado_alarma_sql_corto = "+".join(partes_alarma) if partes_alarma else "OK"

    print(f"--- Guardando y Enviando Datos ({time.strftime('%Y-%m-%d %H:%M:%S')}) ---")
    print(f"ID:{API_KEY_GOOGLE_CLOUD}, P:{ts_pitch_float}, R:{ts_roll_float}, Lat:{ts_lat_decimal}, Lon:{ts_lon_decimal}, Spd:{ts_speed_float}, Hdg:{ts_heading_float}, Alt:{ts_altitude_float}, ROT:{rot_float}, S1:{switch1_status}, S2:{switch2_status}, Alarma:{estado_alarma_sql_corto}")
    agregar_a_consola(f"ID:{API_KEY_GOOGLE_CLOUD}, P:{ts_pitch_float:.1f}, R:{ts_roll_float:.1f}, ROT:{rot_float:.1f}, S1:{switch1_status}, S2:{switch2_status}, Alarma:{estado_alarma_sql_corto}")

    # Guardar en CSV
    guardar_csv()
    agregar_a_consola(f"Guardado en CSV: {CSV_FILENAME}")

    # Enviar a servicio en la nube si hay red
    if network_available:
        if SERVICIO_DATOS_ACTUAL == "thingspeak":
            enviar_thingspeak()
        elif SERVICIO_DATOS_ACTUAL == "azure_sql":
            timestamp_final = ts_timestamp_str if ts_timestamp_str != "N/A" else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            payload_sql = {
                'ShipID': API_KEY_GOOGLE_CLOUD,
                'Date_event': timestamp_final,
                'Pitch': ts_pitch_float, 'Roll': ts_roll_float,
                'Latitud': ts_lat_decimal, 'Longitud': ts_lon_decimal,
                'Velocidad': ts_speed_float, 'Rumbo': ts_heading_float,
                'Rot': rot_float,
                'Sentina1': switch1_status,
                'Sentina2': switch2_status
            }
            sql_thread = threading.Thread(target=worker_enviar_sql, args=(payload_sql,))
            sql_thread.daemon = True
            sql_thread.start()
    
    print("---------------------------------------------------\n")
    ultima_vez_envio_datos = time.time()

def procesar_datos_serie():
    """Lee y procesa las sentencias NMEA, reconstruyendo tramas fragmentadas."""
    global ser, serial_port_available, nmea_data_stale, nmea_buffer
    global mostrar_ventana_test_serial, datos_test_serial_buffer, MAX_LINEAS_TEST_SERIAL

    if not (serial_port_available and ser and ser.is_open):
        return

    try:
        if ser.in_waiting > 0:
            data_bytes = ser.read(ser.in_waiting)
            data_str = data_bytes.decode('ascii', errors='replace')
            
            # Añadir los datos nuevos al buffer
            nmea_buffer += data_str

            # Procesar el buffer línea por línea
            while '\r\n' in nmea_buffer:
                line, nmea_buffer = nmea_buffer.split('\r\n', 1)
                
                # Limpiar la línea de caracteres nulos o extraños antes de procesar
                line = ''.join(filter(lambda x: x in '0123456789,.-*ABCDEFGHIJKLMNOPQRSTUVWXYZ$', line))

                if not line:
                    continue

                # Añadir la línea cruda (reconstruida) a la ventana de test si está abierta
                if mostrar_ventana_test_serial:
                    if len(datos_test_serial_buffer) >= MAX_LINEAS_TEST_SERIAL:
                        datos_test_serial_buffer.pop(0)
                    datos_test_serial_buffer.append(line)

                # Parsear las sentencias NMEA completas
                if line.startswith('$GPGLL') or line.startswith('$GNGLL'):
                    parse_gll(line)
                elif line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                    parse_gga(line)
                elif line.startswith('$GPRMC') or line.startswith('$GNRMC'):
                    parse_rmc(line)
                elif line.startswith('$GPVTG') or line.startswith('$GNVTG'):
                    parse_vtg(line)
                elif line.startswith('$GPHDT') or line.startswith('$GNHDT') or line.startswith('$HEHDT'):
                    parse_hdt(line)
                elif line.startswith('$GPHDG') or line.startswith('$GNHDG'):
                    parse_hdg(line)
                elif line.startswith('$PFEC,GP'): # Captura tanto GPatt como GP
                    parse_pfec_gpatt(line)
                elif line.startswith('$GPZDA') or line.startswith('$GNZDA'):
                    parse_gpzda(line)
                elif line.startswith('$PHDL'):
                    parse_phdl(line)
                elif line.startswith('$GPROT'):
                    parse_rot(line)

    except serial.SerialException as se:
        print(f"SerialException durante lectura: {se}. Marcando puerto como desconectado.")
        if ser:
            ser.close()
        ser = None
        serial_port_available = False
        reset_ui_data()
        nmea_data_stale = True
    except Exception as e:
        print(f"Error general durante lectura/procesamiento NMEA: {e}")
        pass

def main():
    """Dibuja la ventana de activación de licencia."""
    font_titulo = pygame.font.Font(None, 36)
    font_texto = pygame.font.Font(None, 28)
    font_error = pygame.font.Font(None, 24)
    font_boton_med = pygame.font.Font(None, 26) # Fuente para botones un poco más anchos
    font_boton_pequeno = pygame.font.Font(None, 22) # Fuente para botones más pequeños si el texto es largo

    ventana_width = 500
    ventana_height = 450 # Aumentada para nueva disposición y mensaje de error
    ventana_x = (screen.get_width() - ventana_width) // 2
    ventana_y = (screen.get_height() - ventana_height) // 2
    rect_ventana = pygame.Rect(ventana_x, ventana_y, ventana_width, ventana_height)

    # Colores
    color_fondo_ventana = (220, 220, 220)
    color_borde_ventana = (100, 100, 100)
    color_texto = (0, 0, 0)
    color_input_fondo = (255, 255, 255)
    color_input_borde = (50, 50, 50)
    color_boton_fondo = (180, 180, 180)
    color_boton_texto = (0, 0, 0)
    color_error_texto = (200, 0, 0)

    # Dibujar ventana
    pygame.draw.rect(screen, color_fondo_ventana, rect_ventana)
    pygame.draw.rect(screen, color_borde_ventana, rect_ventana, 2)

    # Título
    titulo_surf = font_titulo.render(TEXTOS[IDIOMA]["activation_required"], True, color_texto)
    screen.blit(titulo_surf, (rect_ventana.centerx - titulo_surf.get_width() // 2, rect_ventana.top + 20))

    # Mostrar ID de Máquina (Display ID)
    id_label_surf = font_texto.render(TEXTOS[IDIOMA]["machine_id_label"], True, color_texto)
    screen.blit(id_label_surf, (rect_ventana.left + 30, rect_ventana.top + 70))
    id_value_surf = font_texto.render(display_id_str, True, color_texto)
    screen.blit(id_value_surf, (rect_ventana.left + 30 + id_label_surf.get_width() + 10, rect_ventana.top + 70))

    # Posición del ID de máquina (para referencia)
    id_text_y_pos = rect_ventana.top + 70
    id_value_rect = id_value_surf.get_rect(top=id_text_y_pos) # Solo para obtener altura y bottom

    # Botón "Copiar ID" - Centrado debajo del ID de máquina
    button_copiar_id_w = 120 # Ancho ajustado
    button_copiar_id_h = 30
    y_copiar_id = id_text_y_pos + id_value_rect.height + 10 # 10px debajo del texto del ID
    rect_boton_copiar_id = pygame.Rect(0, 0, button_copiar_id_w, button_copiar_id_h)
    rect_boton_copiar_id.centerx = rect_ventana.centerx
    rect_boton_copiar_id.top = y_copiar_id
    
    pygame.draw.rect(screen, color_boton_fondo, rect_boton_copiar_id)
    pygame.draw.rect(screen, color_input_borde, rect_boton_copiar_id, 1)
    copiar_id_text_surf = font_boton_pequeno.render(TEXTOS[IDIOMA]["copy_id_button"], True, color_boton_texto)
    screen.blit(copiar_id_text_surf, copiar_id_text_surf.get_rect(center=rect_boton_copiar_id.center))

    # Etiqueta para Clave de Licencia (debajo de Copiar ID)
    y_label_clave = rect_boton_copiar_id.bottom + 15
    key_label_surf = font_texto.render(TEXTOS[IDIOMA]["license_key_label"], True, color_texto)
    screen.blit(key_label_surf, (rect_ventana.left + 30, y_label_clave))

    # Campo de entrada para Clave de Licencia
    y_input_clave = y_label_clave + key_label_surf.get_height() + 5
    rect_input_key = pygame.Rect(rect_ventana.left + 30, y_input_clave, ventana_width - 60, 35)
    pygame.draw.rect(screen, color_input_fondo, rect_input_key)
    pygame.draw.rect(screen, color_input_borde, rect_input_key, 1)
    input_key_surf = font_texto.render(input_key_str, True, color_texto)
    screen.blit(input_key_surf, (rect_input_key.left + 5, rect_input_key.centery - input_key_surf.get_height() // 2))

    # Mensaje de error/feedback (debajo del input de clave)
    y_despues_del_mensaje = rect_input_key.bottom + 8 # Posición Y base después del input key + padding para mensaje
    if error_message:
        error_surf = font_error.render(error_message, True, color_error_texto)
        screen.blit(error_surf, (rect_ventana.centerx - error_surf.get_width() // 2, y_despues_del_mensaje))
        y_inicio_area_botones = y_despues_del_mensaje + error_surf.get_height() + 15 # 15px padding después del mensaje
    else:
        y_inicio_area_botones = y_despues_del_mensaje + 15 # 15px padding incluso si no hay mensaje (o ajustar si se quiere más pegado)

    # --- Nueva Disposición de Botones ---
    button_height = 40
    espacio_vertical_entre_filas = 15
    espacio_entre_botones_horizontal = 20 # Espacio entre botones en la misma fila
    
    # Calcular la altura total del bloque de los 4 botones (2 filas)
    altura_total_bloque_botones = (2 * button_height) + espacio_vertical_entre_filas

    # Determinar el espacio vertical disponible para centrar los botones
    padding_inferior_ventana = 20 # Espacio deseado en la parte inferior de la ventana
    espacio_vertical_disponible_para_bloque = rect_ventana.bottom - y_inicio_area_botones - padding_inferior_ventana
    
    # Calcular la coordenada Y para la primera fila de botones para centrar el bloque
    offset_y_bloque_botones = 0
    if espacio_vertical_disponible_para_bloque > altura_total_bloque_botones:
        offset_y_bloque_botones = (espacio_vertical_disponible_para_bloque - altura_total_bloque_botones) / 2
    
    y_botones_fila1 = y_inicio_area_botones + offset_y_bloque_botones
    
    w_usar_lic = 190 # "Usar Archivo Lic."
    w_guardar_id = 160 # "Guardar ID"
    
    # Cálculo para centrar los dos botones con espacio entre ellos
    ancho_total_fila1 = w_usar_lic + espacio_entre_botones_horizontal + w_guardar_id
    x_inicio_fila1 = rect_ventana.left + (ventana_width - ancho_total_fila1) // 2 # Corregido: relativo a rect_ventana.left
    
    rect_boton_usar_archivo = pygame.Rect(x_inicio_fila1, y_botones_fila1, w_usar_lic, button_height)
    rect_boton_guardar_id = pygame.Rect(x_inicio_fila1 + w_usar_lic + espacio_entre_botones_horizontal, y_botones_fila1, w_guardar_id, button_height)

    # Fila 2: "Activar" y "Salir"
    y_botones_fila2 = y_botones_fila1 + button_height + espacio_vertical_entre_filas 
    w_activar = 120
    w_salir = 120

    ancho_total_fila2 = w_activar + espacio_entre_botones_horizontal + w_salir
    x_inicio_fila2 = rect_ventana.left + (ventana_width - ancho_total_fila2) // 2 # Corregido: relativo a rect_ventana.left

    rect_boton_activar = pygame.Rect(x_inicio_fila2, y_botones_fila2, w_activar, button_height)
    rect_boton_salir_app = pygame.Rect(x_inicio_fila2 + w_activar + espacio_entre_botones_horizontal, y_botones_fila2, w_salir, button_height)

    # Fila 3: "Obtener Licencia Online"
    y_botones_fila3 = y_botones_fila2 + button_height + espacio_vertical_entre_filas
    w_obtener_lic = 220
    rect_boton_obtener_licencia = pygame.Rect(rect_ventana.centerx - w_obtener_lic // 2, y_botones_fila2 + 50, w_obtener_lic, button_height)


    # Dibujar botones y sus textos
    # "Usar Archivo Lic."
    pygame.draw.rect(screen, color_boton_fondo, rect_boton_usar_archivo)
    pygame.draw.rect(screen, color_input_borde, rect_boton_usar_archivo, 1)
    usar_archivo_text_surf = font_boton_med.render(TEXTOS[IDIOMA]["use_license_file_button"], True, color_boton_texto)
    screen.blit(usar_archivo_text_surf, usar_archivo_text_surf.get_rect(center=rect_boton_usar_archivo.center))

    # "Guardar ID"
    pygame.draw.rect(screen, color_boton_fondo, rect_boton_guardar_id)
    pygame.draw.rect(screen, color_input_borde, rect_boton_guardar_id, 1)
    guardar_id_text_surf = font_boton_med.render(TEXTOS[IDIOMA]["save_id_button"], True, color_boton_texto)
    screen.blit(guardar_id_text_surf, guardar_id_text_surf.get_rect(center=rect_boton_guardar_id.center))

    # "Activar"
    pygame.draw.rect(screen, color_boton_fondo, rect_boton_activar)
    pygame.draw.rect(screen, color_input_borde, rect_boton_activar, 1)
    activar_text_surf = font_texto.render(TEXTOS[IDIOMA]["activate_button"], True, color_boton_texto)
    screen.blit(activar_text_surf, activar_text_surf.get_rect(center=rect_boton_activar.center))

    # "Salir"
    pygame.draw.rect(screen, color_boton_fondo, rect_boton_salir_app)
    pygame.draw.rect(screen, color_input_borde, rect_boton_salir_app, 1)
    salir_text_surf = font_texto.render(TEXTOS[IDIOMA]["exit_button"], True, color_boton_texto)
    screen.blit(salir_text_surf, salir_text_surf.get_rect(center=rect_boton_salir_app.center))

    # "Obtener Licencia Online"
    pygame.draw.rect(screen, color_boton_fondo, rect_boton_obtener_licencia)
    pygame.draw.rect(screen, color_input_borde, rect_boton_obtener_licencia, 1)
    obtener_lic_text_surf = font_boton_med.render(TEXTOS[IDIOMA]["get_license_online_button"], True, color_boton_texto)
    screen.blit(obtener_lic_text_surf, obtener_lic_text_surf.get_rect(center=rect_boton_obtener_licencia.center))

    # Dibujar cursor si el input está activo y el cursor es visible
    if input_active and show_cursor:
        text_width = input_key_surf.get_width()
        cursor_x = rect_input_key.left + 5 + text_width
        # Asegurarse de que el cursor no se dibuje más allá del borde derecho del campo de entrada
        if cursor_x > rect_input_key.right - 3: # 3px de padding derecho para el cursor
            cursor_x = rect_input_key.right - 3
        
        pygame.draw.line(screen, color_texto, 
                         (cursor_x, rect_input_key.top + 5), 
                         (cursor_x, rect_input_key.bottom - 5), 1)
    
    pygame.display.flip()
    return rect_input_key, rect_boton_activar, rect_boton_salir_app, rect_boton_guardar_id, rect_boton_usar_archivo, rect_boton_copiar_id, rect_boton_obtener_licencia

# --- Función para manejar la ventana de activación ---
def run_activation_sequence(screen, current_internal_id, current_display_id):
    """
    Maneja la lógica y el bucle de eventos para la ventana de activación.
    Devuelve True si la activación fue exitosa, False en caso contrario.
    Actualiza las variables globales PROGRAM_MODE y ACTIVATED_SUCCESSFULLY.
    """
    global PROGRAM_MODE, ACTIVATED_SUCCESSFULLY, user_license_key_input # Necesitamos user_license_key_input si se mantiene entre llamadas
                                                                    # o se reinicia cada vez. Por ahora, reiniciemos.
    
    user_license_key_input = "" # Reiniciar para cada vez que se muestra la ventana
    activation_error_message = None
    id_saved_message = None 
    id_saved_message_timer = 0 
    activation_window_active = True
    input_key_active = False 

    cursor_visible = True
    cursor_blink_timer = 0


    while activation_window_active:
        current_time_millis = pygame.time.get_ticks()
        if id_saved_message and current_time_millis > id_saved_message_timer:
            id_saved_message = None 
        
        if current_time_millis - cursor_blink_timer > CURSOR_BLINK_INTERVAL:
            cursor_visible = not cursor_visible
            cursor_blink_timer = current_time_millis
        
        current_display_message = activation_error_message if activation_error_message else id_saved_message

        # Llamada a draw_activation_window
        # Asegurarse que los parámetros coinciden con la definición de draw_activation_window
        drawn_rects = draw_activation_window(
            screen, 
            current_display_id, # Renombrado para claridad, antes era display_id
            user_license_key_input, 
            current_display_message, 
            input_key_active, 
            cursor_visible
        )
        rect_input_key_field, rect_btn_activar, rect_btn_salir_app, \
        rect_boton_guardar_id, rect_boton_usar_archivo, rect_boton_copiar_id, rect_boton_obtener_licencia = drawn_rects
        
        for evento_activacion in pygame.event.get():
            if evento_activacion.type == pygame.QUIT:
                pygame.quit()
                sys.exit() 
            if evento_activacion.type == pygame.MOUSEBUTTONDOWN:
                if evento_activacion.button == 1:
                    if rect_btn_activar.collidepoint(evento_activacion.pos):
                        if verify_license_key(user_license_key_input, current_internal_id): # current_internal_id
                            store_license_data(user_license_key_input, current_internal_id) # current_internal_id
                            ACTIVATED_SUCCESSFULLY = True
                            PROGRAM_MODE = "LICENSED"
                            delete_trial_info()
                            activation_window_active = False 
                            print("Licencia activada exitosamente.")
                        else:
                            activation_error_message = "Clave de licencia inválida. Intente de nuevo."
                            user_license_key_input = "" 
                    elif rect_btn_salir_app.collidepoint(evento_activacion.pos):
                        activation_window_active = False 
                        # La lógica de si se inicia trial o no al salir, se manejará fuera,
                        # basado en el valor de retorno de esta función y el estado previo.
                    elif rect_boton_obtener_licencia.collidepoint(evento_activacion.pos):
                        input_key_active = False
                        activation_error_message = "Solicitando licencia en línea..."
                        id_saved_message = None
                        draw_activation_window(screen, current_display_id, user_license_key_input, activation_error_message, input_key_active, cursor_visible)
                        pygame.display.flip()

                        if verificar_y_obtener_licencia():
                            ACTIVATED_SUCCESSFULLY = True
                            PROGRAM_MODE = "LICENSED"
                            delete_trial_info()
                            activation_window_active = False
                            print("Licencia obtenida y activada exitosamente.")
                        else:
                            activation_error_message = "No se pudo obtener la licencia. Inténtelo más tarde o active manualmente."
                            id_saved_message_timer = pygame.time.get_ticks() + 3000

                    elif rect_boton_usar_archivo.collidepoint(evento_activacion.pos):
                        input_key_active = False; activation_error_message = None; id_saved_message = None
                        if TKINTER_AVAILABLE:
                            root = tk.Tk(); root.withdraw()
                            filepath = filedialog.askopenfilename(title="Seleccione el archivo de licencia (.json)", filetypes=(("JSON files", "*.json"), ("All files", "*.*")))
                            root.destroy()
                            if filepath:
                                try:
                                    with open(filepath, 'r') as f_import: data_importada = json.load(f_import)
                                    clave_importada = data_importada.get("license_key")
                                    id_maquina_importado = data_importada.get("machine_identifier")
                                    if clave_importada and id_maquina_importado:
                                        if id_maquina_importado == current_internal_id: # current_internal_id
                                            if verify_license_key(clave_importada, id_maquina_importado):
                                                store_license_data(clave_importada, id_maquina_importado)
                                                ACTIVATED_SUCCESSFULLY = True; PROGRAM_MODE = "LICENSED"; delete_trial_info()
                                                activation_window_active = False
                                            else: activation_error_message = "Clave en archivo de licencia es inválida."
                                        else: activation_error_message = "Licencia no corresponde a esta máquina."
                                    else: activation_error_message = "Archivo de licencia con formato incorrecto."
                                except Exception as e_import: activation_error_message = f"Error al procesar archivo: {e_import}"
                        else: activation_error_message = "Tkinter no disponible."
                        id_saved_message_timer = current_time_millis + 3000
                    
                    elif rect_boton_copiar_id.collidepoint(evento_activacion.pos):
                        input_key_active = False; activation_error_message = None
                        if PYPERCLIP_AVAILABLE:
                            try: pyperclip.copy(current_display_id); id_saved_message = "ID de Máquina copiado." # current_display_id
                            except Exception: id_saved_message = "Error al copiar ID."
                        else: id_saved_message = "Copiar ID no disponible."
                        id_saved_message_timer = current_time_millis + 3000
                    elif rect_boton_guardar_id.collidepoint(evento_activacion.pos):
                        input_key_active = False; activation_error_message = None
                        if save_id_to_file(current_display_id): id_saved_message = f"ID guardado en machine_id.txt" # current_display_id
                        else: id_saved_message = "Error al guardar ID."
                        id_saved_message_timer = current_time_millis + 3000
                    elif rect_input_key_field.collidepoint(evento_activacion.pos):
                        input_key_active = True; activation_error_message = None; id_saved_message = None
                    else:
                        input_key_active = False
            
            if evento_activacion.type == pygame.KEYDOWN and input_key_active:
                if evento_activacion.key == pygame.K_RETURN:
                    if verify_license_key(user_license_key_input, current_internal_id): # current_internal_id
                        store_license_data(user_license_key_input, current_internal_id) # current_internal_id
                        ACTIVATED_SUCCESSFULLY = True; PROGRAM_MODE = "LICENSED"; delete_trial_info()
                        activation_window_active = False
                    else:
                        activation_error_message = "Clave de licencia inválida."; user_license_key_input = ""
                elif evento_activacion.key == pygame.K_BACKSPACE: user_license_key_input = user_license_key_input[:-1]
                elif evento_activacion.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL or pygame.key.get_mods() & pygame.KMOD_META):
                    if PYPERCLIP_AVAILABLE:
                        try:
                                pasted_text = pyperclip.paste() # Punto y coma eliminado de aquí también para consistencia
                                remaining_len = 32 - len(user_license_key_input)
                                # No convertir a .upper() al pegar
                                user_license_key_input += pasted_text[:remaining_len] # Punto y coma eliminado
                                user_license_key_input = user_license_key_input[:32] # Asegurar longitud
                        except Exception: pass 
                elif evento_activacion.unicode.isalnum() and len(user_license_key_input) < 32: # Permitir solo alfanuméricos
                    user_license_key_input += evento_activacion.unicode # No convertir a .upper()
    
    return ACTIVATED_SUCCESSFULLY # Devuelve el estado de activación

# --- Función para formatear el tiempo restante del periodo de gracia ---
def format_remaining_grace_time(start_time_utc: datetime | None) -> str | None:

    if start_time_utc is None:
        return None

    try:
        # Asegurarse que start_time_utc es aware, si no lo es, asumirlo UTC (aunque debería serlo)
        if start_time_utc.tzinfo is None or start_time_utc.tzinfo.utcoffset(start_time_utc) is None:
            # Esto es un fallback, idealmente start_time_utc siempre es aware.
            start_time_utc = start_time_utc.replace(tzinfo=timezone.utc)

        end_time_utc = start_time_utc + timedelta(days=1)
        now_utc = datetime.now(timezone.utc)
        remaining_delta = end_time_utc - now_utc

        if remaining_delta.total_seconds() <= 0:
            return None # O podría ser "Expirado"

        total_seconds = int(remaining_delta.total_seconds())
        
        days = total_seconds // (24 * 3600)
        total_seconds %= (24 * 3600)
        
        hours = total_seconds // 3600
        total_seconds %= 3600
        
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        if days > 0:
            return f"{days}d {hours:02}h {minutes:02}m" # No mostrar segundos si hay días
        else:
            return f"{hours:02}h {minutes:02}m {seconds:02}s"

    except Exception as e:
        print(f"Error al formatear tiempo restante de gracia: {e}")
        return None


def reset_simulation_state():
    """Inicializa o resetea los parámetros de la simulación circular."""
    global sim_initialized, sim_center_lat, sim_center_lon, sim_angle_on_circle_deg
    global ts_lat_decimal, ts_lon_decimal, ts_heading_float, ts_speed_float, ts_altitude_float, ts_pitch_float, ts_roll_float
    
    start_lat_deg, start_lon_deg, initial_heading_deg = -12.0, -77.716667, 10.0
    
    bearing_to_center_rad = math.radians((initial_heading_deg + 90) % 360)
    R, start_lat_rad = 6378137, math.radians(start_lat_deg)
    
    d_lat = sim_radius_meters * math.cos(bearing_to_center_rad)
    d_lon = sim_radius_meters * math.sin(bearing_to_center_rad)
    
    sim_center_lat = start_lat_deg + (d_lat / R) * (180 / math.pi)
    sim_center_lon = start_lon_deg + (d_lon / (R * math.cos(start_lat_rad))) * (180 / math.pi)
    
    sim_angle_on_circle_deg = (math.degrees(bearing_to_center_rad) + 180) % 360
    
    ts_lat_decimal, ts_lon_decimal, ts_heading_float, ts_speed_float, ts_altitude_float, ts_pitch_float, ts_roll_float = \
        start_lat_deg, start_lon_deg, initial_heading_deg, 12.0, 10.0, 0.0, 0.0
    
    sim_initialized = True

def generar_datos_simulados(dt_seconds):
    """Genera y actualiza las variables de datos con valores de la simulación circular."""
    global ts_pitch_float, att_pitch_str, ts_roll_float, att_roll_str, ts_lat_decimal, latitude_str, ts_lon_decimal, longitude_str
    global ts_speed_float, speed_str, ts_heading_float, heading_str, ts_altitude_float, altitude_str, ultima_vez_datos_recibidos, ts_timestamp_str
    global sim_initialized, sim_angle_on_circle_deg

    if not sim_initialized:
        reset_simulation_state()

    current_speed_kts = 12.0 + random.uniform(-2.0, 2.0)
    distancia_recorrida_m = (current_speed_kts * 0.514444) * dt_seconds
    angular_change_deg = math.degrees(distancia_recorrida_m / sim_radius_meters)
    sim_angle_on_circle_deg = (sim_angle_on_circle_deg + angular_change_deg) % 360

    R, center_lat_rad = 6378137, math.radians(sim_center_lat)
    bearing_rad = math.radians(sim_angle_on_circle_deg)
    
    d_lat_m = sim_radius_meters * math.cos(bearing_rad)
    d_lon_m = sim_radius_meters * math.sin(bearing_rad)

    ts_lat_decimal = sim_center_lat + (d_lat_m / R) * (180 / math.pi)
    ts_lon_decimal = sim_center_lon + (d_lon_m / (R * math.cos(center_lat_rad))) * (180 / math.pi)
    
    latitude_str = f"{abs(ts_lat_decimal):.4f}° {'N' if ts_lat_decimal >= 0 else 'S'}"
    longitude_str = f"{abs(ts_lon_decimal):.4f}° {'E' if ts_lon_decimal >= 0 else 'W'}"

    ts_heading_float = (sim_angle_on_circle_deg + 90) % 360
    heading_str = f"{ts_heading_float:.0f}°"

    ts_speed_float = current_speed_kts
    speed_str = f"{ts_speed_float:.1f} Kt"
    
    ts_altitude_float = 10.0 + random.uniform(-1.5, 1.5)
    altitude_str = f"{ts_altitude_float:.1f} M"

    ts_pitch_float = random.uniform(-5.0, 5.0)
    att_pitch_str = f"{ts_pitch_float:.1f}"

    ts_roll_float = random.uniform(-8.0, 8.0)
    att_roll_str = f"{ts_roll_float:.1f}"
    
    ts_timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    ultima_vez_datos_recibidos = pygame.time.get_ticks()

def main():
    global IDIOMA, sonido_alarma_actualmente_reproduciendo, tiempo_ultimo_sonido_iniciado, INDICE_PROXIMA_ALARMA_A_SONAR
    global ultima_reproduccion_alarma_babor_tiempo, ultima_reproduccion_alarma_estribor_tiempo, ultima_reproduccion_alarma_sentado_tiempo, ultima_reproduccion_alarma_encabuzado_tiempo
    global ultima_vez_envio_datos, ultimo_intento_reconeccion_tiempo, network_available, last_network_check_time
    global latitude_str, longitude_str, speed_str, heading_str, att_heading_str, att_pitch_str, att_roll_str, altitude_str
    global ts_pitch_float, ts_roll_float, ts_lat_decimal, ts_lon_decimal, ts_speed_float, ts_heading_float, ts_timestamp_str, ts_altitude_float
    global datos_consola_buffer, MAX_LINEAS_CONSOLA, simulador_activado, sim_data_index
    global alarma_roll_babor_activa, alarma_roll_estribor_activa, alarma_pitch_sentado_activa, alarma_pitch_encabuzado_activa
    global ser, serial_port_available, ultima_vez_datos_recibidos, nmea_data_stale
    global SERVICIO_DATOS_ACTUAL, API_KEY_THINGSPEAK, API_KEY_GOOGLE_CLOUD, input_api_key_thingspeak_str, input_api_key_google_cloud_str, input_password_azure_str
    global mostrar_ventana_config_serial, mostrar_ventana_alarma, mostrar_ventana_idioma, mostrar_ventana_acerca_de
    global mostrar_ventana_servicio_datos, mostrar_ventana_password_servicio, mostrar_ventana_consola_datos, mostrar_ventana_test_serial
    global datos_test_serial_buffer
    global input_puerto_str, input_baudios_idx, puerto_dropdown_activo, baudios_dropdown_activo
    global input_alarma_activo, input_password_str, intento_password_fallido, input_password_activo, input_servicio_activo
    
    pygame.init() # Asegurar que Pygame esté inicializado
    dimensiones = [1100, 600] # Ancho aumentado para cajas de datos
    screen = pygame.display.set_mode(dimensiones) # Crear la pantalla
    pygame.display.set_caption("Clinómetro") # Título genérico inicial

    # Cargar configuraciones (después de la lógica de licencia/trial y antes de usar IDIOMA)
    puerto, baudios = cargar_configuracion_serial() # Carga IDIOMA también
    cargar_configuracion_alarma()
    
    # Inicializar variables de datos
    reset_ui_data()
    init_csv()
    init_alarm_csv() # Inicializar CSV de alarmas
    
    # Configurar título de ventana con idioma correcto
    pygame.display.set_caption(TEXTOS[IDIOMA]["titulo_ventana"])
    
    # Configuración de áreas de visualización
    ALTURA_BARRA_HERRAMIENTAS = 30
    nuevo_ancho_area_izquierda = 790 # Aumentado para centrar
    area_izquierda_rect = pygame.Rect(10, ALTURA_BARRA_HERRAMIENTAS + 10, nuevo_ancho_area_izquierda, dimensiones[1] - (ALTURA_BARRA_HERRAMIENTAS + 20))
    
    # Configuración de círculos para pitch y roll
    radio_circulo_img = 180 # Corregido a 180 (original era 156)
    margen_superior_circulos = 20
    # Ajustar centro_y para el nuevo radio y centrarlo verticalmente
    centro_y_circulos = area_izquierda_rect.top + radio_circulo_img + margen_superior_circulos
    
    # Ajustar centros en x para que quepan y estén bien espaciados
    espacio_entre_circulos = 40
    # Calcular el ancho total de los círculos para centrarlos en el area_izquierda_rect
    ancho_total_contenido = (2 * radio_circulo_img * 2) + espacio_entre_circulos
    offset_x_inicial = (area_izquierda_rect.width - ancho_total_contenido) / 2
    centro_x_circulo1 = area_izquierda_rect.left + offset_x_inicial + radio_circulo_img
    centro_x_circulo2 = centro_x_circulo1 + (2 * radio_circulo_img) + espacio_entre_circulos
    
    # Configuración de marcas de grados
    LONGITUD_MARCA_GRADO = 16
    GROSOR_MARCA_GRADO = 3
    COLOR_MARCA_GRADO = BLANCO
    COLOR_ETIQUETA_GRADO = BLANCO
    RADIO_INICIO_MARCAS = radio_circulo_img
    RADIO_FIN_MARCAS = radio_circulo_img + LONGITUD_MARCA_GRADO
    OFFSET_TEXTO_ETIQUETA = 20
    RADIO_POSICION_TEXTO_ETIQUETA = RADIO_FIN_MARCAS + OFFSET_TEXTO_ETIQUETA
    
    ANGULOS_MARCAS_ETIQUETAS_DEF = {
        "0_der": (0, "0"), 
        "0_izq": (180, "0"), 
        "sup_mas_30": (-120, "+30"), 
        "sup_menos_30": (-60, "-30")
    }
    
    # Configuración de flechas
    LONGITUD_FLECHA_DIR = 20
    ANCHO_FLECHA_DIR = 12
    OFFSET_FLECHA_TEXTO = 10
    OFFSET_LETRA_ROLL_Y = 10
    COLOR_LETRA_ROLL = BLANCO
    
    # Cargar imágenes de fondo
    try:
        imagen_fondo_original = pygame.image.load(resource_path("mar.jpg"))
        imagen_fondo_escalada = pygame.transform.scale(imagen_fondo_original, dimensiones)
        imagen_fondo_escalada = imagen_fondo_escalada.convert()
    except:
        imagen_fondo_escalada = None
    
    # Cargar imágenes de pitch y roll
    pitch_image_base_grande = None
    try:
        pitch_image_surface_original_temp = pygame.image.load(resource_path("pitch.png"))
        lado_pitch_deseado_grande = int((2 * radio_circulo_img) + 2)
        pitch_image_base_grande = pygame.transform.smoothscale(pitch_image_surface_original_temp, (lado_pitch_deseado_grande, lado_pitch_deseado_grande)).convert_alpha()
    except:
        pitch_image_base_grande = None
    
    roll_image_base_grande = None
    try:
        roll_image_surface_original_temp = pygame.image.load(resource_path("roll.png"))
        lado_img_deseado_grande = int((2 * radio_circulo_img) + 2)
        roll_image_base_grande = pygame.transform.smoothscale(roll_image_surface_original_temp, (lado_img_deseado_grande, lado_img_deseado_grande)).convert_alpha()
    except:
        roll_image_base_grande = None
    
    # Configuración de fuentes
    font = pygame.font.Font(None, 24)
    font_bar_herramientas = pygame.font.Font(None, 22)
    font_datos_grandes = pygame.font.Font(None, 50)
    font_circulos_textos = pygame.font.Font(None, 72)
    
    # Configuración de reloj
    reloj = pygame.time.Clock()
    
    # Configuración de la barra de herramientas
    rect_barra_herramientas = pygame.Rect(0, 0, dimensiones[0], ALTURA_BARRA_HERRAMIENTAS)
    rects_opciones_menu_barra = []
    padding_menu_x = 15
    espacio_entre_menus = 10
    
    # Configuración de ventanas
    mostrar_ventana_config_serial = False
    mostrar_ventana_acerca_de = False
    mostrar_ventana_alarma = False
    mostrar_ventana_idioma = False
    
    # Configuración de colores para la interfaz
    COLOR_VENTANA_FONDO = (144, 238, 144)
    COLOR_TEXTO_NORMAL = NEGRO
    COLOR_BORDE_VENTANA = (170, 170, 170)
    COLOR_BORDE_VENTANA_CLARO = (220, 220, 220)
    COLOR_BORDE_VENTANA_OSCURO = (100, 100, 100)
    COLOR_BARRA_HERRAMIENTAS_FONDO = (220, 220, 220)
    COLOR_BARRA_HERRAMIENTAS_BORDE = (180, 180, 180)
    COLOR_ITEM_MENU_TEXTO = NEGRO
    COLOR_BOTON_FONDO = (225, 225, 225)
    COLOR_BOTON_BORDE = (150, 150, 150)
    COLOR_BOTON_FONDO_3D = (210, 210, 210)
    COLOR_BOTON_BORDE_CLARO_3D = (230, 230, 230)
    COLOR_BOTON_BORDE_OSCURO_3D = (130, 130, 130)
    COLOR_INPUT_FONDO = BLANCO
    COLOR_INPUT_BORDE = (120, 120, 120)
    COLOR_INPUT_BORDE_CLARO_3D = (200, 200, 200)
    COLOR_INPUT_BORDE_OSCURO_3D = (80, 80, 80)
    COLOR_DROPDOWN_FONDO = (250, 250, 250)
    COLOR_DROPDOWN_BORDE = (100, 100, 100)
    COLOR_SELECCION_DROPDOWN = (200, 220, 255)
    COLOR_CAJA_DATOS_FONDO = NEGRO  # Cambiado a NEGRO
    COLOR_CAJA_DATOS_BORDE = (120, 120, 120) # Se mantiene el borde gris, o se puede cambiar si se desea
    COLOR_CAJA_DATOS_TEXTO = ROJO   # Cambiado a ROJO
    
    # Configuración del puerto serial
    ser = None
    serial_port_available = True
    try:
        ser = serial.Serial(puerto, baudios, timeout=1)
        print(f"Puerto serial {puerto} abierto con {baudios} baudios.")
    except serial.SerialException as e:
        print(f"Error opening serial port {puerto} with {baudios} baud: {e}")
        serial_port_available = False
    except Exception as e:
        print(f"An unexpected error occurred opening serial port: {e}")
        serial_port_available = False
    
    # Variables para la ventana de configuración
    ventana_config_width = 300
    ventana_config_height = 400
    ventana_config_x = (dimensiones[0] - ventana_config_width) // 2
    ventana_config_y = (dimensiones[1] - ventana_config_height) // 2
    rect_ventana_config = pygame.Rect(ventana_config_x, ventana_config_y, ventana_config_width, ventana_config_height)
    
    input_puerto_str = str(puerto)
    lista_baudios_seleccionables = sorted([4800, 9600, 19200, 38400, 57600, 115200])
    try:
        input_baudios_idx = lista_baudios_seleccionables.index(baudios)
    except ValueError:
        input_baudios_idx = 0
    
    input_elements_top_offset_config = 50
    input_elements_height_config = 30
    label_width_config = 70
    padding_interno_config = 10
    input_width_config = ventana_config_width - label_width_config - padding_interno_config * 3
    
    rect_input_puerto_config = pygame.Rect(
        rect_ventana_config.left + padding_interno_config + label_width_config + padding_interno_config,
        rect_ventana_config.top + input_elements_top_offset_config,
        input_width_config, input_elements_height_config
    )
    
    y_pos_baudios = rect_input_puerto_config.bottom + 15 + 50
    rect_input_baudios_display_config = pygame.Rect(
        rect_ventana_config.left + padding_interno_config + label_width_config + padding_interno_config,
        y_pos_baudios,
        input_width_config, input_elements_height_config
    )
    
    button_config_width = (ventana_config_width - 60) // 2 # Ancho para dos botones con espacio
    button_config_height = 40
    y_botones_config = rect_ventana_config.bottom - button_config_height - 20
    
    rect_boton_test_config = pygame.Rect(
        rect_ventana_config.left + 20,
        y_botones_config,
        button_config_width, button_config_height
    )
    
    rect_boton_guardar_config = pygame.Rect(
        rect_boton_test_config.right + 20,
        y_botones_config,
        button_config_width, button_config_height
    )
    
    rect_boton_cerrar_config = pygame.Rect(
        rect_ventana_config.right - 35,
        rect_ventana_config.top + 5,
        30, 30
    )
    
    # Variables para la ventana de alarma
    rect_ventana_alarma = pygame.Rect(250, 100, 380, 230)
    input_alarma_activo = None
    
    # Variables para la ventana de idioma
    rect_ventana_idioma = pygame.Rect(0, 0, 250, 170)
    rect_boton_es = None
    rect_boton_en = None

    # Variables para la ventana de servicio de datos
    mostrar_ventana_servicio_datos = False
    ventana_servicio_width = 400
    ventana_servicio_height = 370 # Aumentada para el campo de contraseña
    ventana_servicio_x = (dimensiones[0] - ventana_servicio_width) // 2
    ventana_servicio_y = (dimensiones[1] - ventana_servicio_height) // 2
    rect_ventana_servicio_datos = pygame.Rect(ventana_servicio_x, ventana_servicio_y, ventana_servicio_width, ventana_servicio_height)
    input_servicio_activo = None # Para saber qué API key se está editando: "thingspeak" o "google"
    rect_radio_thingspeak = None
    rect_radio_google_cloud = None
    rect_input_apikey_thingspeak = None
    rect_input_apikey_google_cloud = None
    rect_boton_guardar_servicio = None
    rect_boton_mostrar_consola_servicio = None # Nuevo botón
    rect_boton_cerrar_servicio = None
    RADIO_BUTTON_SIZE = 10 # Radio del círculo del radio button

    # Variables para la ventana de contraseña del servicio de datos (dimensiones y rects)
    ventana_password_width = 300
    ventana_password_height = 200
    ventana_password_x = (dimensiones[0] - ventana_password_width) // 2
    ventana_password_y = (dimensiones[1] - ventana_password_height) // 2
    rect_ventana_password_servicio = pygame.Rect(ventana_password_x, ventana_password_y, ventana_password_width, ventana_password_height)
    rect_input_password = None
    rect_boton_entrar_password = None
    rect_boton_cerrar_password_servicio = None # Para el botón 'X' de esta ventana
    input_password_activo = False # Para saber si el campo de contraseña está activo

    # Variables para la ventana de consola de datos
    mostrar_ventana_consola_datos = False # Controla la visibilidad
    rect_ventana_consola_datos = None # Se definirá en el bucle si es visible
    rect_boton_cerrar_consola_datos = None # Botón 'X' para cerrar
    rect_boton_copiar_consola = None # Botón 'Copiar'
    datos_consola_buffer = [] # Buffer para almacenar mensajes de la consola
    MAX_LINEAS_CONSOLA = 100 # Número máximo de líneas a mantener en el buffer
    copy_success_message = None
    copy_message_timer = 0

    # Variables para el cursor parpadeante
    cursor_visible = True
    cursor_blink_timer = 0
    
    # Bucle principal
    global running, window_visible
    running = True
    
    # Lógica de visibilidad para la primera ejecución
    is_first_run = not os.path.exists(FIRST_RUN_FILE)
    if is_first_run:
        window_visible = True
        try:
            with open(FIRST_RUN_FILE, 'w') as f:
                json.dump({"first_run_completed": True}, f)
        except IOError as e:
            print(f"WARN: No se pudo escribir el archivo de primera ejecución: {e}")
    else:
        window_visible = False
        
    nmea_data_stale = False

    tray_thread = threading.Thread(target=setup_tray_icon)
    tray_thread.daemon = True
    tray_thread.start()
    
    while running:
        if window_visible:
            try:
                screen.get_height()
            except pygame.error:
                # Re-initialize the display
                dimensiones = [1100, 600]
                screen = pygame.display.set_mode(dimensiones)
                pygame.display.set_caption(TEXTOS[IDIOMA]["titulo_ventana"])
        else:
            pygame.display.quit()
            # Core logic loop
            while not window_visible and running:
                # Lógica de reconexión del puerto serie
                if not serial_port_available:
                    ahora = pygame.time.get_ticks()
                    if ahora - ultimo_intento_reconeccion_tiempo > INTERVALO_RECONECCION_MS:
                        ultimo_intento_reconeccion_tiempo = ahora
                        print(f"INFO (oculto): Intentando reconectar al puerto {puerto}...")
                        try:
                            if ser is not None:
                                ser.close()
                            ser = serial.Serial(puerto, baudios, timeout=1)
                            serial_port_available = True
                            nmea_data_stale = False
                            ultima_vez_datos_recibidos = pygame.time.get_ticks()
                            print(f"INFO (oculto): Reconexión exitosa al puerto {puerto}.")
                            agregar_a_consola(f"Reconectado a {puerto}.")
                        except serial.SerialException:
                            ser = None
                            serial_port_available = False
                        except Exception as e:
                            print(f"Error inesperado durante reconexión (oculto): {e}")
                            ser = None
                            serial_port_available = False
                    time.sleep(1)

                # Procesar datos del puerto serie
                procesar_datos_serie()
                
                # Lógica de verificación de red
                if not network_available:
                    now = time.time()
                    if now - last_network_check_time > 60:
                        print("INFO (oculto): Verificando estado de la red...")
                        network_check_thread = threading.Thread(target=check_network_connection)
                        network_check_thread.daemon = True
                        network_check_thread.start()
                        last_network_check_time = now

                # Lógica de envío y guardado de datos
                enviar_y_guardar_datos_periodicamente()
                
                pygame.time.delay(100)
            continue

        mouse_pos = pygame.mouse.get_pos()
        
        # Verificar si el mouse está sobre la barra de herramientas
        toolbar_visible = rect_barra_herramientas.collidepoint(mouse_pos)
        
        # Definir opciones del menú dinámicamente
        opciones_menu_barra = []
        opciones_menu_barra.append(TEXTOS[IDIOMA]["menu_config"])
        opciones_menu_barra.append(TEXTOS[IDIOMA]["menu_alarma"])
        opciones_menu_barra.append(TEXTOS[IDIOMA]["menu_idioma"])
        opciones_menu_barra.append(TEXTOS[IDIOMA]["menu_servicio_datos"])
        
        opciones_menu_barra.append(TEXTOS[IDIOMA]["menu_acerca"])
        
        # Manejo del parpadeo del cursor
        current_time_millis = pygame.time.get_ticks()
        if current_time_millis - cursor_blink_timer > CURSOR_BLINK_INTERVAL:
            cursor_visible = not cursor_visible
            cursor_blink_timer = current_time_millis
        
        if copy_success_message and current_time_millis > copy_message_timer:
            copy_success_message = None

        # Manejo de eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                window_visible = False
            
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:  # Clic izquierdo
                    # Manejo de clic en la barra de herramientas
                    if toolbar_visible and not mostrar_ventana_config_serial and not mostrar_ventana_acerca_de and not mostrar_ventana_alarma and not mostrar_ventana_idioma:
                        for i, rect_opcion in enumerate(rects_opciones_menu_barra):
                            if rect_opcion.collidepoint(evento.pos):
                                opcion_clicada_texto = opciones_menu_barra[i] # Obtener el texto de la opción

                                if opcion_clicada_texto == TEXTOS[IDIOMA]["menu_config"]:
                                    mostrar_ventana_config_serial = True
                                    input_puerto_str = str(puerto)
                                    try: input_baudios_idx = lista_baudios_seleccionables.index(int(baudios))
                                    except ValueError: input_baudios_idx = 0
                                    lista_puertos_detectados.clear()
                                    try:
                                        ports = comports()
                                        if ports: lista_puertos_detectados.extend(p.device for p in ports)
                                        else: lista_puertos_detectados.append("N/A")
                                    except Exception: lista_puertos_detectados.append("Error")
                                    
                                elif opcion_clicada_texto == TEXTOS[IDIOMA]["menu_alarma"]:
                                    mostrar_ventana_alarma = True
                                    input_alarma_activo = None
                                    try: valores_ui_input_alarma["pitch"] = str(abs(int(float(valores_alarma["max_pitch_pos"]))))
                                    except: valores_ui_input_alarma["pitch"] = "15"
                                    try: valores_ui_input_alarma["roll"] = str(abs(int(float(valores_alarma["max_roll_pos"]))))
                                    except: valores_ui_input_alarma["roll"] = "15"
                                
                                elif opcion_clicada_texto == TEXTOS[IDIOMA]["menu_idioma"]:
                                    mostrar_ventana_idioma = True
                                    rect_ventana_idioma.center = screen.get_rect().center
                                
                                elif opcion_clicada_texto == TEXTOS[IDIOMA]["menu_servicio_datos"]:
                                    mostrar_ventana_password_servicio = True
                                    input_password_str = ""; intento_password_fallido = False; input_servicio_activo = None
                                
                                elif opcion_clicada_texto == TEXTOS[IDIOMA]["menu_acerca"]:
                                    mostrar_ventana_acerca_de = True
                                break
                    
                    # Manejo de clic en ventana de servicio de datos
                    elif mostrar_ventana_servicio_datos:
                        if globals().get('rect_boton_cerrar_servicio') and globals().get('rect_boton_cerrar_servicio').collidepoint(evento.pos):
                            mostrar_ventana_servicio_datos = False
                            input_servicio_activo = None
                        elif globals().get('rect_radio_thingspeak') and globals().get('rect_radio_thingspeak').collidepoint(evento.pos):
                            SERVICIO_DATOS_ACTUAL = "thingspeak"
                        elif globals().get('rect_radio_google_cloud') and globals().get('rect_radio_google_cloud').collidepoint(evento.pos):
                            SERVICIO_DATOS_ACTUAL = "azure_sql"
                        elif globals().get('rect_input_apikey_thingspeak') and globals().get('rect_input_apikey_thingspeak').collidepoint(evento.pos):
                            input_servicio_activo = "thingspeak"
                        elif globals().get('rect_input_apikey_google_cloud') and globals().get('rect_input_apikey_google_cloud').collidepoint(evento.pos):
                            input_servicio_activo = "google_cloud"
                        elif globals().get('rect_input_password_azure') and globals().get('rect_input_password_azure').collidepoint(evento.pos):
                            input_servicio_activo = "password_azure"
                        elif globals().get('rect_boton_guardar_servicio') and globals().get('rect_boton_guardar_servicio').collidepoint(evento.pos):
                            # Guardar los valores de los inputs en las variables globales principales
                            API_KEY_THINGSPEAK = input_api_key_thingspeak_str
                            API_KEY_GOOGLE_CLOUD = input_api_key_google_cloud_str
                            guardar_configuracion_serial(puerto, baudios) # Guarda todas las configs incluido el servicio y keys
                            mostrar_ventana_servicio_datos = False
                            input_servicio_activo = None
                        elif globals().get('rect_boton_mostrar_consola_servicio') and globals().get('rect_boton_mostrar_consola_servicio').collidepoint(evento.pos):
                            print("Botón 'Mostrar Consola' presionado.")
                            mostrar_ventana_consola_datos = True # Mostrar la ventana de la consola
                            mostrar_ventana_servicio_datos = False # Ocultar la ventana de servicio de datos
                            input_servicio_activo = None # Asegurarse de resetear el input activo de la ventana de servicio
                        else:
                            input_servicio_activo = None # Clic fuera de elementos interactivos

                    # Manejo de clic en ventana de idioma
                    elif mostrar_ventana_consola_datos: # Si la ventana de consola está visible
                        if globals().get('rect_boton_cerrar_consola_datos') and globals().get('rect_boton_cerrar_consola_datos').collidepoint(evento.pos):
                            mostrar_ventana_consola_datos = False # Ocultar la ventana
                        elif globals().get('rect_boton_copiar_consola') and globals().get('rect_boton_copiar_consola').collidepoint(evento.pos):
                            if PYPERCLIP_AVAILABLE:
                                try:
                                    datos_a_copiar = "\n".join(datos_consola_buffer)
                                    pyperclip.copy(datos_a_copiar)
                                    copy_success_message = "Copiado!"
                                    copy_message_timer = pygame.time.get_ticks() + 2000 # Mostrar por 2 segundos
                                except Exception as e:
                                    copy_success_message = "Error al copiar."
                                    copy_message_timer = pygame.time.get_ticks() + 2000
                            else:
                                copy_success_message = "Pyperclip no disponible."
                                copy_message_timer = pygame.time.get_ticks() + 2000
                        # Aquí se podrían manejar otros clics dentro de la consola si fuera necesario (e.g., scrollbar)
                    elif mostrar_ventana_idioma:
                        if rect_boton_es and rect_boton_es.collidepoint(evento.pos):
                            IDIOMA = "es"
                            guardar_configuracion_serial(puerto, baudios) # Guardar idioma
                            mostrar_ventana_idioma = False
                        elif rect_boton_en and rect_boton_en.collidepoint(evento.pos):
                            IDIOMA = "en"
                            guardar_configuracion_serial(puerto, baudios) # Guardar idioma
                            mostrar_ventana_idioma = False
                        elif not rect_ventana_idioma.collidepoint(evento.pos): # Clic fuera de la ventana de idioma
                            mostrar_ventana_idioma = False
                    
                  

                    # Manejo de clic en la ventana de Contraseña para Servicio de Datos
                    elif mostrar_ventana_password_servicio:
                        if globals().get('rect_boton_cerrar_password_servicio') and globals().get('rect_boton_cerrar_password_servicio').collidepoint(evento.pos):
                            mostrar_ventana_password_servicio = False
                            input_password_str = ""
                            intento_password_fallido = False
                            input_password_activo = False
                        elif globals().get('rect_input_password') and globals().get('rect_input_password').collidepoint(evento.pos):
                            input_password_activo = True
                        elif globals().get('rect_boton_entrar_password') and globals().get('rect_boton_entrar_password').collidepoint(evento.pos):
                            if input_password_str == CLAVE_ACCESO_SERVICIO:
                                mostrar_ventana_password_servicio = False
                                mostrar_ventana_servicio_datos = True # Abrir ventana de servicio
                                input_password_str = ""
                                intento_password_fallido = False
                                input_password_activo = False
                                # Cargar claves actuales a los inputs de la ventana de servicio
                                input_api_key_thingspeak_str = API_KEY_THINGSPEAK
                                input_api_key_google_cloud_str = API_KEY_GOOGLE_CLOUD
                                input_password_azure_str = AZURE_SQL_PASSWORD
                            else:
                                input_password_str = ""
                                intento_password_fallido = True
                                input_password_activo = False # Desactivar input para que se pueda ver el mensaje
                        else:
                            input_password_activo = False # Clic fuera de elementos interactivos
                    
                    # Manejo de clic en ventana de configuración serial
                    elif mostrar_ventana_config_serial:
                        # Esta variable debe definirse antes de usarse en el evento de clic
                        puerto_dropdown_activo = globals().get('puerto_dropdown_activo', False)
                        baudios_dropdown_activo = globals().get('baudios_dropdown_activo', False)
                        lista_rects_items_puerto = globals().get('lista_rects_items_puerto', [])
                        lista_rects_items_baudios = globals().get('lista_rects_items_baudios', [])


                        if puerto_dropdown_activo:
                            clic_en_item_puerto = False
                            for i, item_rect in enumerate(lista_rects_items_puerto):
                                if item_rect.collidepoint(evento.pos):
                                    input_puerto_str = lista_puertos_detectados[i]
                                    puerto_dropdown_activo = False
                                    globals()['puerto_dropdown_activo'] = False # Actualizar global
                                    clic_en_item_puerto = True
                                    break
                            if not clic_en_item_puerto and not rect_input_puerto_config.collidepoint(evento.pos):
                                puerto_dropdown_activo = False
                                globals()['puerto_dropdown_activo'] = False
                        
                        elif rect_input_puerto_config.collidepoint(evento.pos):
                            puerto_dropdown_activo = not puerto_dropdown_activo
                            globals()['puerto_dropdown_activo'] = puerto_dropdown_activo
                            if puerto_dropdown_activo:
                                baudios_dropdown_activo = False
                                globals()['baudios_dropdown_activo'] = False
                        
                        elif baudios_dropdown_activo:
                            clic_en_item_baudios = False
                            for i, item_rect in enumerate(lista_rects_items_baudios):
                                if item_rect.collidepoint(evento.pos):
                                    input_baudios_idx = i
                                    baudios_dropdown_activo = False
                                    globals()['baudios_dropdown_activo'] = False
                                    clic_en_item_baudios = True
                                    break
                            if not clic_en_item_baudios and not rect_input_baudios_display_config.collidepoint(evento.pos):
                                baudios_dropdown_activo = False
                                globals()['baudios_dropdown_activo'] = False
                        
                        elif rect_input_baudios_display_config.collidepoint(evento.pos):
                            baudios_dropdown_activo = not baudios_dropdown_activo
                            globals()['baudios_dropdown_activo'] = baudios_dropdown_activo
                            if baudios_dropdown_activo:
                                puerto_dropdown_activo = False
                                globals()['puerto_dropdown_activo'] = False
                        
                        elif rect_boton_cerrar_config.collidepoint(evento.pos):
                            mostrar_ventana_config_serial = False
                            puerto_dropdown_activo = False; globals()['puerto_dropdown_activo'] = False
                            baudios_dropdown_activo = False; globals()['baudios_dropdown_activo'] = False
                        
                        elif rect_boton_test_config.collidepoint(evento.pos):
                            mostrar_ventana_config_serial = False # Ocultar ventana de config
                            mostrar_ventana_test_serial = True
                            datos_test_serial_buffer.clear() # Limpiar buffer al abrir

                        elif rect_boton_guardar_config.collidepoint(evento.pos):
                            nuevos_baudios = lista_baudios_seleccionables[input_baudios_idx]
                            guardado_exitoso = guardar_configuracion_serial(input_puerto_str, nuevos_baudios)
                            if guardado_exitoso:
                                puerto = input_puerto_str
                                baudios = nuevos_baudios
                                if ser and ser.is_open:
                                    ser.close()
                                try:
                                    ser = serial.Serial(puerto, baudios, timeout=2) # Timeout aumentado
                                    serial_port_available = True
                                except serial.SerialException as e:
                                    print(f"Error reabriendo puerto serial {puerto} con {baudios} baud: {e}")
                                    serial_port_available = False
                                except Exception as e: # Captura de error más genérica
                                    print(f"Error inesperado reabriendo puerto: {e}")
                                    serial_port_available = False
                                
                                mostrar_ventana_config_serial = False
                                puerto_dropdown_activo = False; globals()['puerto_dropdown_activo'] = False
                                baudios_dropdown_activo = False; globals()['baudios_dropdown_activo'] = False
                        
                        else: # Clic fuera de los elementos interactivos de la config window
                            puerto_dropdown_activo = False; globals()['puerto_dropdown_activo'] = False
                            baudios_dropdown_activo = False; globals()['baudios_dropdown_activo'] = False
                    
                    # Manejo de clic en ventana de alarma
                    elif mostrar_ventana_alarma:
                      
                        if 'rect_boton_salir_alarma' in locals() and rect_boton_salir_alarma.collidepoint(evento.pos):
                            mostrar_ventana_alarma = False
                            input_alarma_activo = None
                        
                        elif 'rect_boton_guardar_alarma' in locals() and rect_boton_guardar_alarma.collidepoint(evento.pos):
                            try:
                                pitch_ui_val_str = valores_ui_input_alarma["pitch"]
                                roll_ui_val_str = valores_ui_input_alarma["roll"]
                                # Usar 15 como default si el string está vacío
                                pitch_val_to_save = int(pitch_ui_val_str) if pitch_ui_val_str else 15
                                roll_val_to_save = int(roll_ui_val_str) if roll_ui_val_str else 15
                                
                                # Actualizar el diccionario de UI con el valor que se va a guardar (validado o default)
                                valores_ui_input_alarma["pitch"] = str(pitch_val_to_save)
                                valores_ui_input_alarma["roll"] = str(roll_val_to_save)
                                
                                if guardar_configuracion_alarma(): # guardar_config_alarma ahora usa valores_ui_input_alarma
                                    mostrar_ventana_alarma = False
                                    input_alarma_activo = None
                            except ValueError: # Si la conversión a int falla (e.g. string no numérico)
                                print("DEBUG: Error de valor en inputs de alarma. No numérico.")
                        
                        elif 'rect_input_pitch_alarma' in locals() and rect_input_pitch_alarma.collidepoint(evento.pos):
                            input_alarma_activo = "pitch"
                        
                        elif 'rect_input_roll_alarma' in locals() and rect_input_roll_alarma.collidepoint(evento.pos):
                            input_alarma_activo = "roll"
                        
                        else: # Clic fuera de los elementos interactivos de la ventana de alarma
                            input_alarma_activo = None
                    
                    # Manejo de clic en ventana Acerca de
                    elif mostrar_ventana_acerca_de:
                        if 'rect_boton_cerrar_acerca_de' in locals() and rect_boton_cerrar_acerca_de.collidepoint(evento.pos):
                            mostrar_ventana_acerca_de = False
                    
                    elif mostrar_ventana_test_serial:
                        if 'rect_boton_cerrar_test_serial' in globals() and rect_boton_cerrar_test_serial.collidepoint(evento.pos):
                            mostrar_ventana_test_serial = False
                            mostrar_ventana_config_serial = True # Volver a abrir la config
                        elif 'rect_boton_copiar_test_serial' in globals() and rect_boton_copiar_test_serial.collidepoint(evento.pos):
                            if PYPERCLIP_AVAILABLE:
                                try:
                                    datos_a_copiar = "\n".join(datos_test_serial_buffer)
                                    pyperclip.copy(datos_a_copiar)
                                    copy_success_message = "Copiado!"
                                    copy_message_timer = pygame.time.get_ticks() + 2000 # 2 segundos
                                except Exception as e:
                                    copy_success_message = "Error al copiar."
                                    copy_message_timer = pygame.time.get_ticks() + 2000
                            else:
                                copy_success_message = "Pyperclip no disponible."
                                copy_message_timer = pygame.time.get_ticks() + 2000

            # Manejo de entrada de teclado
            if evento.type == pygame.KEYDOWN:
                if mostrar_ventana_config_serial:
                    if evento.key == pygame.K_ESCAPE:
                        mostrar_ventana_config_serial = False
                        puerto_dropdown_activo = False # Resetear estado dropdown
                        globals()['puerto_dropdown_activo'] = False
                
                elif mostrar_ventana_alarma and input_alarma_activo:
                    if evento.key == pygame.K_ESCAPE:
                        mostrar_ventana_alarma = False
                        input_alarma_activo = None
                    elif evento.key == pygame.K_BACKSPACE:
                        valores_ui_input_alarma[input_alarma_activo] = valores_ui_input_alarma[input_alarma_activo][:-1]
                    elif evento.unicode.isdigit():
                        # Permitir solo 2 dígitos para pitch/roll
                        if len(valores_ui_input_alarma[input_alarma_activo]) < 2:
                            valores_ui_input_alarma[input_alarma_activo] += evento.unicode
                
                elif mostrar_ventana_password_servicio and input_password_activo:
                    if evento.key == pygame.K_ESCAPE:
                        mostrar_ventana_password_servicio = False
                        input_password_str = ""
                        intento_password_fallido = False
                        input_password_activo = False
                    elif evento.key == pygame.K_RETURN or evento.key == pygame.K_KP_ENTER:
                        # Simular clic en botón "Entrar"
                        if input_password_str == CLAVE_ACCESO_SERVICIO:
                            mostrar_ventana_password_servicio = False
                            mostrar_ventana_servicio_datos = True
                            input_password_str = ""
                            intento_password_fallido = False
                            input_password_activo = False
                            input_api_key_thingspeak_str = API_KEY_THINGSPEAK
                            input_api_key_google_cloud_str = API_KEY_GOOGLE_CLOUD
                        else:
                            input_password_str = ""
                            intento_password_fallido = True
                            # input_password_activo podría mantenerse True o False aquí
                    elif evento.key == pygame.K_BACKSPACE:
                        input_password_str = input_password_str[:-1]
                    elif evento.unicode.isprintable():
                        if len(input_password_str) < 50: # Limitar longitud de contraseña
                             input_password_str += evento.unicode

                elif mostrar_ventana_servicio_datos and input_servicio_activo:
                    if evento.key == pygame.K_ESCAPE:
                        mostrar_ventana_servicio_datos = False
                        input_servicio_activo = None
                    elif evento.key == pygame.K_BACKSPACE:
                        if input_servicio_activo == "thingspeak":
                            input_api_key_thingspeak_str = input_api_key_thingspeak_str[:-1]
                        elif input_servicio_activo == "google_cloud":
                            input_api_key_google_cloud_str = input_api_key_google_cloud_str[:-1]
                        elif input_servicio_activo == "password_azure":
                            input_password_azure_str = input_password_azure_str[:-1]
                    elif evento.unicode.isprintable(): # Aceptar cualquier caracter imprimible para API keys
                        if input_servicio_activo == "thingspeak":
                            if len(input_api_key_thingspeak_str) < 50: # Limitar longitud
                                input_api_key_thingspeak_str += evento.unicode
                        elif input_servicio_activo == "google_cloud":
                            if len(input_api_key_google_cloud_str) < 200: # Limitar longitud (Google keys pueden ser largas)
                                input_api_key_google_cloud_str += evento.unicode
                        elif input_servicio_activo == "password_azure":
                            if len(input_password_azure_str) < 100:
                                input_password_azure_str += evento.unicode
                    elif evento.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL or pygame.key.get_mods() & pygame.KMOD_META):
                        if PYPERCLIP_AVAILABLE:
                            try:
                                pasted_text = pyperclip.paste()
                                if input_servicio_activo == "thingspeak":
                                    input_api_key_thingspeak_str += pasted_text
                                    if len(input_api_key_thingspeak_str) > 50:
                                        input_api_key_thingspeak_str = input_api_key_thingspeak_str[:50]
                                elif input_servicio_activo == "google_cloud":
                                    input_api_key_google_cloud_str += pasted_text
                                    if len(input_api_key_google_cloud_str) > 200:
                                        input_api_key_google_cloud_str = input_api_key_google_cloud_str[:200]
                                elif input_servicio_activo == "password_azure":
                                    input_password_azure_str += pasted_text
                                    if len(input_password_azure_str) > 100:
                                        input_password_azure_str = input_password_azure_str[:100]
                            except Exception:
                                pass


                elif mostrar_ventana_idioma:
                    if evento.key == pygame.K_ESCAPE:
                        mostrar_ventana_idioma = False
                
                elif mostrar_ventana_acerca_de:
                    if evento.key == pygame.K_ESCAPE:
                        mostrar_ventana_acerca_de = False
                elif mostrar_ventana_consola_datos: # Si la consola está visible
                    if evento.key == pygame.K_ESCAPE:
                        mostrar_ventana_consola_datos = False
                elif mostrar_ventana_test_serial:
                    if evento.key == pygame.K_ESCAPE:
                        mostrar_ventana_test_serial = False
                        mostrar_ventana_config_serial = True # Volver a abrir la config

        # Reconexión automática si el puerto no está disponible
        # Asegurarse que la ventana de consola no bloquee la reconexión si está abierta
        condiciones_para_no_reconectar = (
            mostrar_ventana_config_serial or
            mostrar_ventana_alarma or
            mostrar_ventana_acerca_de or
            mostrar_ventana_idioma or
            mostrar_ventana_password_servicio or # Añadido para ser consistente
            mostrar_ventana_servicio_datos # Añadido para ser consistente
        )
        if not serial_port_available and not condiciones_para_no_reconectar:
            ahora = pygame.time.get_ticks()
            if ahora - ultimo_intento_reconeccion_tiempo > INTERVALO_RECONECCION_MS:
                ultimo_intento_reconeccion_tiempo = ahora
                print(f"INFO: Intentando reconectar al puerto {puerto}...")
                try:
                    # Asegurarse de que el puerto anterior esté completamente cerrado
                    if ser is not None:
                        ser.close()
                    ser = serial.Serial(puerto, baudios, timeout=1)
                    serial_port_available = True
                    nmea_data_stale = False
                    ultima_vez_datos_recibidos = pygame.time.get_ticks()
                    print(f"INFO: Reconexión exitosa al puerto {puerto} a {baudios} baudios.")
                    agregar_a_consola(f"Reconectado a {puerto}.")
                except serial.SerialException:
                    ser = None
                    serial_port_available = False
                    # No imprimir nada aquí para no llenar la consola de fallos
                except Exception as e:
                    print(f"Error inesperado durante reconexión: {e}")
                    ser = None
                    serial_port_available = False
            time.sleep(1) # Pequeña pausa para no sobrecargar la CPU en el bucle de reconexión
        
        # Procesar datos del puerto serie
        procesar_datos_serie()
        # Envío periódico de datos y chequeo de red
        if not network_available:
            now = time.time()
            if now - last_network_check_time > 60: # Chequear cada 60 segundos
                print("INFO: Verificando estado de la red en un hilo separado...")
                network_check_thread = threading.Thread(target=check_network_connection)
                network_check_thread.daemon = True
                network_check_thread.start()
                last_network_check_time = now
        
        enviar_y_guardar_datos_periodicamente()
        
        # Detección de condiciones de alarma
        # Usar los valores de ts_pitch_float y ts_roll_float que ya son floats
        if valores_alarma: # Asegurarse que valores_alarma está cargado
            try:
                # Roll
                umbral_min_roll_float = float(valores_alarma["min_roll_neg"])
                umbral_max_roll_float = float(valores_alarma["max_roll_pos"])
                
                # Alarma Roll Babor
                condicion_babor = ts_roll_float < umbral_min_roll_float if att_roll_str != "N/A" else False
                if condicion_babor and not alarma_roll_babor_activa:
                    msg_alarma = f"ALARMA ROLL BABOR ACTIVADA. Valor: {ts_roll_float:.1f}°, Umbral: {umbral_min_roll_float:.1f}°"
                    guardar_alarma_csv(ts_timestamp_str if ts_timestamp_str != "N/A" else datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ROLL_BABOR", "ACTIVANDO", ts_roll_float, umbral_min_roll_float)
                    agregar_a_consola(msg_alarma)
                elif not condicion_babor and alarma_roll_babor_activa:
                    msg_alarma = f"ALARMA ROLL BABOR DESACTIVADA. Valor: {ts_roll_float:.1f}°"
                    guardar_alarma_csv(ts_timestamp_str if ts_timestamp_str != "N/A" else datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ROLL_BABOR", "DESACTIVANDO", ts_roll_float, umbral_min_roll_float)
                    agregar_a_consola(msg_alarma)
                alarma_roll_babor_activa = condicion_babor

                # Alarma Roll Estribor
                condicion_estribor = ts_roll_float > umbral_max_roll_float if att_roll_str != "N/A" else False
                if condicion_estribor and not alarma_roll_estribor_activa:
                    msg_alarma = f"ALARMA ROLL ESTRIBOR ACTIVADA. Valor: {ts_roll_float:.1f}°, Umbral: {umbral_max_roll_float:.1f}°"
                    guardar_alarma_csv(ts_timestamp_str if ts_timestamp_str != "N/A" else datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ROLL_ESTRIBOR", "ACTIVANDO", ts_roll_float, umbral_max_roll_float)
                    agregar_a_consola(msg_alarma)
                elif not condicion_estribor and alarma_roll_estribor_activa:
                    msg_alarma = f"ALARMA ROLL ESTRIBOR DESACTIVADA. Valor: {ts_roll_float:.1f}°"
                    guardar_alarma_csv(ts_timestamp_str if ts_timestamp_str != "N/A" else datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ROLL_ESTRIBOR", "DESACTIVANDO", ts_roll_float, umbral_max_roll_float)
                    agregar_a_consola(msg_alarma)
                alarma_roll_estribor_activa = condicion_estribor

                # Pitch
                umbral_min_pitch_float = float(valores_alarma["min_pitch_neg"])
                umbral_max_pitch_float = float(valores_alarma["max_pitch_pos"])

                # Alarma Pitch Encabuzado
                condicion_encabuzado = ts_pitch_float < umbral_min_pitch_float if att_pitch_str != "N/A" else False
                if condicion_encabuzado and not alarma_pitch_encabuzado_activa:
                    msg_alarma = f"ALARMA PITCH ENCABUZADO ACTIVADA. Valor: {ts_pitch_float:.1f}°, Umbral: {umbral_min_pitch_float:.1f}°"
                    guardar_alarma_csv(ts_timestamp_str if ts_timestamp_str != "N/A" else datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "PITCH_ENCABUZADO", "ACTIVANDO", ts_pitch_float, umbral_min_pitch_float)
                    agregar_a_consola(msg_alarma)
                elif not condicion_encabuzado and alarma_pitch_encabuzado_activa:
                    msg_alarma = f"ALARMA PITCH ENCABUZADO DESACTIVADA. Valor: {ts_pitch_float:.1f}°"
                    guardar_alarma_csv(ts_timestamp_str if ts_timestamp_str != "N/A" else datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "PITCH_ENCABUZADO", "DESACTIVANDO", ts_pitch_float, umbral_min_pitch_float)
                    agregar_a_consola(msg_alarma)
                alarma_pitch_encabuzado_activa = condicion_encabuzado
                
                # Alarma Pitch Sentado
                condicion_sentado = ts_pitch_float > umbral_max_pitch_float if att_pitch_str != "N/A" else False
                if condicion_sentado and not alarma_pitch_sentado_activa:
                    msg_alarma = f"ALARMA PITCH SENTADO ACTIVADA. Valor: {ts_pitch_float:.1f}°, Umbral: {umbral_max_pitch_float:.1f}°"
                    guardar_alarma_csv(ts_timestamp_str if ts_timestamp_str != "N/A" else datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "PITCH_SENTADO", "ACTIVANDO", ts_pitch_float, umbral_max_pitch_float)
                    agregar_a_consola(msg_alarma)
                elif not condicion_sentado and alarma_pitch_sentado_activa:
                    msg_alarma = f"ALARMA PITCH SENTADO DESACTIVADA. Valor: {ts_pitch_float:.1f}°"
                    guardar_alarma_csv(ts_timestamp_str if ts_timestamp_str != "N/A" else datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "PITCH_SENTADO", "DESACTIVANDO", ts_pitch_float, umbral_max_pitch_float)
                    agregar_a_consola(msg_alarma)
                alarma_pitch_sentado_activa = condicion_sentado
                
            except (ValueError, KeyError) as e: # Si hay error en conversión o claves
                # print(f"Error al procesar umbrales de alarma: {e}")
                alarma_roll_babor_activa = False
                alarma_roll_estribor_activa = False
                alarma_pitch_sentado_activa = False
                alarma_pitch_encabuzado_activa = False
        
        # Manejo de reproducción de alarmas
        alarmas_activas_para_sonar = []
        if alarma_roll_babor_activa:
            alarmas_activas_para_sonar.append(('roll_babor', ultima_reproduccion_alarma_babor_tiempo))
        if alarma_roll_estribor_activa:
            alarmas_activas_para_sonar.append(('roll_estribor', ultima_reproduccion_alarma_estribor_tiempo))
        if alarma_pitch_sentado_activa:
            alarmas_activas_para_sonar.append(('pitch_sentado', ultima_reproduccion_alarma_sentado_tiempo))
        if alarma_pitch_encabuzado_activa:
            alarmas_activas_para_sonar.append(('pitch_encabuzado', ultima_reproduccion_alarma_encabuzado_tiempo))
        
        # Si no hay alarmas activas, detener cualquier sonido que esté reproduciéndose
        if not alarmas_activas_para_sonar:
            if sonido_alarma_actualmente_reproduciendo is not None:
                sonido_alarma_actualmente_reproduciendo.stop()
                sonido_alarma_actualmente_reproduciendo = None
            INDICE_PROXIMA_ALARMA_A_SONAR = 0 # Resetear índice
        else:
            # Manejar reproducción de alarmas activas
            ahora = time.time()
            
            # Verificar si el sonido actual ha terminado o ha pasado el tiempo de pausa para alternar
            puede_reproducir_nueva_alarma = True
            if sonido_alarma_actualmente_reproduciendo is not None:
                try:
                    duracion_sonido_actual = sonido_alarma_actualmente_reproduciendo.get_length()
                    # Si el sonido está activo y no ha pasado su duración + pausa, no reproducir nueva
                    if pygame.mixer.get_busy() and (ahora < tiempo_ultimo_sonido_iniciado + duracion_sonido_actual + PAUSA_ENTRE_SONIDOS_ALTERNADOS_S):
                        puede_reproducir_nueva_alarma = False
                except pygame.error: # Si el sonido ya no es válido
                    sonido_alarma_actualmente_reproduciendo = None # Resetear

            if puede_reproducir_nueva_alarma:
                # Filtrar las alarmas que realmente necesitan sonar (cuyo intervalo ha pasado)
                alarmas_que_deben_sonar_ahora = []
                for tipo_alarma, ultima_vez_reproduccion in alarmas_activas_para_sonar:
                    intervalo_repeticion = INTERVALO_REPETICION_ALARMA_PITCH_S if 'pitch' in tipo_alarma else INTERVALO_REPETICION_ALARMA_ROLL_S
                    if ahora - ultima_vez_reproduccion >= intervalo_repeticion:
                        alarmas_que_deben_sonar_ahora.append(tipo_alarma)
                
                if alarmas_que_deben_sonar_ahora:
                    if INDICE_PROXIMA_ALARMA_A_SONAR >= len(alarmas_que_deben_sonar_ahora):
                        INDICE_PROXIMA_ALARMA_A_SONAR = 0
                    
                    tipo_alarma_a_reproducir = alarmas_que_deben_sonar_ahora[INDICE_PROXIMA_ALARMA_A_SONAR]
                    
                    if reproducir_alarma(tipo_alarma_a_reproducir):
                        # Actualizar el tiempo de última reproducción para ESTA alarma específica
                        if tipo_alarma_a_reproducir == 'roll_babor':
                            ultima_reproduccion_alarma_babor_tiempo = ahora
                        elif tipo_alarma_a_reproducir == 'roll_estribor':
                            ultima_reproduccion_alarma_estribor_tiempo = ahora
                        elif tipo_alarma_a_reproducir == 'pitch_sentado':
                            ultima_reproduccion_alarma_sentado_tiempo = ahora
                        elif tipo_alarma_a_reproducir == 'pitch_encabuzado':
                            ultima_reproduccion_alarma_encabuzado_tiempo = ahora
                        
                        INDICE_PROXIMA_ALARMA_A_SONAR = (INDICE_PROXIMA_ALARMA_A_SONAR + 1) % len(alarmas_que_deben_sonar_ahora)
        
        # Renderizado
        if imagen_fondo_escalada:
            screen.blit(imagen_fondo_escalada, (0, 0))
        else:
            screen.fill(AZUL) # Color de fondo por defecto si no hay imagen
        
        # Actualizar título de la ventana principal con el idioma actual
        pygame.display.set_caption(TEXTOS[IDIOMA]["titulo_ventana"])
        
        # Dibujar barra de herramientas si está visible
        if toolbar_visible: # Solo dibujar si el mouse está encima
            pygame.draw.rect(screen, COLOR_BARRA_HERRAMIENTAS_FONDO, rect_barra_herramientas)
            pygame.draw.rect(screen, COLOR_BARRA_HERRAMIENTAS_BORDE, rect_barra_herramientas, 1) # Borde
            
            rects_opciones_menu_barra.clear() # Limpiar rects anteriores
            current_x_menu_draw = padding_menu_x # Posición X inicial para el primer item del menú
            
            for opcion_texto in opciones_menu_barra: # Usar la lista actualizada
                texto_surf = font_bar_herramientas.render(opcion_texto, True, COLOR_ITEM_MENU_TEXTO)
                texto_rect = texto_surf.get_rect(left=current_x_menu_draw, centery=rect_barra_herramientas.centery)
                
                # Crear un Rect más grande para la detección de clics, centrado en el texto
                clickable_rect = texto_rect.inflate(padding_menu_x * 2, ALTURA_BARRA_HERRAMIENTAS // 3) # Padding horizontal y un poco vertical
                clickable_rect.centery = rect_barra_herramientas.centery # Asegurar centrado vertical
                
                rects_opciones_menu_barra.append(clickable_rect)
                screen.blit(texto_surf, texto_rect)
                current_x_menu_draw += texto_rect.width + espacio_entre_menus + padding_menu_x # Mover X para el siguiente item
        
        # Dibujar círculos para pitch y roll
        pygame.draw.circle(screen, BLANCO, (centro_x_circulo1, centro_y_circulos), radio_circulo_img, 2) # Círculo Pitch
        pygame.draw.circle(screen, BLANCO, (centro_x_circulo2, centro_y_circulos), radio_circulo_img, 2) # Círculo Roll
        
        # Dibujar indicador de pitch
        if pitch_image_base_grande and att_pitch_str != "N/A":
            try:
                valor_pitch_float = float(att_pitch_str)
                angulo_rotacion_pygame = -valor_pitch_float
                imagen_pitch_rotada_grande = pygame.transform.rotate(pitch_image_base_grande, angulo_rotacion_pygame)
                diametro_claraboya = 2 * radio_circulo_img
                claraboya_surface = pygame.Surface((diametro_claraboya, diametro_claraboya), pygame.SRCALPHA)
                claraboya_surface.fill((0,0,0,0))
                offset_x = (diametro_claraboya - imagen_pitch_rotada_grande.get_width()) // 2
                offset_y = (diametro_claraboya - imagen_pitch_rotada_grande.get_height()) // 2
                claraboya_surface.blit(imagen_pitch_rotada_grande, (offset_x, offset_y))
                mask_pygame = pygame.Surface((diametro_claraboya, diametro_claraboya), pygame.SRCALPHA) # Renombrado mask a mask_pygame para evitar conflicto con módulo mask
                mask_pygame.fill((0,0,0,0))
                pygame.draw.circle(mask_pygame, (255,255,255,255), (radio_circulo_img, radio_circulo_img), radio_circulo_img)
                claraboya_surface.blit(mask_pygame, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
                rect_claraboya_final = claraboya_surface.get_rect(center=(centro_x_circulo1, centro_y_circulos))
                screen.blit(claraboya_surface, rect_claraboya_final)
            except ValueError:
                pass
            
            pygame.draw.circle(screen, BLANCO, (centro_x_circulo1, centro_y_circulos), radio_circulo_img, 2)
            
            for key, (angle_deg, etiqueta_str) in ANGULOS_MARCAS_ETIQUETAS_DEF.items():
                angle_rad = math.radians(angle_deg)
                x_inicio_marca = centro_x_circulo1 + RADIO_INICIO_MARCAS * math.cos(angle_rad)
                y_inicio_marca = centro_y_circulos + RADIO_INICIO_MARCAS * math.sin(angle_rad)
                x_fin_marca = centro_x_circulo1 + RADIO_FIN_MARCAS * math.cos(angle_rad)
                y_fin_marca = centro_y_circulos + RADIO_FIN_MARCAS * math.sin(angle_rad)
                pygame.draw.line(screen, COLOR_MARCA_GRADO, (x_inicio_marca, y_inicio_marca), (x_fin_marca, y_fin_marca), GROSOR_MARCA_GRADO)
                etiqueta_surf = font.render(etiqueta_str, True, COLOR_ETIQUETA_GRADO)
                x_texto_etiqueta = centro_x_circulo1 + RADIO_POSICION_TEXTO_ETIQUETA * math.cos(angle_rad)
                y_texto_etiqueta = centro_y_circulos + RADIO_POSICION_TEXTO_ETIQUETA * math.sin(angle_rad)
                etiqueta_rect = etiqueta_surf.get_rect(center=(int(x_texto_etiqueta), int(y_texto_etiqueta)))
                screen.blit(etiqueta_surf, etiqueta_rect)

            if att_pitch_str != "N/A":
                try:
                    valor_pitch_float = float(att_pitch_str)
                    pitch_valor_surf = font_circulos_textos.render(f"{valor_pitch_float:+.1f}°", True, BLANCO)
                    y_pos_texto_pitch = centro_y_circulos + radio_circulo_img * 0.0282
                    pitch_valor_rect = pitch_valor_surf.get_rect(center=(centro_x_circulo1, y_pos_texto_pitch))
                    screen.blit(pitch_valor_surf, pitch_valor_rect)
                    
                    pos_flecha_pitch_x = pitch_valor_rect.left - OFFSET_FLECHA_TEXTO - (LONGITUD_FLECHA_DIR // 2)
                    pos_flecha_pitch_y_centro = pitch_valor_rect.centery
                    if valor_pitch_float > 0.1:
                        pygame.draw.line(screen, BLANCO, (pos_flecha_pitch_x, pos_flecha_pitch_y_centro + LONGITUD_FLECHA_DIR // 2), (pos_flecha_pitch_x, pos_flecha_pitch_y_centro - LONGITUD_FLECHA_DIR // 2), 2)
                        pygame.draw.line(screen, BLANCO, (pos_flecha_pitch_x - ANCHO_FLECHA_DIR // 2, pos_flecha_pitch_y_centro - LONGITUD_FLECHA_DIR // 2 + ANCHO_FLECHA_DIR // 2), (pos_flecha_pitch_x, pos_flecha_pitch_y_centro - LONGITUD_FLECHA_DIR // 2), 2)
                        pygame.draw.line(screen, BLANCO, (pos_flecha_pitch_x + ANCHO_FLECHA_DIR // 2, pos_flecha_pitch_y_centro - LONGITUD_FLECHA_DIR // 2 + ANCHO_FLECHA_DIR // 2), (pos_flecha_pitch_x, pos_flecha_pitch_y_centro - LONGITUD_FLECHA_DIR // 2), 2)
                    elif valor_pitch_float < -0.1:
                        pygame.draw.line(screen, BLANCO, (pos_flecha_pitch_x, pos_flecha_pitch_y_centro - LONGITUD_FLECHA_DIR // 2), (pos_flecha_pitch_x, pos_flecha_pitch_y_centro + LONGITUD_FLECHA_DIR // 2), 2)
                        pygame.draw.line(screen, BLANCO, (pos_flecha_pitch_x - ANCHO_FLECHA_DIR // 2, pos_flecha_pitch_y_centro + LONGITUD_FLECHA_DIR // 2 - ANCHO_FLECHA_DIR // 2), (pos_flecha_pitch_x, pos_flecha_pitch_y_centro + LONGITUD_FLECHA_DIR // 2), 2)
                        pygame.draw.line(screen, BLANCO, (pos_flecha_pitch_x + ANCHO_FLECHA_DIR // 2, pos_flecha_pitch_y_centro + LONGITUD_FLECHA_DIR // 2 - ANCHO_FLECHA_DIR // 2), (pos_flecha_pitch_x, pos_flecha_pitch_y_centro + LONGITUD_FLECHA_DIR // 2), 2)
                except ValueError:
                    pass

        # Dibujar indicador de roll
        if roll_image_base_grande and att_roll_str != "N/A":
            try:
                valor_roll_float = float(att_roll_str)
                angulo_rotacion_pygame_roll = -valor_roll_float
                imagen_roll_rotada_grande = pygame.transform.rotate(roll_image_base_grande, angulo_rotacion_pygame_roll)
                diametro_claraboya_roll = 2 * radio_circulo_img
                claraboya_surface_roll = pygame.Surface((diametro_claraboya_roll, diametro_claraboya_roll), pygame.SRCALPHA)
                claraboya_surface_roll.fill((0,0,0,0))
                offset_x_roll = (diametro_claraboya_roll - imagen_roll_rotada_grande.get_width()) // 2
                offset_y_roll = (diametro_claraboya_roll - imagen_roll_rotada_grande.get_height()) // 2
                claraboya_surface_roll.blit(imagen_roll_rotada_grande, (offset_x_roll, offset_y_roll))
                mask_roll_pygame = pygame.Surface((diametro_claraboya_roll, diametro_claraboya_roll), pygame.SRCALPHA) # Renombrado mask_roll a mask_roll_pygame
                mask_roll_pygame.fill((0,0,0,0))
                pygame.draw.circle(mask_roll_pygame, (255,255,255,255), (radio_circulo_img, radio_circulo_img), radio_circulo_img)
                claraboya_surface_roll.blit(mask_roll_pygame, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
                rect_claraboya_final_roll = claraboya_surface_roll.get_rect(center=(centro_x_circulo2, centro_y_circulos))
                screen.blit(claraboya_surface_roll, rect_claraboya_final_roll)
            except ValueError:
                pass
            
            pygame.draw.circle(screen, BLANCO, (centro_x_circulo2, centro_y_circulos), radio_circulo_img, 2)
            
            for key, (angle_deg, etiqueta_str) in ANGULOS_MARCAS_ETIQUETAS_DEF.items():
                angle_rad = math.radians(angle_deg)
                x_inicio_marca_roll = centro_x_circulo2 + RADIO_INICIO_MARCAS * math.cos(angle_rad)
                y_inicio_marca_roll = centro_y_circulos + RADIO_INICIO_MARCAS * math.sin(angle_rad)
                x_fin_marca_roll = centro_x_circulo2 + RADIO_FIN_MARCAS * math.cos(angle_rad)
                y_fin_marca_roll = centro_y_circulos + RADIO_FIN_MARCAS * math.sin(angle_rad)
                pygame.draw.line(screen, COLOR_MARCA_GRADO, (x_inicio_marca_roll, y_inicio_marca_roll), (x_fin_marca_roll, y_fin_marca_roll), GROSOR_MARCA_GRADO)
                etiqueta_surf_roll = font.render(etiqueta_str, True, COLOR_ETIQUETA_GRADO)
                x_texto_etiqueta_roll = centro_x_circulo2 + RADIO_POSICION_TEXTO_ETIQUETA * math.cos(angle_rad)
                y_texto_etiqueta_roll = centro_y_circulos + RADIO_POSICION_TEXTO_ETIQUETA * math.sin(angle_rad)
                etiqueta_rect_roll = etiqueta_surf_roll.get_rect(center=(int(x_texto_etiqueta_roll), int(y_texto_etiqueta_roll)))
                screen.blit(etiqueta_surf_roll, etiqueta_rect_roll)

            if att_roll_str != "N/A":
                try:
                    valor_roll_float = float(att_roll_str)
                    roll_valor_surf = font_circulos_textos.render(f"{valor_roll_float:+.1f}°", True, BLANCO)
                    y_pos_texto_roll = centro_y_circulos + radio_circulo_img * 0.0282
                    roll_valor_rect = roll_valor_surf.get_rect(center=(centro_x_circulo2, y_pos_texto_roll))
                    screen.blit(roll_valor_surf, roll_valor_rect)
                            
                    letra_roll_str = ""
                    if valor_roll_float > 0.1: # Positivo es Estribor (Starboard)
                        letra_roll_str = "S"
                    elif valor_roll_float < -0.1: # Negativo es Babor (Port)
                        letra_roll_str = "P"
                    if letra_roll_str:
                        letra_roll_surf = font_circulos_textos.render(letra_roll_str, True, COLOR_LETRA_ROLL)
                        letra_roll_rect = letra_roll_surf.get_rect(midtop=(roll_valor_rect.centerx, roll_valor_rect.bottom + OFFSET_LETRA_ROLL_Y))
                        screen.blit(letra_roll_surf, letra_roll_rect)

                    pos_flecha_roll_y_centro = roll_valor_rect.centery
                    if valor_roll_float > 0.1: # Positivo (Estribor), flecha VERDE a la DERECHA
                        pos_flecha_roll_x = roll_valor_rect.right + OFFSET_FLECHA_TEXTO + (LONGITUD_FLECHA_DIR // 2)
                        pygame.draw.line(screen, VERDE, (pos_flecha_roll_x - LONGITUD_FLECHA_DIR // 2, pos_flecha_roll_y_centro), (pos_flecha_roll_x + LONGITUD_FLECHA_DIR // 2, pos_flecha_roll_y_centro), 2)
                        pygame.draw.line(screen, VERDE, (pos_flecha_roll_x + LONGITUD_FLECHA_DIR // 2 - ANCHO_FLECHA_DIR // 2, pos_flecha_roll_y_centro - ANCHO_FLECHA_DIR // 2), (pos_flecha_roll_x + LONGITUD_FLECHA_DIR // 2, pos_flecha_roll_y_centro), 2)
                        pygame.draw.line(screen, VERDE, (pos_flecha_roll_x + LONGITUD_FLECHA_DIR // 2 - ANCHO_FLECHA_DIR // 2, pos_flecha_roll_y_centro + ANCHO_FLECHA_DIR // 2), (pos_flecha_roll_x + LONGITUD_FLECHA_DIR // 2, pos_flecha_roll_y_centro), 2)
                    elif valor_roll_float < -0.1: # Negativo (Babor), flecha ROJA a la IZQUIERDA
                        pos_flecha_roll_x = roll_valor_rect.left - OFFSET_FLECHA_TEXTO - (LONGITUD_FLECHA_DIR // 2)
                        pygame.draw.line(screen, ROJO, (pos_flecha_roll_x + LONGITUD_FLECHA_DIR // 2, pos_flecha_roll_y_centro), (pos_flecha_roll_x - LONGITUD_FLECHA_DIR // 2, pos_flecha_roll_y_centro), 2)
                        pygame.draw.line(screen, ROJO, (pos_flecha_roll_x - LONGITUD_FLECHA_DIR // 2 + ANCHO_FLECHA_DIR // 2, pos_flecha_roll_y_centro - ANCHO_FLECHA_DIR // 2), (pos_flecha_roll_x - LONGITUD_FLECHA_DIR // 2, pos_flecha_roll_y_centro), 2)
                        pygame.draw.line(screen, ROJO, (pos_flecha_roll_x - LONGITUD_FLECHA_DIR // 2 + ANCHO_FLECHA_DIR // 2, pos_flecha_roll_y_centro + ANCHO_FLECHA_DIR // 2), (pos_flecha_roll_x - LONGITUD_FLECHA_DIR // 2, pos_flecha_roll_y_centro), 2)
                except ValueError:
                    pass

        # Dibujar cajas de datos
        espacio_entre_cajas_vertical = 10
        ancho_cajas_datos = 280 # Ancho fijo para las 3 cajas
        x_inicio_cajas_datos = area_izquierda_rect.right + 10 # A la derecha del área de círculos
        
        # Caja de Lat/Lon
        altura_caja_latlon = 120 # Altura ajustada
        y_caja_latlon = ALTURA_BARRA_HERRAMIENTAS + espacio_entre_cajas_vertical # Debajo de la barra de herramientas
        dim_caja_gll = [x_inicio_cajas_datos, y_caja_latlon, ancho_cajas_datos, altura_caja_latlon]
        
        # Caja de Rumbo/Velocidad
        altura_caja_rumbo_vel = 120 # Altura ajustada
        y_caja_rumbo_vel = y_caja_latlon + altura_caja_latlon + espacio_entre_cajas_vertical # Debajo de Lat/Lon
        dim_caja_rumbo_vel = [x_inicio_cajas_datos, y_caja_rumbo_vel, ancho_cajas_datos, altura_caja_rumbo_vel]
        
        # Caja de Cabeceo (Attitude)
        altura_caja_cabeceo = 120 # Altura ajustada
        y_caja_cabeceo = y_caja_rumbo_vel + altura_caja_rumbo_vel + espacio_entre_cajas_vertical # Debajo de Rumbo/Vel
        dim_caja_att = [x_inicio_cajas_datos, y_caja_cabeceo, ancho_cajas_datos, altura_caja_cabeceo]
        
        # Caja de ROT (nueva)
        altura_caja_rot = 60 # Más pequeña
        y_caja_rot = y_caja_cabeceo + altura_caja_cabeceo + espacio_entre_cajas_vertical
        dim_caja_rot = [x_inicio_cajas_datos, y_caja_rot, ancho_cajas_datos, altura_caja_rot]

        # Dibujar las cajas (fondo y borde)
        pygame.draw.rect(screen, COLOR_CAJA_DATOS_FONDO, dim_caja_gll)
        pygame.draw.rect(screen, COLOR_CAJA_DATOS_BORDE, dim_caja_gll, 1)
        
        pygame.draw.rect(screen, COLOR_CAJA_DATOS_FONDO, dim_caja_rumbo_vel)
        pygame.draw.rect(screen, COLOR_CAJA_DATOS_BORDE, dim_caja_rumbo_vel, 1)
        
        pygame.draw.rect(screen, COLOR_CAJA_DATOS_FONDO, dim_caja_att)
        pygame.draw.rect(screen, COLOR_CAJA_DATOS_BORDE, dim_caja_att, 1)
        
        pygame.draw.rect(screen, COLOR_CAJA_DATOS_FONDO, dim_caja_rot)
        pygame.draw.rect(screen, COLOR_CAJA_DATOS_BORDE, dim_caja_rot, 1)

        # Mostrar datos en las cajas (usando TEXTOS[IDIOMA])
        
        # Caja Lat/Lon
        text_surface_titulo_latlon = font.render(TEXTOS[IDIOMA]["lat_lon"], True, COLOR_CAJA_DATOS_TEXTO)
        text_rect_titulo_latlon = text_surface_titulo_latlon.get_rect(centerx=dim_caja_gll[0] + dim_caja_gll[2] // 2, top=dim_caja_gll[1] + 5)
        screen.blit(text_surface_titulo_latlon, text_rect_titulo_latlon)
        
        text_surface_lat_data = font_datos_grandes.render(latitude_str, True, COLOR_CAJA_DATOS_TEXTO)
        text_rect_lat_data = text_surface_lat_data.get_rect(centerx=dim_caja_gll[0] + dim_caja_gll[2] // 2, top=text_rect_titulo_latlon.bottom + 2) # Espacio después del título
        screen.blit(text_surface_lat_data, text_rect_lat_data)
        
        text_surface_lon_data = font_datos_grandes.render(longitude_str, True, COLOR_CAJA_DATOS_TEXTO)
        text_rect_lon_data = text_surface_lon_data.get_rect(centerx=dim_caja_gll[0] + dim_caja_gll[2] // 2, top=text_rect_lat_data.bottom + 2) # Espacio después de latitud
        screen.blit(text_surface_lon_data, text_rect_lon_data)
        
        # Caja Rumbo/Velocidad
        padding_horizontal_caja = 15 # Padding interno para el texto
        y_pos_rumbo_vel = dim_caja_rumbo_vel[1] + 10 # Y inicial para la primera línea de texto
        
        rumbo_etiqueta_surf = font.render(TEXTOS[IDIOMA]["rumbo"] + " :", True, COLOR_CAJA_DATOS_TEXTO)
        rumbo_etiqueta_rect = rumbo_etiqueta_surf.get_rect(left=dim_caja_rumbo_vel[0] + padding_horizontal_caja, top=y_pos_rumbo_vel)
        rumbo_valor_surf = font_datos_grandes.render(heading_str, True, COLOR_CAJA_DATOS_TEXTO)
        # Alinear el valor grande verticalmente con la etiqueta pequeña
        rumbo_valor_rect = rumbo_valor_surf.get_rect(
            left=rumbo_etiqueta_rect.right + 5, 
            centery=rumbo_etiqueta_rect.centery + (font_datos_grandes.get_linesize() - font.get_linesize()) // 2 + 2 # Ajuste fino
        )
        screen.blit(rumbo_etiqueta_surf, rumbo_etiqueta_rect)
        screen.blit(rumbo_valor_surf, rumbo_valor_rect)
        
        y_pos_velocidad = rumbo_etiqueta_rect.top + font_datos_grandes.get_linesize() + 5 # Debajo de la línea de rumbo
        vel_etiqueta_surf = font.render(TEXTOS[IDIOMA]["velocidad"] + " :", True, COLOR_CAJA_DATOS_TEXTO)
        vel_etiqueta_rect = vel_etiqueta_surf.get_rect(left=dim_caja_rumbo_vel[0] + padding_horizontal_caja, top=y_pos_velocidad)
        vel_valor_surf = font_datos_grandes.render(speed_str, True, COLOR_CAJA_DATOS_TEXTO)
        vel_valor_rect = vel_valor_surf.get_rect(
            left=vel_etiqueta_rect.right + 5, 
            centery=vel_etiqueta_rect.centery + (font_datos_grandes.get_linesize() - font.get_linesize()) // 2 + 2 # Ajuste fino
        )
        screen.blit(vel_etiqueta_surf, vel_etiqueta_rect)
        screen.blit(vel_valor_surf, vel_valor_rect)
        
        # Caja Cabeceo (Attitude)
        text_surface_titulo_cabeceo = font.render(TEXTOS[IDIOMA]["actitud"], True, COLOR_CAJA_DATOS_TEXTO)
        text_rect_titulo_cabeceo = text_surface_titulo_cabeceo.get_rect(
            centerx=dim_caja_att[0] + dim_caja_att[2] // 2, 
            top=dim_caja_att[1] + 10 # Espacio desde el borde superior de la caja
        )
        screen.blit(text_surface_titulo_cabeceo, text_rect_titulo_cabeceo)
        
        current_y_att = text_rect_titulo_cabeceo.bottom + 10 # Y para la primera línea de datos (Pitch)
        
        # Pitch
        pitch_etiqueta_str = TEXTOS[IDIOMA]["pitch"] + " :"
        pitch_valor_str = "N/A" # Default
        if att_pitch_str != "N/A":
            try:
                pitch_valor_str = f"{float(att_pitch_str):+.1f}°" # Formato con signo y 1 decimal
            except ValueError:
                pass # Mantener "N/A" si no es convertible
        
        pitch_etiqueta_surf = font.render(pitch_etiqueta_str, True, COLOR_CAJA_DATOS_TEXTO)
        pitch_etiqueta_rect = pitch_etiqueta_surf.get_rect(
            left=dim_caja_att[0] + padding_horizontal_caja, 
            top=current_y_att
        )
        pitch_valor_surf = font_datos_grandes.render(pitch_valor_str, True, COLOR_CAJA_DATOS_TEXTO)
        pitch_valor_rect = pitch_valor_surf.get_rect(
            left=pitch_etiqueta_rect.right + 5, 
            centery=pitch_etiqueta_rect.centery + (font_datos_grandes.get_linesize() - font.get_linesize()) // 2 + 2 # Ajuste
        )
        screen.blit(pitch_etiqueta_surf, pitch_etiqueta_rect)
        screen.blit(pitch_valor_surf, pitch_valor_rect)
        
        current_y_att += font_datos_grandes.get_linesize() + 5 # Y para la siguiente línea (Roll)
        
        # Roll
        roll_etiqueta_str = TEXTOS[IDIOMA]["roll"] + "  :" # Espacio extra para alinear con Pitch
        roll_valor_display_str = "N/A"
        roll_direccion_str = "" # Para "BABOR" o "ESTRIBOR"
        
        if att_roll_str != "N/A":
            try:
                roll_val = float(att_roll_str)
                roll_valor_display_str = f"{roll_val:+.1f}°"
                if roll_val > 0.1: # Si es POSITIVO, es ESTRIBOR
                    roll_direccion_str = "ESTRIBOR" if IDIOMA == "es" else "STARBOARD"
                elif roll_val < -0.1: # Si es NEGATIVO, es BABOR
                    roll_direccion_str = "BABOR" if IDIOMA == "es" else "PORT"
            except ValueError:
                pass
        
        roll_etiqueta_surf = font.render(roll_etiqueta_str, True, COLOR_CAJA_DATOS_TEXTO)
        roll_etiqueta_rect = roll_etiqueta_surf.get_rect(
            left=dim_caja_att[0] + padding_horizontal_caja, 
            top=current_y_att
        )
        roll_valor_surf = font_datos_grandes.render(roll_valor_display_str, True, COLOR_CAJA_DATOS_TEXTO)
        roll_valor_rect = roll_valor_surf.get_rect(
            left=roll_etiqueta_rect.right + 5, 
            centery=roll_etiqueta_rect.centery + (font_datos_grandes.get_linesize() - font.get_linesize()) // 2 + 2 # Ajuste
        )
        screen.blit(roll_etiqueta_surf, roll_etiqueta_rect)
        screen.blit(roll_valor_surf, roll_valor_rect)
        
        if roll_direccion_str: # Mostrar "BABOR" / "ESTRIBOR" si aplica
            roll_direccion_surf = font.render(roll_direccion_str, True, COLOR_CAJA_DATOS_TEXTO)
            # Alinear con la etiqueta de Roll, a la derecha del valor numérico
            roll_direccion_rect = roll_direccion_surf.get_rect(
                left=roll_valor_rect.right + 5, 
                centery=roll_etiqueta_rect.centery # Alinear verticalmente con la etiqueta "Roll:"
            )
            screen.blit(roll_direccion_surf, roll_direccion_rect)
        
        # Caja ROT
        rot_etiqueta_surf = font.render(TEXTOS[IDIOMA]["rot"] + " :", True, COLOR_CAJA_DATOS_TEXTO)
        rot_valor_str = f"{rot_float:+.1f}°/min"
        rot_valor_surf = font_datos_grandes.render(rot_valor_str, True, COLOR_CAJA_DATOS_TEXTO)
        
        rot_etiqueta_rect = rot_etiqueta_surf.get_rect(
            left=dim_caja_rot[0] + padding_horizontal_caja,
            centery=dim_caja_rot[1] + dim_caja_rot[3] // 2
        )
        rot_valor_rect = rot_valor_surf.get_rect(
            left=rot_etiqueta_rect.right + 10,
            centery=rot_etiqueta_rect.centery
        )
        screen.blit(rot_etiqueta_surf, rot_etiqueta_rect)
        screen.blit(rot_valor_surf, rot_valor_rect)

        # Dibujar la nueva caja de Altitud debajo de los círculos
        # (Asegurarse de que se dibuje antes de los mensajes de estado para que no los tape)
        altura_caja_altitud = 60 # Altura para la caja de altitud
        
        # Calcular el ancho total que ocupan los círculos para centrar la caja de altitud y la barra de ROT
        ancho_total_circulos = (centro_x_circulo2 + radio_circulo_img) - (centro_x_circulo1 - radio_circulo_img)
        centro_x_area_circulos = (centro_x_circulo1 - radio_circulo_img) + (ancho_total_circulos / 2)
        
        ancho_caja_altitud = 300 # Un ancho fijo
        x_inicio_caja_altitud = centro_x_area_circulos - (ancho_caja_altitud / 2)

        y_caja_altitud = centro_y_circulos + radio_circulo_img + 20 # 20px de margen debajo de los círculos
        
        dim_caja_altitud = pygame.Rect(x_inicio_caja_altitud, y_caja_altitud, ancho_caja_altitud, altura_caja_altitud)

        pygame.draw.rect(screen, COLOR_CAJA_DATOS_FONDO, dim_caja_altitud)
        pygame.draw.rect(screen, COLOR_CAJA_DATOS_BORDE, dim_caja_altitud, 1)

        # Título para la caja de altitud
        texto_titulo_altitud_str = TEXTOS[IDIOMA].get("altitud", "ALTITUD") # Usar .get con fallback
        text_surface_titulo_altitud = font.render(texto_titulo_altitud_str, True, COLOR_CAJA_DATOS_TEXTO)
        text_rect_titulo_altitud = text_surface_titulo_altitud.get_rect(
            centerx=dim_caja_altitud[0] + dim_caja_altitud[2] // 2, 
            top=dim_caja_altitud[1] + 5 # Pequeño padding superior para el título
        )
        screen.blit(text_surface_titulo_altitud, text_rect_titulo_altitud)

        # Valor de la altitud
        text_surface_altitud_data = font_datos_grandes.render(altitude_str, True, COLOR_CAJA_DATOS_TEXTO)
        text_rect_altitud_data = text_surface_altitud_data.get_rect(
            centerx=dim_caja_altitud[0] + dim_caja_altitud[2] // 2, 
            top=text_rect_titulo_altitud.bottom + 2 # Debajo del título
        )
        screen.blit(text_surface_altitud_data, text_rect_altitud_data)

        # Dibujar LEDs de sentinas
        radio_led = 15
        y_leds = dim_caja_altitud.centery
        x_led1 = dim_caja_altitud.right + 40
        x_led2 = x_led1 + radio_led * 2 + 80

        # LED 1
        if switch1_status == "ON":
            color_led1 = ROJO
        elif switch1_status == "OFF":
            color_led1 = VERDE
        else: # N/A o cualquier otro estado
            color_led1 = AZUL
        pygame.draw.circle(screen, color_led1, (x_led1, y_leds), radio_led)
        label_sentina1_surf = font.render(TEXTOS[IDIOMA]["sentina1"], True, BLANCO)
        label_sentina1_rect = label_sentina1_surf.get_rect(center=(x_led1, y_leds + radio_led + 15))
        screen.blit(label_sentina1_surf, label_sentina1_rect)

        # LED 2
        if switch2_status == "ON":
            color_led2 = ROJO
        elif switch2_status == "OFF":
            color_led2 = VERDE
        else: # N/A o cualquier otro estado
            color_led2 = AZUL
        pygame.draw.circle(screen, color_led2, (x_led2, y_leds), radio_led)
        label_sentina2_surf = font.render(TEXTOS[IDIOMA]["sentina2"], True, BLANCO)
        label_sentina2_rect = label_sentina2_surf.get_rect(center=(x_led2, y_leds + radio_led + 15))
        screen.blit(label_sentina2_surf, label_sentina2_rect)

        # --- Dibujar la barra de ROT ---
        y_barra_rot = dim_caja_altitud.bottom + 35 # Espacio reducido debajo de la caja de altitud
        ancho_barra_rot = 400 # Aumentado de 300 a 400
        alto_barra_rot = 15
        x_barra_rot = centro_x_area_circulos - (ancho_barra_rot / 2)
        
        rect_barra_rot_fondo = pygame.Rect(x_barra_rot, y_barra_rot, ancho_barra_rot, alto_barra_rot)
        
        # Dibujar fondo de la barra y marcas
        pygame.draw.rect(screen, NEGRO, rect_barra_rot_fondo)
        pygame.draw.rect(screen, BLANCO, rect_barra_rot_fondo, 1)
        
        # Marca central (0) y marcas adicionales ("garrapatas")
        tick_values = [-60, -40, -20, 0, 20, 40, 60]
        for val in tick_values:
            ratio = val / 60.0
            tick_x = rect_barra_rot_fondo.centerx + ratio * (ancho_barra_rot / 2)
            pygame.draw.line(screen, BLANCO, (tick_x, rect_barra_rot_fondo.top), (tick_x, rect_barra_rot_fondo.bottom), 1)
        
        # Etiquetas
        font_rot_bar = pygame.font.Font(None, 20)
        label_port_surf = font_rot_bar.render(TEXTOS[IDIOMA]["port_label"], True, BLANCO)
        label_stbd_surf = font_rot_bar.render(TEXTOS[IDIOMA]["stbd_label"], True, BLANCO)
        
        screen.blit(label_port_surf, (rect_barra_rot_fondo.left - label_port_surf.get_width() - 5, rect_barra_rot_fondo.centery - label_port_surf.get_height() // 2))
        screen.blit(label_stbd_surf, (rect_barra_rot_fondo.right + 5, rect_barra_rot_fondo.centery - label_stbd_surf.get_height() // 2))

        # Dibujar etiquetas numéricas para las marcas
        for val in tick_values:
            ratio = val / 60.0
            tick_x = rect_barra_rot_fondo.centerx + ratio * (ancho_barra_rot / 2)
            label_surf = font_rot_bar.render(str(abs(val)), True, BLANCO)
            screen.blit(label_surf, (tick_x - label_surf.get_width() // 2, rect_barra_rot_fondo.bottom + 5))
        
        # Dibujar indicador
        # Mapear el valor de rot_float (-60 a +60) a la posición x en la barra
        max_rot_val = 60.0
        # Limitar el valor de rot_float al rango para que el indicador no se salga de la barra
        rot_clamp = max(-max_rot_val, min(max_rot_val, rot_float))
        
        # Calcular la posición. Si rot_clamp es -60, ratio es -1. Si es +60, ratio es +1. Si es 0, ratio es 0.
        ratio = rot_clamp / max_rot_val
        indicador_x = rect_barra_rot_fondo.centerx + ratio * (ancho_barra_rot / 2)
        
        # Dibujar un rectángulo de llenado (como termómetro)
        ancho_llenado = abs(indicador_x - rect_barra_rot_fondo.centerx)
        if rot_clamp > 0:
            # Si es positivo, dibujar desde el centro hacia la derecha
            rect_llenado = pygame.Rect(rect_barra_rot_fondo.centerx, rect_barra_rot_fondo.top, ancho_llenado, alto_barra_rot)
        else:
            # Si es negativo, dibujar desde la izquierda (indicador_x) hacia el centro
            rect_llenado = pygame.Rect(indicador_x, rect_barra_rot_fondo.top, ancho_llenado, alto_barra_rot)
        
        pygame.draw.rect(screen, VERDE, rect_llenado)


        # Mostrar mensajes de estado (NO HAY DATOS / DESCONECTADO)
        # Estos mensajes deben aparecer encima de los círculos si están activos
        if serial_port_available and ser and ser.is_open:
            ahora_ms = pygame.time.get_ticks()
            if ahora_ms - ultima_vez_datos_recibidos > UMBRAL_SIN_DATOS_MS:
                if not nmea_data_stale: # Si acabamos de perder datos
                    reset_ui_data() # Limpiar todos los valores en pantalla
                    nmea_data_stale = True # Marcar que los datos son viejos
                    agregar_a_consola("NMEA: NO HAY DATOS (TIMEOUT)")
                
                mensaje_no_datos_actual = TEXTOS[IDIOMA]["no_datos"]
                texto_no_datos_surf = font.render(mensaje_no_datos_actual, True, ROJO)
                rect_texto_no_datos = texto_no_datos_surf.get_rect(center=area_izquierda_rect.center)
                screen.blit(texto_no_datos_surf, rect_texto_no_datos)
        elif not serial_port_available: # Si el puerto está desconectado
            if not nmea_data_stale: # Si acabamos de detectar la desconexión
                reset_ui_data()
                nmea_data_stale = True
                agregar_a_consola(f"NMEA: Puerto {puerto} DESCONECTADO.")
            
            mensaje_desconexion_actual = TEXTOS[IDIOMA]["desconectado"]
            texto_desconexion_surf = font.render(mensaje_desconexion_actual, True, ROJO)
            rect_texto_desconexion = texto_desconexion_surf.get_rect(center=area_izquierda_rect.center)
            screen.blit(texto_desconexion_surf, rect_texto_desconexion)
        
        # Dibujar ventanas modales (Configuración, Alarma, Idioma, Acerca de)
        # Estas deben dibujarse al final para que estén por encima de todo lo demás.
        
        # Ventana de configuración de puerto
        if mostrar_ventana_config_serial:
            # Dibujar fondo y borde 3D de la ventana
            pygame.draw.rect(screen, COLOR_VENTANA_FONDO, rect_ventana_config)
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_CLARO, rect_ventana_config.topleft, rect_ventana_config.topright, 2) # Borde superior claro
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_CLARO, rect_ventana_config.topleft, rect_ventana_config.bottomleft, 2) # Borde izquierdo claro
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_OSCURO, rect_ventana_config.bottomleft, rect_ventana_config.bottomright, 2) # Borde inferior oscuro
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_OSCURO, rect_ventana_config.topright, rect_ventana_config.bottomright, 2) # Borde derecho oscuro
            
            # Título de la ventana
            titulo_surf = font.render(TEXTOS[IDIOMA]["titulo_config"], True, COLOR_TEXTO_NORMAL)
            screen.blit(titulo_surf, (rect_ventana_config.centerx - titulo_surf.get_width() // 2, rect_ventana_config.top + 15))
            
            # Botón cerrar (X)
            pygame.draw.rect(screen, COLOR_BOTON_FONDO_3D, rect_boton_cerrar_config) # Fondo del botón
            # Bordes 3D para el botón
            pygame.draw.line(screen, COLOR_BOTON_BORDE_CLARO_3D, rect_boton_cerrar_config.topleft, rect_boton_cerrar_config.topright, 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_CLARO_3D, rect_boton_cerrar_config.topleft, pygame.math.Vector2(rect_boton_cerrar_config.left, rect_boton_cerrar_config.bottom -1), 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_OSCURO_3D, pygame.math.Vector2(rect_boton_cerrar_config.left, rect_boton_cerrar_config.bottom -1), rect_boton_cerrar_config.bottomright, 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_OSCURO_3D, pygame.math.Vector2(rect_boton_cerrar_config.right -1, rect_boton_cerrar_config.top), rect_boton_cerrar_config.bottomright, 1)
            cerrar_text = font.render("X", True, COLOR_TEXTO_NORMAL)
            screen.blit(cerrar_text, cerrar_text.get_rect(center=rect_boton_cerrar_config.center))
            
            # Etiqueta y campo de puerto (dropdown)
            label_puerto_surf = font.render(TEXTOS[IDIOMA]["etiqueta_puerto"], True, COLOR_TEXTO_NORMAL)
            screen.blit(label_puerto_surf, (rect_ventana_config.left + padding_interno_config, rect_input_puerto_config.centery - label_puerto_surf.get_height() // 2))
            
            # Input field para Puerto (display del valor seleccionado)
            pygame.draw.rect(screen, COLOR_INPUT_FONDO, rect_input_puerto_config, 0) # Fondo del input
            # Borde 3D para el input
            pygame.draw.line(screen, COLOR_INPUT_BORDE_OSCURO_3D, rect_input_puerto_config.topleft, rect_input_puerto_config.topright, 1)
            pygame.draw.line(screen, COLOR_INPUT_BORDE_OSCURO_3D, rect_input_puerto_config.topleft, pygame.math.Vector2(rect_input_puerto_config.left, rect_input_puerto_config.bottom -1), 1)
            pygame.draw.line(screen, COLOR_INPUT_BORDE_CLARO_3D, pygame.math.Vector2(rect_input_puerto_config.left, rect_input_puerto_config.bottom -1), rect_input_puerto_config.bottomright, 1)
            pygame.draw.line(screen, COLOR_INPUT_BORDE_CLARO_3D, pygame.math.Vector2(rect_input_puerto_config.right -1, rect_input_puerto_config.top), rect_input_puerto_config.bottomright, 1)
            
            input_puerto_surf = font.render(input_puerto_str, True, COLOR_TEXTO_NORMAL) # Valor actual del puerto
            screen.blit(input_puerto_surf, (rect_input_puerto_config.left + 5, rect_input_puerto_config.centery - input_puerto_surf.get_height() // 2))
            
            # Flecha del dropdown de puerto
            pygame.draw.polygon(screen, COLOR_TEXTO_NORMAL, [
                (rect_input_puerto_config.right - 15, rect_input_puerto_config.centery - 3),
                (rect_input_puerto_config.right - 5, rect_input_puerto_config.centery - 3),
                (rect_input_puerto_config.right - 10, rect_input_puerto_config.centery + 3)
            ])
            
            # Etiqueta y campo de baudios (dropdown)
            label_baudios_surf = font.render(TEXTOS[IDIOMA]["etiqueta_baudios"], True, COLOR_TEXTO_NORMAL)
            screen.blit(label_baudios_surf, (rect_ventana_config.left + padding_interno_config, rect_input_baudios_display_config.centery - label_baudios_surf.get_height() // 2))
            
            pygame.draw.rect(screen, COLOR_INPUT_FONDO, rect_input_baudios_display_config, 0) # Fondo
            # Borde 3D
            pygame.draw.line(screen, COLOR_INPUT_BORDE_OSCURO_3D, rect_input_baudios_display_config.topleft, rect_input_baudios_display_config.topright, 1)
            pygame.draw.line(screen, COLOR_INPUT_BORDE_OSCURO_3D, rect_input_baudios_display_config.topleft, pygame.math.Vector2(rect_input_baudios_display_config.left, rect_input_baudios_display_config.bottom -1), 1)
            pygame.draw.line(screen, COLOR_INPUT_BORDE_CLARO_3D, pygame.math.Vector2(rect_input_baudios_display_config.left, rect_input_baudios_display_config.bottom -1), rect_input_baudios_display_config.bottomright, 1)
            pygame.draw.line(screen, COLOR_INPUT_BORDE_CLARO_3D, pygame.math.Vector2(rect_input_baudios_display_config.right -1, rect_input_baudios_display_config.top), rect_input_baudios_display_config.bottomright, 1)

            baudios_surf = font.render(str(lista_baudios_seleccionables[input_baudios_idx]), True, COLOR_TEXTO_NORMAL)
            screen.blit(baudios_surf, baudios_surf.get_rect(center=rect_input_baudios_display_config.center))
            
            # Flecha del dropdown de baudios
            pygame.draw.polygon(screen, COLOR_TEXTO_NORMAL, [
                (rect_input_baudios_display_config.right - 15, rect_input_baudios_display_config.centery - 3),
                (rect_input_baudios_display_config.right - 5, rect_input_baudios_display_config.centery - 3),
                (rect_input_baudios_display_config.right - 10, rect_input_baudios_display_config.centery + 3)
            ])
            
            # Botón Test
            pygame.draw.rect(screen, COLOR_BOTON_FONDO_3D, rect_boton_test_config)
            # (bordes 3D para el botón test)
            test_surf = font.render(TEXTOS[IDIOMA]["boton_test"], True, COLOR_TEXTO_NORMAL)
            screen.blit(test_surf, test_surf.get_rect(center=rect_boton_test_config.center))

            # Botón guardar
            pygame.draw.rect(screen, COLOR_BOTON_FONDO_3D, rect_boton_guardar_config) # Fondo
            # Borde 3D
            pygame.draw.line(screen, COLOR_BOTON_BORDE_CLARO_3D, rect_boton_guardar_config.topleft, rect_boton_guardar_config.topright, 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_CLARO_3D, rect_boton_guardar_config.topleft, pygame.math.Vector2(rect_boton_guardar_config.left, rect_boton_guardar_config.bottom -1), 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_OSCURO_3D, pygame.math.Vector2(rect_boton_guardar_config.left, rect_boton_guardar_config.bottom -1), rect_boton_guardar_config.bottomright, 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_OSCURO_3D, pygame.math.Vector2(rect_boton_guardar_config.right -1, rect_boton_guardar_config.top), rect_boton_guardar_config.bottomright, 1)
            
            guardar_surf = font.render(TEXTOS[IDIOMA]["boton_guardar"], True, COLOR_TEXTO_NORMAL)
            screen.blit(guardar_surf, guardar_surf.get_rect(center=rect_boton_guardar_config.center))
            
            # Dibujar desplegables si están activos (deben dibujarse encima de otros elementos)
            puerto_dropdown_activo = globals().get('puerto_dropdown_activo', False) # Obtener estado actual
            baudios_dropdown_activo = globals().get('baudios_dropdown_activo', False)
            lista_rects_items_puerto = globals().get('lista_rects_items_puerto', [])
            lista_rects_items_baudios = globals().get('lista_rects_items_baudios', [])


            if puerto_dropdown_activo and lista_puertos_detectados:
                lista_rects_items_puerto.clear() # Limpiar rects de items anteriores
                item_height = input_puerto_surf.get_height() + 4 # Altura de cada item en el dropdown
                # Calcular altura máxima del dropdown para que no se salga de la ventana
                dropdown_max_items = 5 # Mostrar max 5 items a la vez, luego scroll (no implementado aquí)
                dropdown_height = min(item_height * len(lista_puertos_detectados), item_height * dropdown_max_items)
                
                rect_lista_puertos_desplegable = pygame.Rect(
                    rect_input_puerto_config.left,
                    rect_input_puerto_config.bottom, # Debajo del input de puerto
                    rect_input_puerto_config.width,
                    dropdown_height
                )
                globals()['rect_lista_puertos_desplegable'] = rect_lista_puertos_desplegable


                pygame.draw.rect(screen, COLOR_DROPDOWN_FONDO, rect_lista_puertos_desplegable)
                pygame.draw.rect(screen, COLOR_DROPDOWN_BORDE, rect_lista_puertos_desplegable, 1) # Borde del dropdown
                
                for i, port_name in enumerate(lista_puertos_detectados):
                    if i * item_height >= dropdown_height: # No dibujar más items de los que caben
                        break
                    
                    item_rect = pygame.Rect(
                        rect_lista_puertos_desplegable.left,
                        rect_lista_puertos_desplegable.top + i * item_height,
                        rect_lista_puertos_desplegable.width,
                        item_height
                    )
                    lista_rects_items_puerto.append(item_rect) # Guardar rect para detección de clic
                
                    
                    item_surf = font.render(port_name, True, COLOR_TEXTO_NORMAL)
                    screen.blit(item_surf, (item_rect.left + 5, item_rect.centery - item_surf.get_height() // 2))
                globals()['lista_rects_items_puerto'] = lista_rects_items_puerto
            
            elif baudios_dropdown_activo: # Similar para baudios
                lista_rects_items_baudios.clear()
                item_height = baudios_surf.get_height() + 4
                dropdown_max_items = 5
                dropdown_height = min(item_height * len(lista_baudios_seleccionables), item_height * dropdown_max_items)
                
                rect_lista_baudios_desplegable = pygame.Rect(
                    rect_input_baudios_display_config.left,
                    rect_input_baudios_display_config.bottom,
                    rect_input_baudios_display_config.width,
                    dropdown_height
                )
                globals()['rect_lista_baudios_desplegable'] = rect_lista_baudios_desplegable

                pygame.draw.rect(screen, COLOR_DROPDOWN_FONDO, rect_lista_baudios_desplegable)
                pygame.draw.rect(screen, COLOR_DROPDOWN_BORDE, rect_lista_baudios_desplegable, 1)
                
                for i, baud_rate in enumerate(lista_baudios_seleccionables):
                    if i * item_height >= dropdown_height:
                        break
                    
                    item_rect = pygame.Rect(
                        rect_lista_baudios_desplegable.left,
                        rect_lista_baudios_desplegable.top + i * item_height,
                        rect_lista_baudios_desplegable.width,
                        item_height
                    )
                    lista_rects_items_baudios.append(item_rect)
                    
                    if i == input_baudios_idx: # Resaltar el baudrate seleccionado actualmente
                        pygame.draw.rect(screen, COLOR_SELECCION_DROPDOWN, item_rect)
                    # elif item_rect.collidepoint(mouse_pos): # Resaltar si mouse encima (opcional)
                    #    pygame.draw.rect(screen, pygame.Color('lightgrey'), item_rect)
                        
                    item_surf = font.render(str(baud_rate), True, COLOR_TEXTO_NORMAL)
                    screen.blit(item_surf, (item_rect.left + 5, item_rect.centery - item_surf.get_height() // 2))
                globals()['lista_rects_items_baudios'] = lista_rects_items_baudios
        
        # Ventana de configuración de alarmas
        elif mostrar_ventana_alarma:
            pygame.draw.rect(screen, (240, 240, 240), rect_ventana_alarma) # Fondo gris claro
            pygame.draw.rect(screen, COLOR_BORDE_VENTANA, rect_ventana_alarma, 2) # Borde
            
            titulo_alarma_surf = font.render(TEXTOS[IDIOMA]["titulo_alarma"], True, COLOR_TEXTO_NORMAL)
            screen.blit(titulo_alarma_surf, (rect_ventana_alarma.centerx - titulo_alarma_surf.get_width() // 2, rect_ventana_alarma.top + 15))
            
            # Definición de geometrías para inputs de alarma (importante que estén antes de usarlos en eventos)
            y_start_inputs = rect_ventana_alarma.top + 70
            input_height = 30
            label_width_alarma = 150 
            input_width_alarma = 80 
            padding_y_alarma = 25 # Espacio vertical entre inputs
            label_x_alarma = rect_ventana_alarma.left + 20
            input_x_alarma = label_x_alarma + label_width_alarma + 10
            
            # Campo de pitch
            rect_label_pitch_alarma = pygame.Rect(label_x_alarma, y_start_inputs, label_width_alarma, input_height)
            rect_input_pitch_alarma = pygame.Rect(input_x_alarma, y_start_inputs, input_width_alarma, input_height)
            globals()['rect_input_pitch_alarma'] = rect_input_pitch_alarma # Para acceso en eventos
            
            label_pitch_surf = font.render(TEXTOS[IDIOMA]["pitch_rango"], True, COLOR_TEXTO_NORMAL)
            screen.blit(label_pitch_surf, label_pitch_surf.get_rect(centery=rect_label_pitch_alarma.centery, left=rect_label_pitch_alarma.left))
            
            color_fondo_input_pitch = pygame.Color('lightskyblue1') if input_alarma_activo == "pitch" else COLOR_INPUT_FONDO
            pygame.draw.rect(screen, color_fondo_input_pitch, rect_input_pitch_alarma)
            pygame.draw.rect(screen, COLOR_INPUT_BORDE, rect_input_pitch_alarma, 1) # Borde del input
            
            input_pitch_surf = font.render(valores_ui_input_alarma["pitch"], True, COLOR_TEXTO_NORMAL)
            screen.blit(input_pitch_surf, (rect_input_pitch_alarma.left + 5, rect_input_pitch_alarma.centery - input_pitch_surf.get_height() // 2))
            
            # Campo de roll
            y_current_alarma = y_start_inputs + input_height + padding_y_alarma
            rect_label_roll_alarma = pygame.Rect(label_x_alarma, y_current_alarma, label_width_alarma, input_height)
            rect_input_roll_alarma = pygame.Rect(input_x_alarma, y_current_alarma, input_width_alarma, input_height)
            globals()['rect_input_roll_alarma'] = rect_input_roll_alarma # Para acceso en eventos

            label_roll_surf = font.render(TEXTOS[IDIOMA]["roll_rango"], True, COLOR_TEXTO_NORMAL)
            screen.blit(label_roll_surf, label_roll_surf.get_rect(centery=rect_label_roll_alarma.centery, left=rect_label_roll_alarma.left))
            
            color_fondo_input_roll = pygame.Color('lightskyblue1') if input_alarma_activo == "roll" else COLOR_INPUT_FONDO
            pygame.draw.rect(screen, color_fondo_input_roll, rect_input_roll_alarma)
            pygame.draw.rect(screen, COLOR_INPUT_BORDE, rect_input_roll_alarma, 1) # Borde
            
            input_roll_surf = font.render(valores_ui_input_alarma["roll"], True, COLOR_TEXTO_NORMAL)
            screen.blit(input_roll_surf, (rect_input_roll_alarma.left + 5, rect_input_roll_alarma.centery - input_roll_surf.get_height() // 2))
            
            # Botones Guardar y Salir para ventana de alarma
            button_width_alarma = 120
            button_height_alarma = 40
            y_botones_alarma = rect_ventana_alarma.bottom - button_height_alarma - 20 # Posición Y de los botones
            
            rect_boton_guardar_alarma = pygame.Rect(
                rect_ventana_alarma.centerx - button_width_alarma - 10, # Botón Guardar a la izquierda
                y_botones_alarma,
                button_width_alarma,
                button_height_alarma
            )
            globals()['rect_boton_guardar_alarma'] = rect_boton_guardar_alarma

            rect_boton_salir_alarma = pygame.Rect(
                rect_ventana_alarma.centerx + 10, # Botón Salir a la derecha
                y_botones_alarma,
                button_width_alarma,
                button_height_alarma
            )
            globals()['rect_boton_salir_alarma'] = rect_boton_salir_alarma
            
            # Dibujar botón Guardar
            pygame.draw.rect(screen, COLOR_BOTON_FONDO, rect_boton_guardar_alarma)
            pygame.draw.rect(screen, COLOR_BOTON_BORDE, rect_boton_guardar_alarma, 1) # Borde
            guardar_alarma_surf = font.render(TEXTOS[IDIOMA]["boton_guardar"], True, COLOR_TEXTO_NORMAL)
            screen.blit(guardar_alarma_surf, guardar_alarma_surf.get_rect(center=rect_boton_guardar_alarma.center))
            
            # Dibujar botón Salir
            pygame.draw.rect(screen, COLOR_BOTON_FONDO, rect_boton_salir_alarma)
            pygame.draw.rect(screen, COLOR_BOTON_BORDE, rect_boton_salir_alarma, 1) # Borde
            salir_alarma_surf = font.render(TEXTOS[IDIOMA]["boton_salir"], True, COLOR_TEXTO_NORMAL)
            screen.blit(salir_alarma_surf, salir_alarma_surf.get_rect(center=rect_boton_salir_alarma.center))
        
        # Ventana Acerca de
        elif mostrar_ventana_acerca_de:
            rect_ventana_acerca_de = pygame.Rect(250, 150, 400, 250) # Definir dimensiones
            pygame.draw.rect(screen, (240, 240, 240), rect_ventana_acerca_de) # Fondo
            pygame.draw.rect(screen, COLOR_BORDE_VENTANA, rect_ventana_acerca_de, 2) # Borde
            
            titulo_acerca_surf = font.render(TEXTOS[IDIOMA]["about_title"], True, COLOR_TEXTO_NORMAL)
            screen.blit(titulo_acerca_surf, (rect_ventana_acerca_de.centerx - titulo_acerca_surf.get_width() // 2, rect_ventana_acerca_de.top + 15))
            
            texto_info = [
                TEXTOS[IDIOMA]["about_line1"],
                TEXTOS[IDIOMA]["about_line2"],
                TEXTOS[IDIOMA]["about_line3"],
                TEXTOS[IDIOMA]["about_line4"],
                "                                        " + TEXTOS[IDIOMA]["about_line5"]
            ]
            
            y_offset_info = rect_ventana_acerca_de.top + 60
            for linea in texto_info:
                info_surf = font.render(linea, True, COLOR_TEXTO_NORMAL)
                screen.blit(info_surf, (rect_ventana_acerca_de.left + 20, y_offset_info))
                y_offset_info += info_surf.get_height() + 10 # Espacio entre líneas
            
            # Botón Cerrar para ventana Acerca de
            rect_boton_cerrar_acerca_de = pygame.Rect(
                rect_ventana_acerca_de.centerx - 50, # Centrado
                rect_ventana_acerca_de.bottom - 50, # Cerca del fondo
                100, 30 # Ancho, Alto
            )
            globals()['rect_boton_cerrar_acerca_de'] = rect_boton_cerrar_acerca_de
            
            pygame.draw.rect(screen, COLOR_BOTON_FONDO, rect_boton_cerrar_acerca_de)
            pygame.draw.rect(screen, COLOR_BOTON_BORDE, rect_boton_cerrar_acerca_de, 1) # Borde
            cerrar_acerca_surf = font.render(TEXTOS[IDIOMA]["boton_cerrar"], True, COLOR_TEXTO_NORMAL)
            screen.blit(cerrar_acerca_surf, cerrar_acerca_surf.get_rect(center=rect_boton_cerrar_acerca_de.center))
        
        # Ventana de selección de idioma
        elif mostrar_ventana_idioma:
            pygame.draw.rect(screen, COLOR_VENTANA_FONDO, rect_ventana_idioma) # Fondo
            pygame.draw.rect(screen, COLOR_BORDE_VENTANA, rect_ventana_idioma, 2) # Borde
            
            # Título de la ventana de idioma (no está en TEXTOS, así que se hardcodea o se añade)
            # Por ahora, hardcodeado para simplicidad, idealmente estaría en TEXTOS.
            titulo_idioma_surf = font.render("IDIOMA / LANGUAGE", True, COLOR_TEXTO_NORMAL)
            screen.blit(titulo_idioma_surf, (rect_ventana_idioma.centerx - titulo_idioma_surf.get_width() // 2, rect_ventana_idioma.top + 15))
            
            button_width_lang = 150
            button_height_lang = 40
            padding_y_lang = 20 # Espacio vertical entre botones
            
            # Botón Español
            rect_boton_es = pygame.Rect(
                rect_ventana_idioma.centerx - button_width_lang // 2,
                rect_ventana_idioma.top + titulo_idioma_surf.get_height() + 30, # Debajo del título
                button_width_lang,
                button_height_lang
            )
            globals()['rect_boton_es'] = rect_boton_es


            # Botón Inglés
            rect_boton_en = pygame.Rect(
                rect_ventana_idioma.centerx - button_width_lang // 2,
                rect_boton_es.bottom + padding_y_lang, # Debajo del botón español
                button_width_lang,
                button_height_lang
            )
            globals()['rect_boton_en'] = rect_boton_en
            
            # Dibujar botón Español (resaltado si es el idioma actual)
            color_fondo_es = COLOR_BOTON_FONDO_3D if IDIOMA == "es" else COLOR_BOTON_FONDO
            pygame.draw.rect(screen, color_fondo_es, rect_boton_es)
            pygame.draw.rect(screen, COLOR_BOTON_BORDE, rect_boton_es, 1) # Borde
            texto_es_surf = font.render("ESPAÑOL", True, COLOR_TEXTO_NORMAL)
            screen.blit(texto_es_surf, texto_es_surf.get_rect(center=rect_boton_es.center))
            
            # Dibujar botón Inglés (resaltado si es el idioma actual)
            color_fondo_en = COLOR_BOTON_FONDO_3D if IDIOMA == "en" else COLOR_BOTON_FONDO
            pygame.draw.rect(screen, color_fondo_en, rect_boton_en)
            pygame.draw.rect(screen, COLOR_BOTON_BORDE, rect_boton_en, 1) # Borde
            texto_en_surf = font.render("ENGLISH", True, COLOR_TEXTO_NORMAL)
            screen.blit(texto_en_surf, texto_en_surf.get_rect(center=rect_boton_en.center))
        
        # Ventana de Contraseña para Servicio de Datos
        elif mostrar_ventana_password_servicio:
            pygame.draw.rect(screen, COLOR_VENTANA_FONDO, rect_ventana_password_servicio)
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_CLARO, rect_ventana_password_servicio.topleft, rect_ventana_password_servicio.topright, 2)
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_CLARO, rect_ventana_password_servicio.topleft, rect_ventana_password_servicio.bottomleft, 2)
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_OSCURO, rect_ventana_password_servicio.bottomleft, rect_ventana_password_servicio.bottomright, 2)
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_OSCURO, rect_ventana_password_servicio.topright, rect_ventana_password_servicio.bottomright, 2)

            titulo_pwd_surf = font.render(TEXTOS[IDIOMA]["titulo_password_servicio"], True, COLOR_TEXTO_NORMAL)
            screen.blit(titulo_pwd_surf, (rect_ventana_password_servicio.centerx - titulo_pwd_surf.get_width() // 2, rect_ventana_password_servicio.top + 15))

            # Botón Cerrar 'X'
            rect_boton_cerrar_password_servicio = pygame.Rect(rect_ventana_password_servicio.right - 35, rect_ventana_password_servicio.top + 5, 30, 30)
            globals()['rect_boton_cerrar_password_servicio'] = rect_boton_cerrar_password_servicio
            pygame.draw.rect(screen, COLOR_BOTON_FONDO_3D, rect_boton_cerrar_password_servicio)
            # ... (bordes 3D para el botón cerrar)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_CLARO_3D, rect_boton_cerrar_password_servicio.topleft, rect_boton_cerrar_password_servicio.topright, 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_CLARO_3D, rect_boton_cerrar_password_servicio.topleft, pygame.math.Vector2(rect_boton_cerrar_password_servicio.left, rect_boton_cerrar_password_servicio.bottom -1), 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_OSCURO_3D, pygame.math.Vector2(rect_boton_cerrar_password_servicio.left, rect_boton_cerrar_password_servicio.bottom -1), rect_boton_cerrar_password_servicio.bottomright, 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_OSCURO_3D, pygame.math.Vector2(rect_boton_cerrar_password_servicio.right -1, rect_boton_cerrar_password_servicio.top), rect_boton_cerrar_password_servicio.bottomright, 1) # Typo corrected here
            cerrar_pwd_text = font.render("X", True, COLOR_TEXTO_NORMAL)
            screen.blit(cerrar_pwd_text, cerrar_pwd_text.get_rect(center=rect_boton_cerrar_password_servicio.center))

            # Etiqueta y campo de contraseña
            label_pwd_surf = font.render(TEXTOS[IDIOMA]["etiqueta_password"], True, COLOR_TEXTO_NORMAL)
            input_y_pwd = rect_ventana_password_servicio.top + 60
            screen.blit(label_pwd_surf, (rect_ventana_password_servicio.left + 20, input_y_pwd + 5))

            input_pwd_width = ventana_password_width - 40 - label_pwd_surf.get_width() - 10
            rect_input_password = pygame.Rect(rect_ventana_password_servicio.left + 20 + label_pwd_surf.get_width() + 5, input_y_pwd, input_pwd_width, 30)
            globals()['rect_input_password'] = rect_input_password
            
            color_fondo_input_pwd = pygame.Color('lightskyblue1') if input_password_activo else COLOR_INPUT_FONDO
            pygame.draw.rect(screen, color_fondo_input_pwd, rect_input_password)
            pygame.draw.rect(screen, COLOR_INPUT_BORDE, rect_input_password, 1)
            input_pwd_text_surf = font.render("*" * len(input_password_str), True, COLOR_TEXTO_NORMAL) # Mostrar asteriscos
            screen.blit(input_pwd_text_surf, (rect_input_password.left + 5, rect_input_password.centery - input_pwd_text_surf.get_height() // 2))

            # Mensaje de contraseña incorrecta
            if intento_password_fallido:
                error_surf = font.render(TEXTOS[IDIOMA]["password_incorrecta"], True, ROJO)
                screen.blit(error_surf, (rect_ventana_password_servicio.centerx - error_surf.get_width() // 2, rect_input_password.bottom + 10))

            # Botón Entrar
            btn_entrar_width = 100
            rect_boton_entrar_password = pygame.Rect(rect_ventana_password_servicio.centerx - btn_entrar_width // 2, rect_ventana_password_servicio.bottom - 50, btn_entrar_width, 30)
            globals()['rect_boton_entrar_password'] = rect_boton_entrar_password
            pygame.draw.rect(screen, COLOR_BOTON_FONDO, rect_boton_entrar_password)
            pygame.draw.rect(screen, COLOR_BOTON_BORDE, rect_boton_entrar_password, 1)
            entrar_surf = font.render(TEXTOS[IDIOMA]["boton_entrar"], True, COLOR_TEXTO_NORMAL)
            screen.blit(entrar_surf, entrar_surf.get_rect(center=rect_boton_entrar_password.center))

        # Ventana de configuración de servicio de datos
        elif mostrar_ventana_servicio_datos:
            pygame.draw.rect(screen, COLOR_VENTANA_FONDO, rect_ventana_servicio_datos)
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_CLARO, rect_ventana_servicio_datos.topleft, rect_ventana_servicio_datos.topright, 2)
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_CLARO, rect_ventana_servicio_datos.topleft, rect_ventana_servicio_datos.bottomleft, 2)
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_OSCURO, rect_ventana_servicio_datos.bottomleft, rect_ventana_servicio_datos.bottomright, 2)
            pygame.draw.line(screen, COLOR_BORDE_VENTANA_OSCURO, rect_ventana_servicio_datos.topright, rect_ventana_servicio_datos.bottomright, 2)

            titulo_surf = font.render(TEXTOS[IDIOMA]["titulo_servicio_datos"], True, COLOR_TEXTO_NORMAL)
            screen.blit(titulo_surf, (rect_ventana_servicio_datos.centerx - titulo_surf.get_width() // 2, rect_ventana_servicio_datos.top + 15))

            # Botón cerrar (X) - similar al de otras ventanas
            rect_boton_cerrar_servicio = pygame.Rect(rect_ventana_servicio_datos.right - 35, rect_ventana_servicio_datos.top + 5, 30, 30)
            globals()['rect_boton_cerrar_servicio'] = rect_boton_cerrar_servicio
            pygame.draw.rect(screen, COLOR_BOTON_FONDO_3D, rect_boton_cerrar_servicio)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_CLARO_3D, rect_boton_cerrar_servicio.topleft, rect_boton_cerrar_servicio.topright, 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_CLARO_3D, rect_boton_cerrar_servicio.topleft, pygame.math.Vector2(rect_boton_cerrar_servicio.left, rect_boton_cerrar_servicio.bottom -1), 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_OSCURO_3D, pygame.math.Vector2(rect_boton_cerrar_servicio.left, rect_boton_cerrar_servicio.bottom -1), rect_boton_cerrar_servicio.bottomright, 1)
            pygame.draw.line(screen, COLOR_BOTON_BORDE_OSCURO_3D, pygame.math.Vector2(rect_boton_cerrar_servicio.right -1, rect_boton_cerrar_servicio.top), rect_boton_cerrar_servicio.bottomright, 1)
            cerrar_text_servicio = font.render("X", True, COLOR_TEXTO_NORMAL)
            screen.blit(cerrar_text_servicio, cerrar_text_servicio.get_rect(center=rect_boton_cerrar_servicio.center))

            # Sección de selección de servicio
            padding_x_servicio = 20
            padding_y_servicio = 20
            current_y_servicio = rect_ventana_servicio_datos.top + titulo_surf.get_height() + 30
            
            label_servicio_surf = font.render(TEXTOS[IDIOMA]["etiqueta_servicio"], True, COLOR_TEXTO_NORMAL)
            screen.blit(label_servicio_surf, (rect_ventana_servicio_datos.left + padding_x_servicio, current_y_servicio))
            current_y_servicio += label_servicio_surf.get_height() + 10

            # Radio Button ThingSpeak
            radio_x = rect_ventana_servicio_datos.left + padding_x_servicio + RADIO_BUTTON_SIZE + 5
            rect_radio_thingspeak = pygame.Rect(radio_x, current_y_servicio, RADIO_BUTTON_SIZE * 2, RADIO_BUTTON_SIZE * 2)
            globals()['rect_radio_thingspeak'] = pygame.Rect(rect_ventana_servicio_datos.left + padding_x_servicio, current_y_servicio, ventana_servicio_width - 2*padding_x_servicio, RADIO_BUTTON_SIZE*2 + 4 ) # Rect más grande para clic
            
            pygame.draw.circle(screen, COLOR_TEXTO_NORMAL, (radio_x + RADIO_BUTTON_SIZE, current_y_servicio + RADIO_BUTTON_SIZE), RADIO_BUTTON_SIZE, 1)
            if SERVICIO_DATOS_ACTUAL == "thingspeak":
                pygame.draw.circle(screen, COLOR_TEXTO_NORMAL, (radio_x + RADIO_BUTTON_SIZE, current_y_servicio + RADIO_BUTTON_SIZE), RADIO_BUTTON_SIZE - 4)
            
            label_ts_surf = font.render(TEXTOS[IDIOMA]["opcion_thingspeak"], True, COLOR_TEXTO_NORMAL)
            screen.blit(label_ts_surf, (radio_x + RADIO_BUTTON_SIZE * 2 + 10, current_y_servicio + (RADIO_BUTTON_SIZE*2 - label_ts_surf.get_height())//2))
            current_y_servicio += RADIO_BUTTON_SIZE * 2 + padding_y_servicio

            # API Key ThingSpeak
            label_apikey_ts_surf = font.render(TEXTOS[IDIOMA]["etiqueta_apikey_thingspeak"], True, COLOR_TEXTO_NORMAL)
            screen.blit(label_apikey_ts_surf, (rect_ventana_servicio_datos.left + padding_x_servicio, current_y_servicio))
            
            input_width_servicio = ventana_servicio_width - (padding_x_servicio * 2) - label_apikey_ts_surf.get_width() - 10
            max_input_width = 200 # Limitar ancho para que no sea demasiado grande
            input_width_servicio = min(input_width_servicio, max_input_width)

            rect_input_apikey_thingspeak = pygame.Rect(rect_ventana_servicio_datos.left + padding_x_servicio + label_apikey_ts_surf.get_width() + 5, current_y_servicio -2, input_width_servicio, font.get_height() + 4)
            globals()['rect_input_apikey_thingspeak'] = rect_input_apikey_thingspeak
            
            color_fondo_input_ts = pygame.Color('lightskyblue1') if input_servicio_activo == "thingspeak" else COLOR_INPUT_FONDO
            pygame.draw.rect(screen, color_fondo_input_ts, rect_input_apikey_thingspeak)
            pygame.draw.rect(screen, COLOR_INPUT_BORDE, rect_input_apikey_thingspeak, 1)
            input_ts_surf = font.render(input_api_key_thingspeak_str, True, COLOR_TEXTO_NORMAL)
            screen.blit(input_ts_surf, (rect_input_apikey_thingspeak.left + 5, rect_input_apikey_thingspeak.top + 2))
            
            if input_servicio_activo == "thingspeak" and cursor_visible:
                cursor_x = rect_input_apikey_thingspeak.left + 5 + input_ts_surf.get_width()
                if cursor_x < rect_input_apikey_thingspeak.right - 2:
                    pygame.draw.line(screen, COLOR_TEXTO_NORMAL, (cursor_x, rect_input_apikey_thingspeak.top + 4), (cursor_x, rect_input_apikey_thingspeak.bottom - 4), 1)

            current_y_servicio += label_apikey_ts_surf.get_height() + padding_y_servicio


            # Radio Button Google Cloud
            rect_radio_google_cloud = pygame.Rect(radio_x, current_y_servicio, RADIO_BUTTON_SIZE * 2, RADIO_BUTTON_SIZE * 2)
            globals()['rect_radio_google_cloud'] = pygame.Rect(rect_ventana_servicio_datos.left + padding_x_servicio, current_y_servicio, ventana_servicio_width - 2*padding_x_servicio, RADIO_BUTTON_SIZE*2 + 4)

            pygame.draw.circle(screen, COLOR_TEXTO_NORMAL, (radio_x + RADIO_BUTTON_SIZE, current_y_servicio + RADIO_BUTTON_SIZE), RADIO_BUTTON_SIZE, 1)
            if SERVICIO_DATOS_ACTUAL == "azure_sql":
                pygame.draw.circle(screen, COLOR_TEXTO_NORMAL, (radio_x + RADIO_BUTTON_SIZE, current_y_servicio + RADIO_BUTTON_SIZE), RADIO_BUTTON_SIZE - 4)

            label_gc_surf = font.render(TEXTOS[IDIOMA]["opcion_google_cloud"], True, COLOR_TEXTO_NORMAL)
            screen.blit(label_gc_surf, (radio_x + RADIO_BUTTON_SIZE * 2 + 10, current_y_servicio + (RADIO_BUTTON_SIZE*2 - label_gc_surf.get_height())//2))
            current_y_servicio += RADIO_BUTTON_SIZE * 2 + padding_y_servicio

            # API Key Google Cloud
            label_apikey_gc_surf = font.render(TEXTOS[IDIOMA]["etiqueta_apikey_google_cloud"], True, COLOR_TEXTO_NORMAL)
            screen.blit(label_apikey_gc_surf, (rect_ventana_servicio_datos.left + padding_x_servicio, current_y_servicio))
            
            rect_input_apikey_google_cloud = pygame.Rect(rect_ventana_servicio_datos.left + padding_x_servicio + label_apikey_gc_surf.get_width() + 5, current_y_servicio -2, input_width_servicio, font.get_height() + 4)
            globals()['rect_input_apikey_google_cloud'] = rect_input_apikey_google_cloud

            color_fondo_input_gc = pygame.Color('lightskyblue1') if input_servicio_activo == "google_cloud" else COLOR_INPUT_FONDO
            pygame.draw.rect(screen, color_fondo_input_gc, rect_input_apikey_google_cloud)
            pygame.draw.rect(screen, COLOR_INPUT_BORDE, rect_input_apikey_google_cloud, 1)
            input_gc_surf = font.render(input_api_key_google_cloud_str, True, COLOR_TEXTO_NORMAL)
            screen.blit(input_gc_surf, (rect_input_apikey_google_cloud.left + 5, rect_input_apikey_google_cloud.top + 2))

            if input_servicio_activo == "google_cloud" and cursor_visible:
                cursor_x = rect_input_apikey_google_cloud.left + 5 + input_gc_surf.get_width()
                if cursor_x < rect_input_apikey_google_cloud.right - 2:
                    pygame.draw.line(screen, COLOR_TEXTO_NORMAL, (cursor_x, rect_input_apikey_google_cloud.top + 4), (cursor_x, rect_input_apikey_google_cloud.bottom - 4), 1)
            
            current_y_servicio += label_apikey_gc_surf.get_height() + padding_y_servicio

            # Contraseña Azure SQL
            label_password_azure_surf = font.render(TEXTOS[IDIOMA]["etiqueta_password_azure"], True, COLOR_TEXTO_NORMAL)
            screen.blit(label_password_azure_surf, (rect_ventana_servicio_datos.left + padding_x_servicio, current_y_servicio))
            
            rect_input_password_azure = pygame.Rect(rect_ventana_servicio_datos.left + padding_x_servicio + label_password_azure_surf.get_width() + 5, current_y_servicio -2, input_width_servicio, font.get_height() + 4)
            globals()['rect_input_password_azure'] = rect_input_password_azure

            color_fondo_input_pwd = pygame.Color('lightskyblue1') if input_servicio_activo == "password_azure" else COLOR_INPUT_FONDO
            pygame.draw.rect(screen, color_fondo_input_pwd, rect_input_password_azure)
            pygame.draw.rect(screen, COLOR_INPUT_BORDE, rect_input_password_azure, 1)
            input_pwd_surf = font.render("*" * len(input_password_azure_str), True, COLOR_TEXTO_NORMAL)
            screen.blit(input_pwd_surf, (rect_input_password_azure.left + 5, rect_input_password_azure.top + 2))

            if input_servicio_activo == "password_azure" and cursor_visible:
                cursor_x = rect_input_password_azure.left + 5 + input_pwd_surf.get_width()
                if cursor_x < rect_input_password_azure.right - 2:
                    pygame.draw.line(screen, COLOR_TEXTO_NORMAL, (cursor_x, rect_input_password_azure.top + 4), (cursor_x, rect_input_password_azure.bottom - 4), 1)

            current_y_servicio += label_password_azure_surf.get_height() + padding_y_servicio + 10 # Espacio antes de botones

            # Botones Guardar y Mostrar Consola
            button_servicio_width = 150 # Un poco más ancho para "Mostrar Consola"
            button_servicio_height = 40
            espacio_entre_botones_servicio = 10

            y_botones_servicio = rect_ventana_servicio_datos.bottom - button_servicio_height - padding_y_servicio

            # Botón Guardar (a la izquierda)
            rect_boton_guardar_servicio = pygame.Rect(
                rect_ventana_servicio_datos.centerx - button_servicio_width - espacio_entre_botones_servicio // 2,
                y_botones_servicio,
                button_servicio_width, button_servicio_height
            )
            globals()['rect_boton_guardar_servicio'] = rect_boton_guardar_servicio
            pygame.draw.rect(screen, COLOR_BOTON_FONDO, rect_boton_guardar_servicio)
            pygame.draw.rect(screen, COLOR_BOTON_BORDE, rect_boton_guardar_servicio, 1)
            guardar_servicio_surf = font.render(TEXTOS[IDIOMA]["boton_guardar"], True, COLOR_TEXTO_NORMAL)
            screen.blit(guardar_servicio_surf, guardar_servicio_surf.get_rect(center=rect_boton_guardar_servicio.center))

            # Nuevo Botón Mostrar Consola (a la derecha)
            rect_boton_mostrar_consola_servicio = pygame.Rect(
                rect_ventana_servicio_datos.centerx + espacio_entre_botones_servicio // 2,
                y_botones_servicio,
                button_servicio_width, button_servicio_height
            )
            globals()['rect_boton_mostrar_consola_servicio'] = rect_boton_mostrar_consola_servicio
            pygame.draw.rect(screen, COLOR_BOTON_FONDO, rect_boton_mostrar_consola_servicio)
            pygame.draw.rect(screen, COLOR_BOTON_BORDE, rect_boton_mostrar_consola_servicio, 1)
            mostrar_consola_servicio_surf = font.render(TEXTOS[IDIOMA]["boton_mostrar_consola"], True, COLOR_TEXTO_NORMAL)
            screen.blit(mostrar_consola_servicio_surf, mostrar_consola_servicio_surf.get_rect(center=rect_boton_mostrar_consola_servicio.center))

       
        elif mostrar_ventana_consola_datos:
            # Usar una fuente estándar para la consola, o definir una específica
            font_para_consola = pygame.font.Font(None, 22) # Puede ser la misma que font_bar_herramientas
            draw_console_window(screen, font_para_consola, datos_consola_buffer, copy_success_message)
        
        elif mostrar_ventana_test_serial:
            font_para_test = pygame.font.Font(None, 22)
            draw_test_window(screen, font_para_test, datos_test_serial_buffer, copy_success_message)


        pygame.display.flip()
        reloj.tick(60) # Limitar a 60 FPS
    
    # Limpieza al salir del bucle principal
    if serial_port_available and ser is not None:
        if ser.is_open:
            ser.close()
    pygame.quit()


# --- Nueva función para dibujar la ventana de la consola ---
def draw_console_window(screen, font_console, buffer_datos, copy_message=None):
    global rect_ventana_consola_datos, rect_boton_cerrar_consola_datos, rect_boton_copiar_consola # Necesario para guardar los rects

    ventana_consola_width = 800 # Aumentado de 600 a 800
    ventana_consola_height = 400
    # Centrar horizontalmente
    ventana_consola_x = (screen.get_width() - ventana_consola_width) // 2
    # Posicionar en la parte inferior con un pequeño margen
    margen_inferior_consola = 20 # Píxeles desde el borde inferior
    ventana_consola_y = screen.get_height() - ventana_consola_height - margen_inferior_consola
    rect_ventana_consola_datos = pygame.Rect(ventana_consola_x, ventana_consola_y, ventana_consola_width, ventana_consola_height)

    # Colores (pueden ser constantes globales o pasadas)
    COLOR_FONDO_CONSOLA = (30, 30, 30) # Gris oscuro
    COLOR_BORDE_CONSOLA = (80, 80, 80)
    COLOR_TEXTO_CONSOLA = (200, 200, 200) # Gris claro
    COLOR_BOTON_CERRAR_CONSOLA_FONDO = (50, 50, 50)

    # Dibujar fondo y borde de la ventana
    pygame.draw.rect(screen, COLOR_FONDO_CONSOLA, rect_ventana_consola_datos)
    pygame.draw.rect(screen, COLOR_BORDE_CONSOLA, rect_ventana_consola_datos, 2)

    # Título de la ventana
    titulo_consola_surf = font_console.render("Consola de Datos", True, COLOR_TEXTO_CONSOLA)
    screen.blit(titulo_consola_surf, (rect_ventana_consola_datos.centerx - titulo_consola_surf.get_width() // 2, rect_ventana_consola_datos.top + 10))

    # Botón cerrar (X)
    rect_boton_cerrar_consola_datos = pygame.Rect(rect_ventana_consola_datos.right - 30, rect_ventana_consola_datos.top + 5, 25, 25)
    pygame.draw.rect(screen, COLOR_BOTON_CERRAR_CONSOLA_FONDO, rect_boton_cerrar_consola_datos)
    cerrar_text_consola = font_console.render("X", True, COLOR_TEXTO_CONSOLA)
    screen.blit(cerrar_text_consola, cerrar_text_consola.get_rect(center=rect_boton_cerrar_consola_datos.center))

    # Área de texto para los datos
    area_texto_x = rect_ventana_consola_datos.left + 10
    area_texto_y = rect_ventana_consola_datos.top + titulo_consola_surf.get_height() + 20
    area_texto_width = rect_ventana_consola_datos.width - 20
    area_texto_height = rect_ventana_consola_datos.height - (titulo_consola_surf.get_height() + 30) - 10 # -10 para padding inferior

    # Botón Copiar
    btn_copiar_width = 100
    btn_copiar_height = 30
    rect_boton_copiar_consola = pygame.Rect(
        rect_ventana_consola_datos.left + 10, 
        rect_ventana_consola_datos.bottom - btn_copiar_height - 10, 
        btn_copiar_width, 
        btn_copiar_height
    )
    pygame.draw.rect(screen, COLOR_BOTON_CERRAR_CONSOLA_FONDO, rect_boton_copiar_consola)
    copiar_text_surf = font_console.render("Copiar", True, COLOR_TEXTO_CONSOLA)
    screen.blit(copiar_text_surf, copiar_text_surf.get_rect(center=rect_boton_copiar_consola.center))

    # Mensaje de confirmación de copiado
    if copy_message:
        copy_msg_surf = font_console.render(copy_message, True, VERDE)
        screen.blit(copy_msg_surf, (rect_boton_copiar_consola.right + 10, rect_boton_copiar_consola.centery - copy_msg_surf.get_height() // 2))

    # Dibujar los datos del buffer (las últimas N líneas)
    line_height = font_console.get_linesize()
    max_lines_display = area_texto_height // line_height
    
    # Mostrar las últimas 'max_lines_display' líneas del buffer
    start_index = max(0, len(buffer_datos) - max_lines_display)
    
    current_y_text = area_texto_y
    for i in range(start_index, len(buffer_datos)):
        linea_texto = buffer_datos[i]
        texto_surf = font_console.render(linea_texto, True, COLOR_TEXTO_CONSOLA)
        screen.blit(texto_surf, (area_texto_x, current_y_text))
        current_y_text += line_height
        if current_y_text + line_height > area_texto_y + area_texto_height: # No dibujar fuera del área
            break
# --- Fin de la nueva función ---
def draw_test_window(screen, font_test, buffer_datos, copy_message=None):
    """Dibuja la ventana de visualización de datos de prueba del puerto serie."""
    global rect_ventana_test_serial, rect_boton_cerrar_test_serial, rect_boton_copiar_test_serial

    ventana_test_width = 600
    ventana_test_height = 400
    ventana_test_x = (screen.get_width() - ventana_test_width) // 2
    ventana_test_y = (screen.get_height() - ventana_test_height) // 2
    rect_ventana_test_serial = pygame.Rect(ventana_test_x, ventana_test_y, ventana_test_width, ventana_test_height)

    COLOR_FONDO_TEST = (30, 30, 30)
    COLOR_BORDE_TEST = (80, 80, 80)
    COLOR_TEXTO_TEST = (0, 255, 0) # Texto verde para look "terminal"
    COLOR_BOTON_FONDO_TEST = (50, 50, 50)

    pygame.draw.rect(screen, COLOR_FONDO_TEST, rect_ventana_test_serial)
    pygame.draw.rect(screen, COLOR_BORDE_TEST, rect_ventana_test_serial, 2)

    titulo_test_surf = font_test.render("Datos del Puerto Serie (Test)", True, COLOR_TEXTO_TEST)
    screen.blit(titulo_test_surf, (rect_ventana_test_serial.centerx - titulo_test_surf.get_width() // 2, rect_ventana_test_serial.top + 10))

    rect_boton_cerrar_test_serial = pygame.Rect(rect_ventana_test_serial.right - 30, rect_ventana_test_serial.top + 5, 25, 25)
    pygame.draw.rect(screen, COLOR_BOTON_FONDO_TEST, rect_boton_cerrar_test_serial)
    cerrar_text_test = font_test.render("X", True, COLOR_TEXTO_TEST)
    screen.blit(cerrar_text_test, cerrar_text_test.get_rect(center=rect_boton_cerrar_test_serial.center))
    
    # Botón Copiar
    btn_copiar_width = 100
    btn_copiar_height = 30
    rect_boton_copiar_test_serial = pygame.Rect(
        rect_ventana_test_serial.left + 10,
        rect_ventana_test_serial.bottom - btn_copiar_height - 10,
        btn_copiar_width,
        btn_copiar_height
    )
    pygame.draw.rect(screen, COLOR_BOTON_FONDO_TEST, rect_boton_copiar_test_serial)
    copiar_text_surf = font_test.render("Copiar", True, COLOR_TEXTO_TEST)
    screen.blit(copiar_text_surf, copiar_text_surf.get_rect(center=rect_boton_copiar_test_serial.center))

    # Mensaje de confirmación de copiado
    if copy_message:
        copy_msg_surf = font_test.render(copy_message, True, VERDE)
        screen.blit(copy_msg_surf, (rect_boton_copiar_test_serial.right + 10, rect_boton_copiar_test_serial.centery - copy_msg_surf.get_height() // 2))

    area_texto_y = rect_ventana_test_serial.top + titulo_test_surf.get_height() + 20
    area_texto_height = rect_ventana_test_serial.height - (titulo_test_surf.get_height() + 30) - (btn_copiar_height + 20)
    
    line_height = font_test.get_linesize()
    max_lines_display = area_texto_height // line_height
    start_index = max(0, len(buffer_datos) - max_lines_display)

    current_y_text = area_texto_y
    for i in range(start_index, len(buffer_datos)):
        linea_texto = buffer_datos[i]
        texto_surf = font_test.render(linea_texto, True, COLOR_TEXTO_TEST)
        screen.blit(texto_surf, (rect_ventana_test_serial.left + 10, current_y_text))
        current_y_text += line_height

# Punto de entrada del programa
if __name__ == "__main__":
    main()














































