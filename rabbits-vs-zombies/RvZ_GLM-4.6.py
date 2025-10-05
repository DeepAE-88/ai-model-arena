import pygame
import math
import random

# --- Константы ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
SKY_BLUE = (135, 206, 235)
ORANGE = (255, 165, 0)
RED = (220, 20, 60)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

# Физика
GRAVITY = 9.8 * 50  # Масштабировано для пикселей
AIR_RESISTANCE_COEFF = 0.002  # Коэффициент квадратичного сопротивления воздуха
TIME_STEP = 1 / FPS

# Пушка
CANNON_LENGTH = 60
CANNON_WIDTH = 25
CANNON_COLOR = DARK_GRAY
SHAKE_GROWTH_RATE = 0.5  # Скорость роста амплитуды колебаний
MAX_SHAKE_AMPLITUDE = 15  # Максимальная амплитуда в градусах
SHAKE_FREQUENCY = 0.01  # Частота колебаний

# Снаряды
CABBAGE_MASS = 1.0
CABBAGE_RADIUS = 8
CABBAGE_COLOR = GREEN
CABBAGE_DAMAGE_COEFF = 0.5
CARROT_MASS = 0.5
CARROT_RADIUS = 5
CARROT_COLOR = ORANGE
CARROT_DAMAGE_COEFF = 0.3
CARROT_SPREAD_ANGLE = 15 # Угол разлета моркови в градусах
CARROT_COUNT = 5

# Зомби
ZOMBIE_BASE_SPEED = 20
ZOMBIE_BASE_HEALTH = 100
ZOMBIE_COLOR = (150, 150, 150)
ARMORED_ZOMBIE_SPEED = ZOMBIE_BASE_SPEED * 0.5
ARMORED_ZOMBIE_HEALTH = ZOMBIE_BASE_HEALTH * 3
ARMORED_ZOMBIE_COLOR = DARK_GRAY

# Огород
GARDEN_ROWS = 2
GARDEN_COLS = 5
PLOT_SIZE = 40
GROWTH_TIME = 5000 # Время роста в миллисекундах

class Terrain:
    """Класс для генерации и отрисовки холмистого ландшафта"""
    def __init__(self, width, height, base_height):
        self.width = width
        self.height = height
        self.base_height = base_height
        self.points = []
        self.generate()

    def generate(self):
        """Генерирует точки ландшафта с помощью синусоиды"""
        num_points = self.width // 10
        for i in range(num_points + 1):
            x = i * 10
            y = self.base_height + math.sin(i * 0.02) * 80 + math.sin(i * 0.05) * 40
            self.points.append((x, y))

    def draw(self, screen):
        """Рисует ландшафт"""
        # Рисуем небо
        screen.fill(SKY_BLUE)
        # Рисуем землю
        points_with_corners = self.points + [(self.width, self.height), (0, self.height)]
        pygame.draw.polygon(screen, GREEN, points_with_corners)

    def get_height_at(self, x):
        """Возвращает высоту ландшафта в точке x"""
        if x < 0 or x > self.width:
            return self.base_height
        
        # Находим два ближайших сегмента
        for i in range(len(self.points) - 1):
            p1, p2 = self.points[i], self.points[i+1]
            if p1[0] <= x <= p2[0]:
                # Линейная интерполяция
                if p2[0] - p1[0] == 0: return p1[1]
                t = (x - p1[0]) / (p2[0] - p1[0])
                return p1[1] + t * (p2[1] - p1[1])
        return self.base_height


