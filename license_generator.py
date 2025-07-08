import pygame
import json
import os
import hashlib
import uuid
from pygame.locals import *

# Configuración de Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gestor de Licencias - Clinómetro")

# Debug: Mostrar ubicación actual
print(f"Directorio del script: {os.path.dirname(os.path.abspath(__file__))}")
print(f"Directorio de trabajo: {os.getcwd()}")

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (0, 0, 139)
RED = (255, 0, 0)
GREEN = (0, 128, 0)

# Fuentes
font_large = pygame.font.SysFont('Arial', 32)
font_medium = pygame.font.SysFont('Arial', 24)
font_small = pygame.font.SysFont('Arial', 18)

# Constantes de licencia (RUTAS ABSOLUTAS)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LICENSE_FOLDER = os.path.join(SCRIPT_DIR, "licenses")
LICENSE_FILE = os.path.join(LICENSE_FOLDER, "license.json")
SECRET_KEY = "my_super_secret_clinometer_key"

# Función para verificar permisos
def check_directory_permissions():
    try:
        test_file = os.path.join(LICENSE_FOLDER, "test.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✔ Permisos de escritura verificados")
        return True
    except Exception as e:
        print(f"✖ Error de permisos: {e}")
        return False

# Crear carpeta licenses con verificación robusta
try:
    os.makedirs(LICENSE_FOLDER, exist_ok=True)
    print(f"✔ Directorio de licencias: {LICENSE_FOLDER}")
    
    if not check_directory_permissions():
        raise SystemExit("Error: Sin permisos de escritura en el directorio")
except Exception as e:
    print(f"✖ Error crítico al crear directorio: {e}")
    print(f"Ruta intentada: {LICENSE_FOLDER}")
    raise SystemExit("No se puede continuar sin directorio de licencias")

class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = BLACK
        self.text = text
        self.txt_surface = font_medium.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = DARK_BLUE if self.active else BLACK
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.txt_surface = font_medium.render(self.text, True, self.color)
        return False

    def update(self):
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, 2)
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))

