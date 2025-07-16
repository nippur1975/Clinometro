import numpy as np
import pygame
from scipy.ndimage import gaussian_filter
import math
import random

# Configuración
W, H = 800, 800
CENTER = (W // 2, H // 2)
FPS = 30
R_MAX = 350

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Simrad Sonar - Barrido Concéntrico con Movimiento")
clock = pygame.time.Clock()

# Colormap tipo Simrad
def colormap(val):
    val = np.clip(val, 0, 1)
    r = (np.clip(val * 4 - 2.5, 0, 1) * 255).astype(np.uint8)
    g = (np.clip(1.5 - abs(val * 4 - 2), 0, 1) * 255).astype(np.uint8)
    b = (np.clip(1.0 - val * 3, 0, 1) * 255).astype(np.uint8)
    return np.stack([r, g, b], axis=-1)

# Generar mancha roja en la proa, con offset
def generar_cardumen(x_offset=0, y_offset=0):
    base = np.zeros((H, W), dtype=np.float32)
    for _ in range(40):
        x = np.random.randint(CENTER[0] - 80, CENTER[0] + 80) + x_offset
        y = np.random.randint(60, 120) + y_offset
        rx = np.random.randint(30, 60)
        ry = np.random.randint(8, 20)
        intensidad = np.random.uniform(0.7, 1.0)
        yy, xx = np.ogrid[:H, :W]
        elipse = ((xx - x) / rx) ** 2 + ((yy - y) / ry) ** 2 <= 1
        base[elipse] += intensidad
    base = gaussian_filter(base, sigma=12)
    base = (base - base.min()) / (base.max() - base.min())
    return base

# Estado inicial
cardumen_base = generar_cardumen()
cardumen_actual = cardumen_base.copy()
cardumen_pos = [0, 0]
r_barrido = 0
vel_barrido = 3

# Bucle principal
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))

    y, x = np.ogrid[:H, :W]
    dist = np.sqrt((x - CENTER[0])**2 + (y - CENTER[1])**2)
    mascara_barrido = np.abs(dist - r_barrido) < 2
    zona_cardumen = (dist >= 100) & (dist <= 150)

    if np.any(mascara_barrido & zona_cardumen):
        ruido = np.random.normal(0, 0.01, (H, W))
        cardumen_actual = np.clip(cardumen_actual + gaussian_filter(ruido, sigma=6), 0, 1)
        dx = random.randint(-10, 10)
        dy = random.randint(-5, 5)
        cardumen_pos[0] = np.clip(cardumen_pos[0] + dx, -40, 40)
        cardumen_pos[1] = np.clip(cardumen_pos[1] + dy, -30, 30)
        cardumen_base = generar_cardumen(cardumen_pos[0], cardumen_pos[1])
        cardumen_actual = cardumen_base.copy()

    imagen_rgb = colormap(cardumen_actual)
    surface = pygame.surfarray.make_surface(np.transpose(imagen_rgb, (1, 0, 2)))
    screen.blit(surface, (0, 0))

    for r in range(100, R_MAX, 50):
        pygame.draw.circle(screen, (80, 80, 80), CENTER, r, 1)

    if r_barrido < R_MAX:
        pygame.draw.circle(screen, (255, 255, 255), CENTER, int(r_barrido), 1)

    r_barrido += vel_barrido
    if r_barrido > R_MAX:
        r_barrido = 0

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