class Cannon:
    """Класс пушки с механикой колебаний"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = -math.pi / 4  # Начальный угол
        self.base_angle = self.angle
        self.shake_amplitude = 0
        self.last_mouse_pos = None
        self.shake_timer = 0

    def update(self, mouse_pos):
        """Обновляет угол пушки и амплитуду колебаний"""
        if mouse_pos:
            dx = mouse_pos[0] - self.x
            dy = mouse_pos[1] - self.y
            self.base_angle = math.atan2(dy, dx)

            # Механика колебаний
            if self.last_mouse_pos and mouse_pos == self.last_mouse_pos:
                self.shake_timer += TIME_STEP
                self.shake_amplitude = min(self.shake_timer * SHAKE_GROWTH_RATE, MAX_SHAKE_AMPLITUDE)
            else:
                self.shake_timer = 0
                self.shake_amplitude = 0
            
            self.last_mouse_pos = mouse_pos

            # Применяем колебания
            shake_offset = math.radians(self.shake_amplitude) * math.sin(pygame.time.get_ticks() * SHAKE_FREQUENCY)
            self.angle = self.base_angle + shake_offset

    def draw(self, screen):
        """Рисует пушку"""
        end_x = self.x + CANNON_LENGTH * math.cos(self.angle)
        end_y = self.y + CANNON_LENGTH * math.sin(self.angle)
        
        pygame.draw.line(screen, CANNON_COLOR, (self.x, self.y), (end_x, end_y), CANNON_WIDTH)
        pygame.draw.circle(screen, CANNON_COLOR, (int(self.x), int(self.y)), CANNON_WIDTH // 2)

    def get_barrel_end(self):
        """Возвращает координаты конца ствола"""
        end_x = self.x + CANNON_LENGTH * math.cos(self.angle)
        end_y = self.y + CANNON_LENGTH * math.sin(self.angle)
        return end_x, end_y


class Projectile:
    """Класс снаряда с реалистичной физикой"""
    def __init__(self, x, y, angle, speed, mass, radius, color, damage_coeff):
        self.x = x
        self.y = y
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.mass = mass
        self.radius = radius
        self.color = color
        self.damage_coeff = damage_coeff
        self.active = True
        self.trail = [] # След за снарядом

    def update(self, terrain):
        """Обновляет позицию снаряда с учетом гравитации и сопротивления воздуха"""
        if not self.active:
            return

        # Сохраняем след
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 10:
            self.trail.pop(0)

        # Скорость
        v = math.sqrt(self.vx**2 + self.vy**2)
        if v > 0:
            # Сила сопротивления воздуха (квадратичная модель)
            drag_force_x = -AIR_RESISTANCE_COEFF * v * self.vx
            drag_force_y = -AIR_RESISTANCE_COEFF * v * self.vy
            
            # Ускорение
            ax = drag_force_x / self.mass
            ay = GRAVITY + (drag_force_y / self.mass)
            
            # Обновление скорости (метод Эйлера)
            self.vx += ax * TIME_STEP
            self.vy += ay * TIME_STEP
        
        # Обновление позиции
        self.x += self.vx * TIME_STEP
        self.y += self.vy * TIME_STEP
        
        # Проверка на выход за экран или столкновение с землей
        if self.x < 0 or self.x > SCREEN_WIDTH or self.y > SCREEN_HEIGHT:
            self.active = False
        
        if self.y > terrain.get_height_at(self.x):
            self.active = False

    def draw(self, screen):
        """Рисует снаряд и его след"""
        if not self.active:
            return
        # Рисуем след
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)))
            color = (*self.color, alpha)
            pygame.draw.circle(screen, self.color, pos, self.radius // 2)
        # Рисуем сам снаряд
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def get_momentum(self):
        """Возвращает импульс снаряда"""
        v = math.sqrt(self.vx**2 + self.vy**2)
        return self.mass * v

    def get_damage(self):
        """Рассчитывает урон на основе импульса"""
        return self.get_momentum() * self.damage_coeff


class Zombie:
    """Класс зомби"""
    def __init__(self, x, y, terrain, zombie_type="normal"):
        self.x = x
        self.y = y
        self.terrain = terrain
        self.type = zombie_type
        
        if self.type == "normal":
            self.speed = ZOMBIE_BASE_SPEED
            self.max_health = ZOMBIE_BASE_HEALTH
            self.color = ZOMBIE_COLOR
            self.size = 20
        elif self.type == "armored":
            self.speed = ARMORED_ZOMBIE_SPEED
            self.max_health = ARMORED_ZOMBIE_HEALTH
            self.color = ARMORED_ZOMBIE_COLOR
            self.size = 25
        
        self.health = self.max_health
        self.animation_offset = random.uniform(0, math.pi * 2)
        self.active = True

    def update(self, cannon_x):
        """Двигает зомби к пушке"""
        if not self.active:
            return
        
        # Движение по горизонтали
        if self.x > cannon_x:
            self.x -= self.speed * TIME_STEP
        else:
            self.x += self.speed * TIME_STEP
            
        # Следование за рельефом
        self.y = self.terrain.get_height_at(self.x) - self.size

    def draw(self, screen):
        """Рисует зомби с анимацией ходьбы"""
        if not self.active:
            return
        
        # Анимация "покачивания"
        wobble = math.sin(pygame.time.get_ticks() * 0.005 + self.animation_offset) * 3
        draw_y = self.y + wobble
        
        # Тело
        pygame.draw.circle(screen, self.color, (int(self.x), int(draw_y)), self.size)
        # Глаза
        eye_y = draw_y - 5
        pygame.draw.circle(screen, RED, (int(self.x - 7), int(eye_y)), 3)
        pygame.draw.circle(screen, RED, (int(self.x + 7), int(eye_y)), 3)
        
        # Полоска здоровья
        bar_width = 40
        bar_height = 5
        bar_x = self.x - bar_width // 2
        bar_y = draw_y - self.size - 10
        health_percentage = self.health / self.max_health
        
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, bar_width * health_percentage, bar_height))

    def take_damage(self, damage):
        """Наносит урон зомби"""
        self.health -= damage
        if self.health <= 0:
            self.active = False


class Garden:
    """Класс для огорода"""
    def __init__(self, start_x, start_y):
        self.plots = []
        self.start_x = start_x
        self.start_y = start_y
        self.init_plots()

    def init_plots(self):
        for row in range(GARDEN_ROWS):
            for col in range(GARDEN_COLS):
                x = self.start_x + col * (PLOT_SIZE + 10)
                y = self.start_y + row * (PLOT_SIZE + 10)
                self.plots.append({
                    'rect': pygame.Rect(x, y, PLOT_SIZE, PLOT_SIZE),
                    'growth_time': 0,
                    'is_growing': False,
                    'is_ready': False,
                    'type': random.choice(['cabbage', 'carrot'])
                })

    def plant(self):
        """Начинает выращивать на пустых грядках"""
        for plot in self.plots:
            if not plot['is_growing'] and not plot['is_ready']:
                plot['is_growing'] = True
                plot['growth_time'] = pygame.time.get_ticks()

    def update(self):
        """Обновляет состояние грядок"""
        current_time = pygame.time.get_ticks()
        for plot in self.plots:
            if plot['is_growing'] and not plot['is_ready']:
                if current_time - plot['growth_time'] > GROWTH_TIME:
                    plot['is_ready'] = True
                    plot['is_growing'] = False

    def harvest(self):
        """Собирает готовый урожай"""
        harvested = {'cabbage': 0, 'carrot': 0}
        for plot in self.plots:
            if plot['is_ready']:
                harvested[plot['type']] += 1
                plot['is_ready'] = False
        return harvested

    def draw(self, screen):
        """Рисует огород"""
        font = pygame.font.Font(None, 20)
        for plot in self.plots:
            # Рисуем грядку
            color = BROWN
            if plot['is_growing']:
                progress = (pygame.time.get_ticks() - plot['growth_time']) / GROWTH_TIME
                color = (int(139 * (1 - progress)), int(69 + 50 * progress), int(19 * (1 - progress)))
            elif plot['is_ready']:
                color = YELLOW if plot['type'] == 'cabbage' else ORANGE
            
            pygame.draw.rect(screen, color, plot['rect'])
            pygame.draw.rect(screen, BLACK, plot['rect'], 2)
            
            # Подпись
            label = "C" if plot['type'] == 'cabbage' else "M"
            text = font.render(label, True, WHITE)
            text_rect = text.get_rect(center=plot['rect'].center)
            screen.blit(text, text_rect)


class Game:
    """Основной класс игры"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Кролики против Зомби")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.running = True
        self.reset_game()

    def reset_game(self):
        """Сбрасывает игру в начальное состояние"""
        self.terrain = Terrain(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_HEIGHT - 150)
        cannon_y = self.terrain.get_height_at(100) - 30
        self.cannon = Cannon(100, cannon_y)
        self.projectiles = []
        self.zombies = []
        self.zombie_spawn_timer = 0
        self.zombie_spawn_delay = 3000  # Спавн зомби каждые 3 секунды

        self.inventory = {'cabbage': 10, 'carrot': 5}
        self.garden = Garden(SCREEN_WIDTH - 250, 50)
        
        self.game_over = False

    def spawn_zombie(self):
        """Создает нового зомби"""
        x = SCREEN_WIDTH - 50
        y = self.terrain.get_height_at(x)
        zombie_type = "armored" if random.random() < 0.3 else "normal"
        self.zombies.append(Zombie(x, y, self.terrain, zombie_type))

    def handle_events(self):
        """Обрабатывает события"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    harvested = self.garden.harvest()
                    self.inventory['cabbage'] += harvested['cabbage']
                    self.inventory['carrot'] += harvested['carrot']
                    self.garden.plant() # Сразу сажаем новое
                if event.key == pygame.K_r:
                    self.reset_game()

            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                mouse_pos = pygame.mouse.get_pos()
                barrel_end_x, barrel_end_y = self.cannon.get_barrel_end()
                
                # Начальная скорость снаряда
                initial_speed = 800
                
                if event.button == 1:  # Левая кнопка - капуста
                    if self.inventory['cabbage'] > 0:
                        self.projectiles.append(
                            Projectile(barrel_end_x, barrel_end_y, self.cannon.angle, initial_speed,
                                       CABBAGE_MASS, CABBAGE_RADIUS, CABBAGE_COLOR, CABBAGE_DAMAGE_COEFF)
                        )
                        self.inventory['cabbage'] -= 1
                        self.garden.plant()

                elif event.button == 3:  # Правая кнопка - морковь
                    if self.inventory['carrot'] > 0:
                        for i in range(CARROT_COUNT):
                            spread_angle_rad = math.radians(random.uniform(-CARROT_SPREAD_ANGLE, CARROT_SPREAD_ANGLE))
                            angle = self.cannon.angle + spread_angle_rad
                            self.projectiles.append(
                                Projectile(barrel_end_x, barrel_end_y, angle, initial_speed * random.uniform(0.9, 1.1),
                                           CARROT_MASS, CARROT_RADIUS, CARROT_COLOR, CARROT_DAMAGE_COEFF)
                            )
                        self.inventory['carrot'] -= 1
                        self.garden.plant()

    def update(self):
        """Обновляет состояние всех объектов игры"""
        if self.game_over:
            return

        mouse_pos = pygame.mouse.get_pos()
        self.cannon.update(mouse_pos)

        # Обновление снарядов
        for proj in self.projectiles[:]:
            proj.update(self.terrain)
            if not proj.active:
                self.projectiles.remove(proj)

        # Обновление зомби
        for zombie in self.zombies[:]:
            zombie.update(self.cannon.x)
            if not zombie.active:
                self.zombies.remove(zombie)
            elif abs(zombie.x - self.cannon.x) < 30: # Зомби добрался до пушки
                self.game_over = True

        # Проверка столкновений
        for proj in self.projectiles[:]:
            if not proj.active:
                continue
            for zombie in self.zombies:
                if not zombie.active:
                    continue
                dist = math.sqrt((proj.x - zombie.x)**2 + (proj.y - zombie.y)**2)
                if dist < proj.radius + zombie.size:
                    damage = proj.get_damage()
                    zombie.take_damage(damage)
                    proj.active = False # Снаряд исчезает при попадании
                    break

        # Спавн зомби
        current_time = pygame.time.get_ticks()
        if current_time - self.zombie_spawn_timer > self.zombie_spawn_delay:
            self.spawn_zombie()
            self.zombie_spawn_timer = current_time
            # Увеличиваем сложность
            self.zombie_spawn_delay = max(1000, self.zombie_spawn_delay - 10)

        # Обновление огорода
        self.garden.update()

    def draw(self):
        """Отрисовывает все объекты на экране"""
        self.terrain.draw(self.screen)
        self.cannon.draw(self.screen)
        
        for proj in self.projectiles:
            proj.draw(self.screen)
            
        for zombie in self.zombies:
            zombie.draw(self.screen)

        # UI
        self.garden.draw(self.screen)
        
        # Инвентарь
        inv_text = self.font.render(f"Капуста: {self.inventory['cabbage']}  Морковь: {self.inventory['carrot']}", True, BLACK)
        self.screen.blit(inv_text, (10, 10))
        
        # Подсказка
        hint_text = self.small_font.render("ЛКМ - Капуста | ПКМ - Морковь | Пробел - Собрать урожай | R - Рестарт", True, BLACK)
        self.screen.blit(hint_text, (10, 50))

        if self.game_over:
            game_over_text = self.font.render("ЗОМБИ СЪЕЛИ КРОЛИКА! Нажмите R для перезапуска.", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            pygame.draw.rect(self.screen, WHITE, text_rect.inflate(20, 10))
            self.screen.blit(game_over_text, text_rect)


        pygame.display.flip()

    def run(self):
        """Главный игровой цикл"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()