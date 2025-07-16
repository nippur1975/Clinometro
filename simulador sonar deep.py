import pygame
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
import random
import math

# Configuración
W, H = 600, 600
CENTER = (W // 2, H // 2)
R_MAX = 280
FPS = 30

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Simrad Sonar - Cardumen Alargado + Barrido")
clock = pygame.time.Clock()

# Generar una mancha amorfa, alargada, roja
def generar_cardumen_alargado():
    base = np.zeros((H, W), dtype=np.float32)
    for _ in range(40):
        x = random.randint(260, 340)
        y = random.randint(80, 160)
        intensidad = random.uniform(0.8, 1.0)
        rx = random.randint(25, 40)  # más ancho horizontalmente
        ry = random.randint(10, 20)  # más estrecho verticalmente
        yy, xx = np.ogrid[:H, :W]
        elipse = ((xx - x) / rx)**2 + ((yy - y) / ry)**2 <= 1
        base[elipse] += intensidad

    base = gaussian_filter(base, sigma=10)
    base = (base - base.min()) / (base.max() - base.min())
    return base

# Deformación suave + oscilación de tamaño
def deformar_organico(base, frame):
    # Oscilación de escala (zoom pulsante)
    scale = 1.0 + 0.05 * math.sin(frame * 0.05)
    yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')
    cx, cy = CENTER
    dx = (xx - cx) * scale
    dy = (yy - cy) * scale

    coords_x = cx + dx
    coords_y = cy + dy
    coords = np.array([coords_y, coords_x])
    deformado = map_coordinates(base, coords, order=1, mode='reflect')

    # Aplicar ligera ondulación
    ondula_x = 4.0 * np.sin(2 * np.pi * yy / 150 + frame * 0.02)
    ondula_y = 2.0 * np.cos(2 * np.pi * xx / 200 + frame * 0.015)
    coords_ondula = np.array([yy + ondula_y, xx + ondula_x])
    deformado = map_coordinates(deformado, coords_ondula, order=1, mode='reflect')
    return np.clip(deformado, 0, 1)

# Colormap ajustado: más rojo, menos verde
def colormap(val):
    val = np.clip(val, 0, 1)
    r = (val * 255).astype(np.uint8)
    g = (np.clip(1.2 - val * 2, 0, 1) * 180).astype(np.uint8)  # menos verde
    b = np.zeros_like(r)
    return np.stack([r, g, b], axis=-1)

# Variables
cardumen_base = generar_cardumen_alargado()
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

    # Deformación fluida con cambio de tamaño
    cardumen = deformar_organico(cardumen_base, frame)

    # Crear máscara del barrido concéntrico
    y, x = np.ogrid[:H, :W]
    distancia = np.sqrt((x - CENTER[0])**2 + (y - CENTER[1])**2)
    mascara_barrido = np.abs(distancia - r_barrido) < grosor_barrido

    # Atenuar ligeramente donde pasa el barrido
    atenuacion = np.where(mascara_barrido, 0.65, 1.0)
    imagen_final = cardumen * atenuacion

    # Aplicar colormap
    imagen_rgb = colormap(imagen_final)
    superficie = pygame.surfarray.make_surface(np.transpose(imagen_rgb, (1, 0, 2)))
    screen.blit(superficie, (0, 0))

    # Dibujar retícula
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

