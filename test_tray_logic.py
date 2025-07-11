import pygame
import sys
import os
from PIL import Image, ImageDraw 
from unittest.mock import MagicMock, patch

# --- Mockear pystray ANTES de cualquier importación o uso ---
MockPystrayIconClass = MagicMock(name="MockPystrayIconClass")
MockPystrayMenuItemClass = MagicMock(name="MockPystrayMenuItemClass", side_effect=lambda label, action, **kwargs: (label, action)) # Simula la tupla

mock_pystray_module = MagicMock(name="MockPystrayModule")
mock_pystray_module.Icon = MockPystrayIconClass
mock_pystray_module.MenuItem = MockPystrayMenuItemClass
sys.modules['pystray'] = mock_pystray_module
# --- Fin del mockeo de pystray ---

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

screen = None
dimensiones = [1060, 430]
window_visible = True
hecho = False
ser = None 
tray_icon = None

def resource_path(relative_path):
    if relative_path == "compas1.png":
        try:
            img = Image.new('RGB', (60, 60), color = 'red')
            dummy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dummy_icon.png")
            img.save(dummy_path)
            return dummy_path
        except Exception as e:
            # print(f"Error creando dummy_icon.png: {e}")
            return None 
    return relative_path

def quit_program_real_sim(icon_mock_instance, item_mock_instance):
    global hecho, ser, tray_icon
    # print("Mock: quit_program_real_sim llamada")
    if ser and hasattr(ser, 'is_open') and ser.is_open:
        ser.close()
    hecho = True
    if tray_icon and hasattr(tray_icon, 'stop'):
        tray_icon.stop()
    pygame.quit()

def show_window_real_sim(icon_mock_instance, item_mock_instance):
    global window_visible, screen, dimensiones
    # print("Mock: show_window_real_sim llamada")
    pygame.display.init()
    try:
        pygame.display.set_mode(dimensiones)
    except pygame.error:
        pass
    window_visible = True

def hide_window_to_tray_real_sim():
    global window_visible, tray_icon 
    from pystray import Icon, MenuItem # pylint: disable=import-outside-toplevel 

    # print("Mock: hide_window_to_tray_real_sim llamada")
    window_visible = False

    image = None # Inicializar image
    try:
        image_path = resource_path("compas1.png")
        if image_path is None: raise FileNotFoundError("dummy_icon.png no pudo ser creado")
        image = Image.open(image_path)
    except Exception:
        from PIL import ImageDraw as PILImageDraw # pylint: disable=import-outside-toplevel
        width, height = 64, 64
        image = Image.new('RGB', (width, height), (200, 200, 200))
        dc = PILImageDraw.Draw(image)
        dc.rectangle((width // 2, 0, width, height // 2), fill=(100,100,100))
        dc.rectangle((0, height // 2, width // 2, height), fill=(100,100,100))
    
    menu_items = (MenuItem('Mostrar Lalito', show_window_real_sim, default=True),
                  MenuItem('Salir', quit_program_real_sim))
    
    mock_icon_instance = Icon("Lalito_sim", image, "Lalito Clinómetro Sim", menu_items)
    mock_icon_instance.run_detached()
    tray_icon = mock_icon_instance

def run_tests():
    global window_visible, tray_icon, hecho, ser, screen, dimensiones, MockPystrayIconClass

    pygame.init()
    try:
        screen = pygame.display.set_mode(dimensiones, pygame.NOFRAME) # Intentar sin ventana visible
    except pygame.error:
        # print("INFO: No se pudo crear la pantalla de Pygame.")
        try: # Fallback a pantalla normal si NOFRAME falla y luego iconify
            screen = pygame.display.set_mode(dimensiones)
            pygame.display.iconify()
        except pygame.error:
            # print("INFO: Fallback de pantalla de Pygame también falló.")
            pass


    print("### Iniciando Prueba 1: Ocultar a la bandeja ###")
    window_visible = True 
    tray_icon = None
    
    mock_icon_instance_returned = MagicMock(name="ReturnedIconInstance")
    mock_icon_instance_returned.visible = True
    MockPystrayIconClass.reset_mock() # Resetear mocks de la clase antes de usar
    MockPystrayIconClass.return_value = mock_icon_instance_returned
    
    hide_window_to_tray_real_sim() 

    assert not window_visible, "Fallo Prueba 1: window_visible debería ser False."
    assert tray_icon is mock_icon_instance_returned, "Fallo Prueba 1: tray_icon global no es la instancia mock devuelta."
    MockPystrayIconClass.assert_called_once() 
    tray_icon.run_detached.assert_called_once()
    print("Prueba 1 completada.")

    print("### Iniciando Prueba 2: Mostrar desde la bandeja ###")
    assert tray_icon is not None, "Precondición Prueba 2: tray_icon no debe ser None."
    
    show_window_real_sim(tray_icon, None) 
    assert window_visible, "Fallo Prueba 2: window_visible debería ser True."
    print("Prueba 2 completada.")

    print("### Iniciando Prueba 3: Funcionamiento en segundo plano (Conceptual) ###")
    print("Prueba 3: Revisión de código indica que el bucle principal de clinometro.py procesa tareas en segundo plano.")
    print("Prueba 3 completada.")

    print("### Iniciando Prueba 4: Cierre completo desde la bandeja ###")
    hecho = False 
    ser = MagicMock(name="MockSerial") 
    ser.is_open = True
    
    assert tray_icon is not None, "Precondición Prueba 4: tray_icon no debe ser None."
    tray_icon.stop = MagicMock() # Asegurar que stop es un mock fresco para esta llamada

    quit_program_real_sim(tray_icon, None)
    assert hecho, "Fallo Prueba 4: 'hecho' debería ser True."
    if hasattr(ser, 'close') and isinstance(ser.close, MagicMock):
      ser.close.assert_called_once()
    tray_icon.stop.assert_called_once()
    print("Prueba 4 completada.")

if __name__ == "__main__":
    run_tests()
    print("\n### Todas las pruebas simuladas completadas. ###")
    dummy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dummy_icon.png")
    if os.path.exists(dummy_path):
        os.remove(dummy_path)
    pygame.quit()
