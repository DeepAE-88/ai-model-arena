import pygame
import sys
import math
import random

# Инициализация
pygame.init()
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Кролики против зомби!")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

# Цвета
GREEN = (34, 139, 34)
BROWN = (139, 69, 19)
GRAY = (100, 100, 100)
RED = (220, 20, 60)
ORANGE = (255, 140, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (70, 130, 180)

# Параметры пушки
CANNON_X, CANNON_Y = 100, HEIGHT - 100
CANNON_LENGTH = 60

# Огород
garden_plots = [
    {"x": 50, "y": HEIGHT - 50, "crop": None, "growth": 0, "max_growth": 300},
    {"x": 120, "y": HEIGHT - 70, "crop": None, "growth": 0, "max_growth": 250},
]
planting_mode = None  # 'cabbage' or 'carrot'

# Ресурсы кролика
cabbage_count = 0
carrot_count = 0

# Снаряды
projectiles = []
current_ammo = "cabbage"  # or "carrot"

# Зомби
zombies = []
zombie_spawn_timer = 0
zombie_types = [
    {"name": "basic", "hp": 50, "speed": 0.8, "color": RED, "size": 30},
    {"name": "armored", "hp": 100, "speed": 0.5, "color": (100, 100, 120), "size": 35},
]

# Игровое состояние
aiming = False
aim_start_time = 0
last_shot_time = 0
game_time = 0

# Функция для рисования пушки
def draw_cannon(angle):
    end_x = CANNON_X + CANNON_LENGTH * math.cos(angle)
    end_y = CANNON_Y - CANNON_LENGTH * math.sin(angle)
    pygame.draw.line(screen, BROWN, (CANNON_X, CANNON_Y), (end_x, end_y), 12)
    pygame.draw.circle(screen, (80, 50, 20), (CANNON_X, CANNON_Y), 15)

# Класс снаряда
class Projectile:
    def __init__(self, x, y, angle, proj_type):
        self.x = x
        self.y = y
        self.type = proj_type
        speed = 12
        self.vx = speed * math.cos(angle)
        self.vy = -speed * math.sin(angle)  # вверх — отрицательно
        self.mass = 1.0 if proj_type == "cabbage" else 0.7
        self.radius = 8 if proj_type == "cabbage" else 6
        self.alive = True
        self.exploded = False

    def update(self, dt):
        if not self.alive:
            return
        # Гравитация и сопротивление (упрощённо)
        self.vy += 300 * dt  # гравитация
        drag = 0.98
        self.vx *= drag
        self.vy *= drag
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        # Проверка выхода за экран
        if self.x > WIDTH or self.y > HEIGHT or self.y < 0:
            self.alive = False

    def draw(self):
        color = GREEN if self.type == "cabbage" else ORANGE
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)