class Button:
    def __init__(self, x, y, w, h, text, color=LIGHT_BLUE, hover_color=DARK_BLUE):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.hover_color = hover_color
        self.text = text
        self.txt_surface = font_medium.render(text, True, BLACK)
        self.is_hovered = False

    def draw(self, screen):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        text_rect = self.txt_surface.get_rect(center=self.rect.center)
        screen.blit(self.txt_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

def generate_license_key(user_identifier: str) -> str:
    m = hashlib.sha256()
    m.update(user_identifier.encode('utf-8'))
    m.update(SECRET_KEY.encode('utf-8'))
    return m.hexdigest()[:32]

def store_license(license_key: str, user_identifier: str):
    data = {
        "license_key": license_key,
        "machine_identifier": user_identifier  # Cambiado de user_identifier
    }
    try:
        # Verificación adicional antes de guardar
        if not os.path.exists(LICENSE_FOLDER):
            os.makedirs(LICENSE_FOLDER)
            
        with open(LICENSE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Licencia guardada en: {os.path.abspath(LICENSE_FILE)}")
        return True
    except Exception as e:
        print(f"Error al guardar licencia. Ruta intentada: {os.path.abspath(LICENSE_FILE)}")
        print(f"Error detallado: {e}")
        return False

def load_license_data() -> dict | None:
    if not os.path.exists(LICENSE_FILE):
        print(f"No existe archivo de licencia en: {os.path.abspath(LICENSE_FILE)}")
        return None
    try:
        with open(LICENSE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar licencia: {e}")
        return None

def verify_license(provided_license_key: str, user_identifier: str) -> bool:
    expected_license_key = generate_license_key(user_identifier)
    return provided_license_key == expected_license_key

def get_machine_identifier() -> str: # Esta función ahora es redundante, pero la dejamos por si se usa en otro lado.
    mac_num = uuid.getnode()
    if (mac_num == uuid.getnode() and mac_num != 0):
        return ':'.join(('%012X' % mac_num)[i:i+2] for i in range(0, 12, 2))
    else:
        return str(uuid.uuid4())

# --- Funciones de Licencia (adaptadas de main.py para consistencia) ---
def get_machine_specific_identifier() -> tuple[str, str]:
    """
    Genera un identificador de máquina completo (para la lógica de licencia) 
    y un ID corto para mostrar al usuario.
    """
    try:
        mac_num = uuid.getnode()
        if mac_num != uuid.getnode() or mac_num == 0: # Comprobación más robusta
            try:
                import socket # Asegurar que socket está importado aquí también
                hostname_hash = hashlib.sha1(socket.gethostname().encode()).hexdigest()
                internal_id_str = hostname_hash
                print("Advertencia: No se pudo obtener la MAC address de forma fiable. Usando ID derivado del hostname.")
            except:
                internal_id_str = str(uuid.uuid4())
                print("Advertencia: No se pudo obtener MAC ni ID de hostname. Usando UUID aleatorio como identificador interno.")
        else:
            internal_id_str = ':'.join(('%012X' % mac_num)[i:i+2] for i in range(0, 12, 2))
    except Exception as e:
        print(f"Error obteniendo MAC/UUID: {e}. Usando UUID aleatorio como identificador interno.")
        internal_id_str = str(uuid.uuid4())

    display_id = hashlib.sha1(internal_id_str.encode('utf-8')).hexdigest()[:6].upper()
    
    return internal_id_str, display_id

def license_screen():
    # Obtener ambos IDs: el interno para la lógica, el display para mostrar al usuario.
    current_internal_id, current_display_id = get_machine_specific_identifier()
    
    # El InputBox mostrará el display_id por defecto, pero el usuario puede cambiarlo si genera para otra máquina.
    # Sin embargo, para la lógica interna, necesitaremos el internal_id si el usuario NO lo cambia.
    # Si el usuario edita el campo, asumimos que está ingresando un display_id o un internal_id de otra máquina.
    # Para simplificar, la licencia se generará basada en el TEXTO EXACTO del input_box.
    # Y se guardará ese mismo texto como machine_identifier.
    # PERO, para el caso por defecto (cuando el usuario no toca el input),
    # queremos que se genere y guarde usando el internal_id de la máquina actual.
    # Esto crea una ambigüedad.
    # Solución: El input box se puede inicializar con el display_id.
    # Si el usuario quiere generar para OTRA máquina, debe conocer el INTERNAL ID de esa otra máquina
    # y pegarlo en el input_box.
    # Por lo tanto, el InputBox debería ser para el INTERNAL_ID o el ID que se usará para generar.
    # Vamos a mostrar el display_id, pero al generar/guardar, usaremos el internal_id correspondiente
    # a la máquina actual si el texto del inputbox sigue siendo el display_id de la máquina actual.
    # Si el usuario lo modifica, ese texto modificado se usará como el identificador.
    # El InputBox se inicializa con el display_id para que el usuario lo vea.
    input_box = InputBox(WIDTH//2 - 150, 200, 300, 32, current_display_id) # InputBox muestra current_display_id

    generate_btn = Button(WIDTH//2 - 100, 250, 200, 40, "Generar Licencia")
    save_btn = Button(WIDTH//2 - 100, 300, 200, 40, "Guardar Licencia")
    back_btn = Button(WIDTH//2 - 100, 500, 200, 40, "Volver")
    
    license_key = ""
    status_msg = ""
    status_color = BLACK
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if input_box.handle_event(event):
                pass
            
            if generate_btn.is_clicked(mouse_pos, event):
                identifier_for_licensing = input_box.text
                # Si el texto en el input sigue siendo el display_id de la máquina actual,
                # entonces usamos el internal_id de la máquina actual para generar la licencia.
                # Si el usuario ha modificado el texto, usamos ese texto tal cual.
                if input_box.text == current_display_id:
                    identifier_for_licensing = current_internal_id
                
                if identifier_for_licensing:
                    license_key = generate_license_key(identifier_for_licensing)
                    status_msg = "Licencia generada!"
                    status_color = GREEN
                else:
                    status_msg = "ID para licencia está vacío!" # Mensaje más preciso
                    status_color = RED
            
            if save_btn.is_clicked(mouse_pos, event) and license_key:
                identifier_to_store = input_box.text
                if input_box.text == current_display_id: # Coherencia con la generación
                    identifier_to_store = current_internal_id

                if store_license(license_key, identifier_to_store): # Usar el ID correcto para guardar
                    status_msg = f"Licencia guardada en: {LICENSE_FILE}"
                    status_color = GREEN
                else:
                    status_msg = "Error al guardar la licencia"
                    status_color = RED
            
            if back_btn.is_clicked(mouse_pos, event):
                running = False
        
        generate_btn.check_hover(mouse_pos)
        save_btn.check_hover(mouse_pos)
        back_btn.check_hover(mouse_pos)
        
        screen.fill(WHITE)
        
        title = font_large.render("Gestor de Licencias", True, DARK_BLUE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        instructions = font_small.render("Ingrese ID de usuario/máquina y genere una licencia:", True, BLACK)
        screen.blit(instructions, (WIDTH//2 - instructions.get_width()//2, 150))
        
        input_label = font_medium.render("ID:", True, BLACK)
        screen.blit(input_label, (WIDTH//2 - 150, 205))
        input_box.update()
        input_box.draw(screen)
        
        generate_btn.draw(screen)
        
        if license_key:
            save_btn.draw(screen)
            
            license_text = font_small.render("Licencia generada:", True, BLACK)
            screen.blit(license_text, (WIDTH//2 - license_text.get_width()//2, 370))
            
            license_display = font_small.render(license_key, True, DARK_BLUE)
            screen.blit(license_display, (WIDTH//2 - license_display.get_width()//2, 400))
        
        if status_msg:
            status_text = font_medium.render(status_msg, True, status_color)
            screen.blit(status_text, (WIDTH//2 - status_text.get_width()//2, 450))
        
        back_btn.draw(screen)
        
        pygame.display.flip()
    
    return True

def verification_screen():
    license_data = load_license_data()
    status_msg = "Verificando licencia..."
    status_color = BLACK
    
    if license_data:
        # Usar la clave correcta "machine_identifier" también al verificar
        is_valid = verify_license(license_data["license_key"], license_data.get("machine_identifier", license_data.get("user_identifier"))) # Compatible con ambos por si acaso
        if is_valid:
            status_msg = "Licencia VÁLIDA"
            status_color = GREEN
        else:
            status_msg = "Licencia INVÁLIDA"
            status_color = RED
    else:
        status_msg = f"No se encontró archivo de licencia en: {LICENSE_FILE}"
        status_color = RED
    
    back_btn = Button(WIDTH//2 - 100, 400, 200, 40, "Volver")
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if back_btn.is_clicked(mouse_pos, event):
                running = False
        
        back_btn.check_hover(mouse_pos)
        
        screen.fill(WHITE)
        
        title = font_large.render("Verificación de Licencia", True, DARK_BLUE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        
        if license_data:
            # Mostrar el identificador usando la clave correcta
            identifier_to_display = license_data.get("machine_identifier", license_data.get("user_identifier", "N/A"))
            id_text = font_medium.render(f"ID: {identifier_to_display}", True, BLACK)
            screen.blit(id_text, (WIDTH//2 - id_text.get_width()//2, 200))
            
            key_text = font_small.render(f"Clave: {license_data['license_key']}", True, BLACK)
            screen.blit(key_text, (WIDTH//2 - key_text.get_width()//2, 240))
        
        status_text = font_medium.render(status_msg, True, status_color)
        screen.blit(status_text, (WIDTH//2 - status_text.get_width()//2, 300))
        
        back_btn.draw(screen)
        
        pygame.display.flip()
    
    return True

def main_menu():
    create_btn = Button(WIDTH//2 - 100, 200, 200, 40, "Crear Licencia")
    verify_btn = Button(WIDTH//2 - 100, 260, 200, 40, "Verificar Licencia")
    exit_btn = Button(WIDTH//2 - 100, 400, 200, 40, "Salir")
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if create_btn.is_clicked(mouse_pos, event):
                if not license_screen():
                    running = False
            
            if verify_btn.is_clicked(mouse_pos, event):
                if not verification_screen():
                    running = False
            
            if exit_btn.is_clicked(mouse_pos, event):
                running = False
        
        create_btn.check_hover(mouse_pos)
        verify_btn.check_hover(mouse_pos)
        exit_btn.check_hover(mouse_pos)
        
        screen.fill(WHITE)
        
        title = font_large.render("Sistema de Licencias", True, DARK_BLUE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        
        create_btn.draw(screen)
        verify_btn.draw(screen)
        exit_btn.draw(screen)
        
        info_text = font_small.render("Clinómetro - Versión Profesional", True, BLACK)
        screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, 500))
        
        pygame.display.flip()

if __name__ == "__main__":
    main_menu()
    pygame.quit()
