import serial
import time
import requests
import json

# --- Funciones de parseo NMEA (copiadas de clinometro.py) ---
def parse_pfec_gpatt(sentence):
    global ts_pitch_float, ts_roll_float
    try:
        parts = sentence.split(',')
        if len(parts) >= 5 and parts[1] == "GPatt":
            raw_pitch = parts[3]
            try:
                ts_pitch_float = float(raw_pitch)
            except:
                ts_pitch_float = 0.0
            raw_roll_part = parts[4].split('*')[0]
            try:
                ts_roll_float = float(raw_roll_part)
            except ValueError:
                ts_roll_float = 0.0
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia PFEC,GPatt: {e}. Sentencia: {sentence}")
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

def parse_gga(sentence):
    global ts_altitude_float, ts_lat_decimal, ts_lon_decimal
    try:
        parts = sentence.split(',')
        if len(parts) > 10 and parts[9]:
            alt_val_str = parts[9]
            if alt_val_str:
                try:
                    ts_altitude_float = float(alt_val_str)
                except ValueError:
                    ts_altitude_float = 0.0
            else:
                ts_altitude_float = 0.0

            lat_raw_val = parts[2]
            lat_dir = parts[3]
            lon_raw_val = parts[4]
            lon_dir = parts[5]
            ts_lat_decimal = convertir_coord(lat_raw_val, lat_dir, is_longitude=False)
            ts_lon_decimal = convertir_coord(lon_raw_val, lon_dir, is_longitude=True)

    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia GGA: {e}. Sentencia: {sentence}")
    except Exception as e:
        print(f"Error inesperado en parse_gga: {e}. Sentencia: {sentence}")

def parse_vtg(sentence):
    global ts_speed_float
    try:
        parts = sentence.split(',')
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
            except:
                pass
        ts_speed_float = temp_speed_float
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia VTG: {e}. Sentencia: {sentence}")
    except Exception as e:
        print(f"Error inesperado en parse_vtg: {e}. Sentencia: {sentence}")

def parse_hdt(sentence):
    global ts_heading_float
    try:
        parts = sentence.split(',')
        if len(parts) > 1 and parts[1]:
            heading_val_str = parts[1]
            try:
                ts_heading_float = float(heading_val_str)
            except:
                ts_heading_float = 0.0
    except (IndexError, ValueError) as e:
        print(f"Error parseando sentencia HDT: {e}. Sentencia: {sentence}")
    except Exception as e:
        print(f"Error inesperado en parse_hdt: {e}. Sentencia: {sentence}")

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

def enviar_thingspeak():
    payload = {
        'api_key': API_KEY_THINGSPEAK,
        'field1': ts_pitch_float,
        'field2': ts_roll_float,
        'field3': ts_lat_decimal,
        'field4': ts_lon_decimal,
        'field5': ts_speed_float,
        'field6': ts_heading_float,
        'field7': ts_timestamp_str,
        'field8': ts_altitude_float
    }
    try:
        r = requests.get(THINGSPEAK_URL, params=payload)
        if r.status_code == 200:
            print(f"[OK] ThingSpeak OK: {ts_timestamp_str} (Alt: {ts_altitude_float})")
        else:
            print(f"[ERROR] ThingSpeak ERR: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[ERROR] ThingSpeak Conn. ERR: {e}")

# --- Variables Globales ---
API_KEY_THINGSPEAK = "5TRR6EXF6N5CZF54"
THINGSPEAK_URL = "https://api.thingspeak.com/update"
INTERVALO_ENVIO_DATOS_S = 15

ts_pitch_float = 0.0
ts_roll_float = 0.0
ts_lat_decimal = 0.0
ts_lon_decimal = 0.0
ts_speed_float = 0.0
ts_heading_float = 0.0
ts_timestamp_str = "N/A"
ts_altitude_float = 0.0

def main():
    print("Starting main loop...")
    # Simulated NMEA data
    nmea_data = [
        "$PFEC,GPatt,103320.30,345.3,0.1,6.4*4C",
        "$GPGGA,103320,1202.8059,S,07728.4752,W,1,09,0.9,12.3,M,-34.2,M,,*5A",
        "$GPVTG,0.0,T,356.9,M,6.8,N,12.5,K,A*01",
        "$GPHDT,345.3,T*01",
        "$GPZDA,103320.30,19,07,2025,00,00*64"
    ]

    print("Processing NMEA data...")
    for line in nmea_data:
        if line.startswith('$PFEC,GPatt'):
            parse_pfec_gpatt(line)
        elif line.startswith('$GPGGA') or line.startswith('$GNGGA'):
            parse_gga(line)
        elif line.startswith('$GPVTG') or line.startswith('$GNVTG'):
            parse_vtg(line)
        elif line.startswith('$GPHDT') or line.startswith('$GNHDT'):
            parse_hdt(line)
        elif line.startswith('$GPZDA') or line.startswith('$GNZDA'):
            parse_gpzda(line)
    print("Finished processing NMEA data.")

    print("--- Enviando datos ---")
    print(f"Valores: P:{ts_pitch_float}, R:{ts_roll_float}, Lat:{ts_lat_decimal}, Lon:{ts_lon_decimal}, Spd:{ts_speed_float}, Hdg:{ts_heading_float}, TS:{ts_timestamp_str}, Alt:{ts_altitude_float}")
    enviar_thingspeak()

if __name__ == "__main__":
    main()