# Класс зомби
class Zombie:
    def __init__(self, ztype):
        self.x = WIDTH + 50
        self.y = HEIGHT - 100
        self.hp = ztype["hp"]
        self.max_hp = ztype["hp"]
        self.speed = ztype["speed"]
        self.color = ztype["color"]
        self.size = ztype["size"]
        self.alive = True

    def update(self, dt):
        if self.alive:
            self.x -= self.speed * dt * 60
            if self.x < 0:
                self.alive = False

    def draw(self):
        if self.alive:
            pygame.draw.rect(screen, self.color, (self.x - self.size//2, self.y - self.size//2, self.size, self.size))
            # Полоска здоровья
            bar_width = self.size
            pygame.draw.rect(screen, RED, (self.x - bar_width//2, self.y - self.size//2 - 10, bar_width, 5))
            pygame.draw.rect(screen, (0, 200, 0), (self.x - bar_width//2, self.y - self.size//2 - 10, bar_width * (self.hp / self.max_hp), 5))

# Проверка коллизии
def check_collision(proj, zombie):
    dx = proj.x - zombie.x
    dy = proj.y - zombie.y
    distance = math.hypot(dx, dy)
    return distance < (proj.radius + zombie.size // 2)

# Основной цикл
running = True
while running:
    dt = clock.tick(60) / 1000.0
    game_time += dt
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ — начало прицеливания
                aiming = True
                aim_start_time = game_time
            elif event.button == 3:  # ПКМ — выстрел
                if current_ammo == "cabbage" and cabbage_count > 0:
                    cabbage_count -= 1
                    projectiles.append(Projectile(CANNON_X, CANNON_Y, cannon_angle, "cabbage"))
                elif current_ammo == "carrot" and carrot_count > 0:
                    carrot_count -= 1
                    projectiles.append(Projectile(CANNON_X, CANNON_Y, cannon_angle, "carrot"))
            elif event.button == 4:  # Колесо вверх
                current_ammo = "cabbage"
            elif event.button == 5:  # Колесо вниз
                current_ammo = "carrot"
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                aiming = False

    # Расчёт угла пушки
    dx = mouse_x - CANNON_X
    dy = CANNON_Y - mouse_y
    base_angle = math.atan2(dy, dx)
    cannon_angle = base_angle

    # Дрожание при удержании
    if aiming:
        hold_time = game_time - aim_start_time
        jitter = random.uniform(-0.3, 0.3) * min(hold_time * 2, 1.0)
        cannon_angle += jitter

    # Спавн зомби
    zombie_spawn_timer += dt
    if zombie_spawn_timer > 2.0:  # каждые 2 секунды
        zombie_spawn_timer = 0
        ztype = random.choice(zombie_types)
        zombies.append(Zombie(ztype))

    # Обновление огорода
    for plot in garden_plots:
        if plot["crop"]:
            plot["growth"] += dt * 20
            if plot["growth"] >= plot["max_growth"]:
                if plot["crop"] == "cabbage":
                    cabbage_count += 1
                else:
                    carrot_count += 1
                plot["crop"] = None
                plot["growth"] = 0
        else:
            # Автоматическая посадка, если есть семена (для упрощения)
            if cabbage_count > 3 and plot["crop"] is None:
                plot["crop"] = "cabbage"
            elif carrot_count > 3 and plot["crop"] is None:
                plot["crop"] = "carrot"

    # Обновление снарядов
    for proj in projectiles[:]:
        proj.update(dt)
        if not proj.alive:
            projectiles.remove(proj)
            continue
        # Проверка попаданий
        for zombie in zombies:
            if zombie.alive and check_collision(proj, zombie):
                proj.alive = False
                speed = math.hypot(proj.vx, proj.vy)
                impulse = proj.mass * speed
                damage = impulse * 0.3
                zombie.hp -= damage
                if zombie.hp <= 0:
                    zombie.alive = False
                # Взрыв морковки
                if proj.type == "carrot" and not proj.exploded:
                    proj.exploded = True
                    for z in zombies:
                        if z.alive:
                            dx = z.x - proj.x
                            dy = z.y - proj.y
                            dist = math.hypot(dx, dy)
                            if dist < 60:
                                z.hp -= 15
                                if z.hp <= 0:
                                    z.alive = False
                break

    # Обновление зомби
    for zombie in zombies[:]:
        zombie.update(dt)
        if not zombie.alive:
            zombies.remove(zombie)

    # Очистка мёртвых снарядов
    projectiles = [p for p in projectiles if p.alive]

    # --- Рендеринг ---
    screen.fill((135, 206, 235))  # голубое небо

    # Земля
    pygame.draw.rect(screen, (34, 100, 34), (0, HEIGHT - 50, WIDTH, 50))

    # Огород
    for plot in garden_plots:
        color = (50, 120, 50)
        if plot["crop"] == "cabbage":
            color = GREEN
        elif plot["crop"] == "carrot":
            color = ORANGE
        pygame.draw.rect(screen, color, (plot["x"] - 15, plot["y"] - 15, 30, 30))
        # Индикатор роста
        if plot["crop"]:
            progress = min(1.0, plot["growth"] / plot["max_growth"])
            pygame.draw.rect(screen, WHITE, (plot["x"] - 15, plot["y"] + 20, 30, 5))
            pygame.draw.rect(screen, BLUE, (plot["x"] - 15, plot["y"] + 20, int(30 * progress), 5))

    # Пушка
    draw_cannon(cannon_angle)

    # Снаряды
    for proj in projectiles:
        proj.draw()

    # Зомби
    for zombie in zombies:
        zombie.draw()

    # Интерфейс
    ammo_text = font.render(f"Патроны: {current_ammo} (ПКМ — выстрел, колесо — смена)", True, WHITE)
    screen.blit(ammo_text, (10, 10))
    count_text = font.render(f"Капуста: {cabbage_count}   Морковка: {carrot_count}", True, WHITE)
    screen.blit(count_text, (10, 40))
    hint = font.render("ЛКМ — удерживай для прицеливания (дрожание!)", True, WHITE)
    screen.blit(hint, (10, 70))

    pygame.display.flip()

pygame.quit()
sys.exit()