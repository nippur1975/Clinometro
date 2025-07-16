import pygame
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
import random

# Configuración
W, H = 600, 600
CENTER = (W // 2, H // 2)
R_MAX = 280
FPS = 30

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Simrad Sonar - Mancha Realista + Barrido Concéntrico")
clock = pygame.time.Clock()

# Generar una sola mancha orgánica amorfa
def generar_cardumen_realista():
    base = np.zeros((H, W), dtype=np.float32)
    for _ in range(30):
        x = random.randint(260, 340)
        y = random.randint(80, 160)
        intensidad = random.uniform(0.8, 1.0)
        radio = random.randint(12, 28)
        yy, xx = np.ogrid[:H, :W]
        mask = (xx - x)**2 + (yy - y)**2 <= radio**2
        base[mask] += intensidad

    base = gaussian_filter(base, sigma=16)
    base = (base - base.min()) / (base.max() - base.min())
    return base

# Deformación fluida tipo desplazamiento orgánico
def deformar_organico(base, frame):
    yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')
    dx = 5.0 * np.sin(2 * np.pi * yy / 200 + frame * 0.02)
    dy = 5.0 * np.cos(2 * np.pi * xx / 200 + frame * 0.015)
    coords = np.array([yy + dy, xx + dx])
    deformado = map_coordinates(base, coords, order=1, mode='reflect')
    return np.clip(deformado, 0, 1)

# Colormap sonar: verde → amarillo → rojo intenso
def colormap(val):
    val = np.clip(val, 0, 1)
    r = (np.clip(val * 3 - 1, 0, 1) * 255).astype(np.uint8)
    g = (np.clip(1.5 - abs(val * 3 - 1.5), 0, 1) * 255).astype(np.uint8)
    b = np.zeros_like(r)
    return np.stack([r, g, b], axis=-1)

# Variables
cardumen_base = generar_cardumen_realista()
r_barrido = 0
vel_barrido = 2
grosor_barrido = 3
frame = 0

# Bucle principal
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            exit()

    screen.fill((0, 0, 0))

    # Deformación suave y continua
    cardumen = deformar_organico(cardumen_base, frame)

    # Crear máscara del barrido concéntrico
    y, x = np.ogrid[:H, :W]
    distancia = np.sqrt((x - CENTER[0])**2 + (y - CENTER[1])**2)
    mascara_barrido = np.abs(distancia - r_barrido) < grosor_barrido

    # Aplicar atenuación suave en el área del barrido
    atenuacion = np.where(mascara_barrido, 0.7, 1.0)
    imagen_final = cardumen * atenuacion

    # Aplicar colormap y mostrar
    imagen_rgb = colormap(imagen_final)
    superficie = pygame.surfarray.make_surface(np.transpose(imagen_rgb, (1, 0, 2)))
    screen.blit(superficie, (0, 0))

    # Dibujar retícula sonar
    for r in range(50, R_MAX, 50):
        pygame.draw.circle(screen, (40, 40, 40), CENTER, r, 1)

    # Dibujar borde del barrido
    if r_barrido > 0:
        pygame.draw.circle(screen, (0, 200, 200), CENTER, int(r_barrido), 1)

    # Avanzar barrido
    r_barrido += vel_barrido
    if r_barrido > R_MAX:
        r_barrido = 0

    pygame.display.flip()
    clock.tick(FPS)
    frame += 1
