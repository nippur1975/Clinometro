# license_manager.py

import json
import os
import hashlib
import uuid

LICENSE_FILE = "license.json"
# Una "clave secreta" simple para este ejemplo. En una aplicación real, esto debería ser más robusto.
SECRET_KEY = "my_super_secret_clinometer_key"

def generate_license_key(user_identifier: str) -> str:
    """
    Genera una clave de licencia simple basada en un identificador de usuario y una clave secreta.
    """
    # Crear un hash combinado del identificador del usuario y la clave secreta
    # Esto es un ejemplo simple, no criptográficamente seguro para producción real.
    m = hashlib.sha256()
    m.update(user_identifier.encode('utf-8'))
    m.update(SECRET_KEY.encode('utf-8'))
    # Devolvemos los primeros 32 caracteres del hash hexadecimal como clave de licencia
    return m.hexdigest()[:32]

def store_license(license_key: str, user_identifier: str):
    """
    Almacena la clave de licencia y el identificador del usuario en un archivo.
    """
    data = {
        "license_key": license_key,
        "user_identifier": user_identifier # Podría ser un email, nombre de usuario, etc.
    }
    try:
        with open(LICENSE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Licencia guardada en {LICENSE_FILE}")
    except IOError:
        print(f"Error al guardar la licencia en {LICENSE_FILE}")

def load_license_data() -> dict | None:
    """
    Carga los datos de la licencia desde el archivo.
    Devuelve un diccionario con los datos o None si el archivo no existe o hay un error.
    """
    if not os.path.exists(LICENSE_FILE):
        return None
    try:
        with open(LICENSE_FILE, 'r') as f:
            data = json.load(f)
            return data
    except (IOError, json.JSONDecodeError):
        return None

def verify_license(provided_license_key: str, user_identifier: str) -> bool:
    """
    Verifica si la clave de licencia proporcionada es válida para el identificador de usuario.
    """
    expected_license_key = generate_license_key(user_identifier)
    return provided_license_key == expected_license_key

def check_license_status() -> tuple[bool, str | None, str | None]:
    """
    Comprueba el estado de la licencia almacenada.
    Devuelve:
        - bool: True si la licencia es válida, False en caso contrario.
        - str | None: La clave de licencia si existe y es válida.
        - str | None: El identificador de usuario si existe.
    """
    license_data = load_license_data()
    if not license_data:
        return False, None, None

    stored_key = license_data.get("license_key")
    stored_identifier = license_data.get("user_identifier")

    if not stored_key or not stored_identifier:
        return False, None, None

    if verify_license(stored_key, stored_identifier):
        return True, stored_key, stored_identifier
    else:
        return False, stored_key, stored_identifier # Devuelve la clave e identificador aunque no coincidan

def get_machine_identifier() -> str:
    """
    Genera un identificador de máquina simple (UUID basado en la MAC address).
    Esto es un ejemplo, puede no ser único o estable en todos los sistemas.
    """
    # Intenta obtener la MAC address de forma estándar
    mac_num = uuid.getnode()
    if (mac_num == uuid.getnode() and mac_num != 0): # Verifica si se obtuvo una MAC válida
        mac_address = ':'.join(('%012X' % mac_num)[i:i+2] for i in range(0, 12, 2))
        return mac_address
    else:
        # Fallback si no se puede obtener la MAC address (ej. en algunos contenedores o VMs)
        # Generar un UUID aleatorio y almacenarlo para consistencia en esta sesión/instalación.
        # Para persistencia real, este UUID debería guardarse en algún lugar.
        # Por simplicidad, aquí generamos uno nuevo cada vez si la MAC falla.
        # En un escenario real, se guardaría en un archivo de configuración del usuario.
        print("Advertencia: No se pudo obtener la MAC address. Usando UUID aleatorio como identificador.")
        return str(uuid.uuid4())


if __name__ == "__main__":
    # Ejemplo de uso (esto se ejecutaría si corres license_manager.py directamente)

    print("--- Ejemplo de Gestión de Licencias ---")

    # Identificador único para esta instancia/usuario.
    # Podría ser un email, un nombre de usuario, o un ID de máquina.
    # Para este ejemplo, usaremos un identificador de máquina.
    machine_id = get_machine_identifier()
    print(f"Identificador de máquina para licencia: {machine_id}")

    # Comprobar estado de la licencia existente
    is_valid, current_key, current_id = check_license_status()
    if is_valid:
        print(f"Licencia válida encontrada para {current_id}: {current_key}")
    else:
        print("No se encontró una licencia válida o la licencia existente es incorrecta.")

        # Simular la generación y almacenamiento de una nueva licencia
        print("\nGenerando una nueva licencia para este identificador...")
        new_license_key = generate_license_key(machine_id)
        store_license(new_license_key, machine_id)
        print(f"Nueva clave de licencia generada: {new_license_key}")
        print(f"Esta clave debe ser proporcionada al usuario '{machine_id}' para activar el software.")

        # Verificar la licencia recién almacenada
        is_valid_after_store, stored_key_after, stored_id_after = check_license_status()
        if is_valid_after_store:
            print(f"Verificación exitosa de la nueva licencia para {stored_id_after}: {stored_key_after}")
        else:
            print("Error: La licencia recién almacenada no pudo ser verificada.")

    print("\n--- Prueba de verificación con una clave y un ID ---")
    test_id = "test_user@example.com"
    test_key_correct = generate_license_key(test_id)
    test_key_incorrect = "incorrect_license_key_12345"

    if verify_license(test_key_correct, test_id):
        print(f"ÉXITO: La clave '{test_key_correct}' ES válida para el usuario '{test_id}'.")
    else:
        print(f"FALLO: La clave '{test_key_correct}' NO ES válida para el usuario '{test_id}'.")

    if verify_license(test_key_incorrect, test_id):
        print(f"FALLO (esperado): La clave '{test_key_incorrect}' ES válida para el usuario '{test_id}'.")
    else:
        print(f"ÉXITO (esperado): La clave '{test_key_incorrect}' NO ES válida para el usuario '{test_id}'.")
    
    print("\n--- Prueba de carga de licencia ---")
    loaded_data = load_license_data()
    if loaded_data:
        print(f"Datos de licencia cargados: {loaded_data}")
    else:
        print("No se pudo cargar el archivo de licencia o no existe.")

    # Para probar, puedes borrar 'license.json' y volver a ejecutar.
    # También puedes modificar 'license.json' para simular una licencia inválida.
    # Por ejemplo, cambia la 'license_key' o 'user_identifier'.
    # Luego ejecuta check_license_status() (indirectamente a través de este script).
    # Y verás el mensaje "No se encontró una licencia válida..."
    # O si solo cambias la clave, "La licencia existente es incorrecta."
    
    # Ejemplo de cómo un usuario ingresaría su licencia
    # (esto iría en la aplicación principal)
    # user_provided_key = input("Ingrese su clave de licencia: ")
    # current_machine_id = get_machine_identifier() # El identificador que la app usa
    # if verify_license(user_provided_key, current_machine_id):
    #     print("Licencia activada exitosamente!")
    #     store_license(user_provided_key, current_machine_id) # Guardar la licencia verificada
    # else:
    #     print("La clave de licencia no es válida para este equipo/usuario.")

# Consideraciones para una implementación más robusta:
# 1. Cifrado del archivo de licencia: Para evitar que se modifique fácilmente.
# 2. Ofuscación del código: Para dificultar la ingeniería inversa.
# 3. Mecanismos anti-manipulación más fuertes: Detectar si el archivo de licencia ha sido alterado.
# 4. Activación en línea: Validar la licencia contra un servidor central.
# 5. Licencias basadas en hardware más complejas: Usar múltiples identificadores de hardware.
# 6. Manejo de errores y excepciones más detallado.
# 7. Pruebas unitarias exhaustivas.
# 8. Considerar la experiencia del usuario (UX) para el proceso de activación.
# 9. SECRET_KEY no debería estar hardcodeada así en una app de producción. Debería ser gestionada de forma segura.
# 10. El user_identifier (o machine_identifier) debería ser consistente. La forma actual de get_machine_identifier
#     puede variar o fallar. Una solución más robusta podría implicar guardar el primer identificador
#     generado o pedir al usuario un identificador único (como email) durante la "compra" o "registro"
#     de la licencia.
# 11. Si se usa un identificador de máquina, informar al usuario que la licencia está atada a esa máquina.
# 12. Permitir un número limitado de activaciones o un proceso de desactivación/transferencia de licencia.
# 13. Para licencias con caducidad, se necesitaría añadir lógica de fechas y validación de las mismas.
