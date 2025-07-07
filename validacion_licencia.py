# genera_licencias.py (MANTÉN ESTE ARCHIVO EN SECRETO)
import hashlib
from datetime import datetime, timedelta

def generar_licencia(hw_id, dias_validez=1095):
    # Firma única basada en HW_ID + Fecha + Clave maestra
    clave_secreta = "Tasa2025"  # ¡Cámbiala!
    fecha_expira = (datetime.now() + timedelta(days=dias_validez)).strftime("%Y-%m-%d")
    
    # Genera hash de seguridad
    hash_licencia = hashlib.sha256(
        f"{hw_id}{fecha_expira}{clave_secreta}".encode()
    ).hexdigest()[:16].upper()
    
    licencia = f"{hw_id[:4]}-{hash_licencia}-{fecha_expira}"
    return licencia

# Ejemplo: Generar licencia para un cliente
hw_id_cliente = "A1B2C3D4"  # Pídele este ID al usuario
licencia = generar_licencia(hw_id_cliente, dias_validez=1095)
print(f"Licencia generada: {licencia}")  # Ej: "A1B2-8F3E21D5-2024-12-31"