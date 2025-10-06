import pygame
import math
import random
import sys

# Константы
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRAVITY = 0.5  # Масштабированная g
DRAG = 0.005   # Коэффициент сопротивления
FPS = 60

# Цвета
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

class Terrain:
    def __init__(self):
        self.height_map = [SCREEN_HEIGHT // 2] * SCREEN_WIDTH
        self.generate_hills()
    
    def generate_hills(self):
        # Procedural холмы (синусоида)
        for x in range(SCREEN_WIDTH):
            self.height_map[x] = SCREEN_HEIGHT // 2 + 100 * math.sin(x * 0.01) + 50 * math.sin(x * 0.03)
    
    def get_height(self, x):
        if 0 <= x < SCREEN_WIDTH:
            return self.height_map[int(x)]
        return SCREEN_HEIGHT // 2
    
    def draw(self, screen):
        points = [(x, self.height_map[x]) for x in range(SCREEN_WIDTH)]
        pygame.draw.polygon(screen, GREEN, points + [(SCREEN_WIDTH, SCREEN_HEIGHT), (0, SCREEN_HEIGHT)])

class Garden:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cabbage_ready = False
        self.carrot_ready = False
        self.growth_timer = 0
        self.max_timer = 300  # 5 сек на FPS=60
    
    def update(self):
        self.growth_timer += 1
        if self.growth_timer >= self.max_timer:
            self.cabbage_ready = True
            self.carrot_ready = True  # Морковь растёт быстрее, но для простоты одинаково
    
    def care(self):  # Уход ускоряет
        self.growth_timer += 30
        self.growth_timer = min(self.growth_timer, self.max_timer)
    
    def harvest(self, type_):
        if type_ == 'cabbage' and self.cabbage_ready:
            self.cabbage_ready = False
            self.growth_timer = 0
            return True
        elif type_ == 'carrot' and self.carrot_ready:
            self.carrot_ready = False
            self.growth_timer = 0
            return True
        return False
    
    def draw(self, screen):
        pygame.draw.rect(screen, BROWN, (self.x - 20, self.y - 20, 40, 40))
        if self.cabbage_ready:
            pygame.draw.circle(screen, GREEN, (self.x, self.y - 10), 10)  # Капуста
        if self.carrot_ready:
            pygame.draw.circle(screen, YELLOW, (self.x + 10, self.y), 8)  # Морковь

class Cannon:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.shake_amplitude = 0
        self.shake_timer = 0
        self.last_mouse_pos = (x, y)
        self.recoil_timer = 0
    
    def update(self, mouse_pos, dt):
        # Прицеливание
        dx = mouse_pos[0] - self.x
        dy = mouse_pos[1] - self.y
        self.angle = math.atan2(dy, dx)
        
        # Колебания: чем дольше в одной точке, тем сильнее
        if mouse_pos == self.last_mouse_pos:
            self.shake_timer += dt
            self.shake_amplitude = min(5 * (self.shake_timer / 1000), 15)  # Макс 15 пикселей
        else:
            self.shake_timer = 0
            self.shake_amplitude *= 0.9  # Затухание
        
        self.last_mouse_pos = mouse_pos
        
        # Отдача после выстрела
        if self.recoil_timer > 0:
            self.recoil_timer -= dt
            self.angle += 0.1 * math.sin(self.recoil_timer / 100)
        
        # Применяем shake
        shake_x = self.shake_amplitude * math.sin(pygame.time.get_ticks() * 0.01)
        shake_y = self.shake_amplitude * math.cos(pygame.time.get_ticks() * 0.01)
        self.x += shake_x * dt / 1000
        self.y += shake_y * dt / 1000
    
    def shoot(self, type_, terrain):
        if self.recoil_timer > 0:
            return None
        self.recoil_timer = 500  # 0.5 сек перезарядка
        vx = 10 * math.cos(self.angle)
        vy = 10 * math.sin(self.angle)
        if type_ == 'cabbage':
            return Projectile(self.x, self.y, vx, vy, 5, BLUE, terrain, is_aoe=False)  # Масса 5
        elif type_ == 'carrot':
            projectiles = []
            for i in range(3):  # Кластер
                offset_angle = self.angle + random.uniform(-0.2, 0.2)
                pvx = 8 * math.cos(offset_angle)
                pvy = 8 * math.sin(offset_angle)
                proj = Projectile(self.x, self.y, pvx, pvy, 3, YELLOW, terrain, is_aoe=True)
                projectiles.append(proj)
            return projectiles  # Возвращаем список
        return None
    
    def draw(self, screen):
        # Пушка как линия
        end_x = self.x + 50 * math.cos(self.angle)
        end_y = self.y + 50 * math.sin(self.angle)
        pygame.draw.line(screen, RED, (self.x, self.y), (end_x, end_y), 5)
        # База
        pygame.draw.circle(screen, BROWN, (int(self.x), int(self.y)), 10)

class Projectile:
    def __init__(self, x, y, vx, vy, mass, color, terrain, is_aoe=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.mass = mass
        self.color = color
        self.terrain = terrain
        self.is_aoe = is_aoe
        self.alive = True
        self.hit = False
    
    def update(self, dt, zombies):
        if not self.alive:
            return
        
        # Физика с drag (квадратичная модель)
        drag_force = DRAG * (self.vx**2 + self.vy**2)
        self.vx -= (drag_force * self.vx / math.sqrt(self.vx**2 + self.vy**2)) * dt if self.vx != 0 else 0
        self.vy -= (drag_force * self.vy / math.sqrt(self.vx**2 + self.vy**2)) * dt if self.vy != 0 else 0
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Проверка земли
        if self.y > self.terrain.get_height(self.x):
            self.alive = False
            return
        
        # Проверка зомби (неупругое столкновение)
        for zombie in zombies[:]:
            dist = math.hypot(self.x - zombie.x, self.y - zombie.y)
            if dist < 20:  # Радиус попадания
                impulse = self.mass * math.sqrt(self.vx**2 + self.vy**2)
                damage = impulse * 0.5  # Пропорционально импульсу
                zombie.take_damage(damage, self.vx, self.vy)  # Замедление от vx
                self.alive = False
                self.hit = True
                if self.is_aoe:
                    # AoE: поражает соседей
                    for other_z in zombies:
                        if other_z != zombie and math.hypot(self.x - other_z.x, self.y - other_z.y) < 50:
                            other_z.take_damage(damage * 0.7, 0, 0)
                break
    
    def draw(self, screen):
        if self.alive or self.hit:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 5)
            if self.hit:
                pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), 15, 2)  # Вспышка

class Zombie:
    def __init__(self, x, y, speed, health, terrain):
        self.x = x
        self.y = y
        self.speed = speed
        self.health = health
        self.max_health = health
        self.terrain = terrain
        self.anim_frame = 0  # Для анимации шага
    
    def update(self, dt, rabbit_x):
        # Движение к кролику, учитывая холмы
        self.y = self.terrain.get_height(self.x)
        dx = rabbit_x - self.x
        if dx > 0:
            self.x += self.speed * dt / 1000
            self.anim_frame += dt  # Анимация
        if self.x > rabbit_x + 50:  # Добрался — конец игры (упрощённо)
            print("Зомби добрался! Игра окончена.")
            pygame.quit()
            sys.exit()
    
    def take_damage(self, damage, push_x, push_y):
        self.health -= damage
        self.speed *= 0.8  # Замедление от неупругого удара
        self.x += push_x * 0.1  # Отбрасывание
        if self.health <= 0:
            print("Зомби убит!")
    
    def draw(self, screen):
        # Простая анимация: зомби как красный круг, "шагает" вверх-вниз
        bob = 5 * math.sin(self.anim_frame * 0.01)
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y + bob)), 15)
        # Здоровье бар
        bar_width = 30
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        pygame.draw.rect(screen, RED, (self.x - 15, self.y - 25, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (self.x - 15, self.y - 25, fill, bar_height))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Кролики против зомби")
        self.clock = pygame.time.Clock()
        self.terrain = Terrain()
        self.cannon = Cannon(100, self.terrain.get_height(100) - 20)  # Пушка на холме
        self.garden = Garden(80, self.terrain.get_height(80) - 30)
        self.zombies = []
        self.projectiles = []
        self.rabbit_type = "farmer"  # Базовый кролик
        self.spawn_timer = 0
        self.shoot_type = 'cabbage'  # По умолчанию
        self.running = True
    
    def spawn_zombie(self):
        types = [
            {"speed": 1, "health": 50},  # Обычный
            {"speed": 1.5, "health": 30},  # Быстрый
            {"speed": 0.5, "health": 100}  # Бронированный
        ]
        t = random.choice(types)
        x = -20
        y = self.terrain.get_height(x)
        zombie = Zombie(x, y, t["speed"], t["health"], self.terrain)
        self.zombies.append(zombie)
    
    def update(self):
        dt = self.clock.get_time()
        mouse_pos = pygame.mouse.get_pos()
        
        self.cannon.update(mouse_pos, dt)
        self.garden.update()
        
        # Спавн зомби
        self.spawn_timer += dt
        if self.spawn_timer > 2000:  # Каждые 2 сек
            self.spawn_zombie()
            self.spawn_timer = 0
        
        # Обновление зомби
        for zombie in self.zombies[:]:
            zombie.update(dt, self.cannon.x)
            if zombie.health <= 0:
                self.zombies.remove(zombie)
        
        # Обновление снарядов
        for proj in self.projectiles[:]:
            if isinstance(proj, list):
                for p in proj[:]:
                    p.update(dt, self.zombies)
                    if not p.alive:
                        proj.remove(p)
                if not proj:
                    self.projectiles.remove(proj)
            else:
                proj.update(dt, self.zombies)
                if not proj.alive:
                    self.projectiles.remove(proj)
        
        # Проверка клика на огород
        if pygame.mouse.get_pressed()[0] and math.hypot(mouse_pos[0] - self.garden.x, mouse_pos[1] - self.garden.y) < 20:
            self.garden.care()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левый клик — стрельба
                    harvested = False
                    if self.shoot_type == 'cabbage' and self.garden.harvest('cabbage'):
                        proj = self.cannon.shoot('cabbage', self.terrain)
                        if proj:
                            self.projectiles.append(proj)
                        harvested = True
                    elif self.shoot_type == 'carrot' and self.garden.harvest('carrot'):
                        projs = self.cannon.shoot('carrot', self.terrain)
                        if projs:
                            self.projectiles.append(projs)
                        harvested = True
                    if not harvested:
                        print("Нет урожая! Уходите за огородом.")
                elif event.button == 3:  # Правый клик — переключить тип
                    self.shoot_type = 'carrot' if self.shoot_type == 'cabbage' else 'cabbage'
    
    def draw(self):
        self.screen.fill(WHITE)
        self.terrain.draw(self.screen)
        self.garden.draw(self.screen)
        self.cannon.draw(self.screen)
        
        for zombie in self.zombies:
            zombie.draw(self.screen)
        
        for proj in self.projectiles:
            if isinstance(proj, list):
                for p in proj:
                    p.draw(self.screen)
            else:
                proj.draw(self.screen)
        
        # Кролик (простой)
        pygame.draw.circle(self.screen, (200, 150, 100), (int(self.cannon.x - 10), int(self.cannon.y - 30)), 8)  # Голова
        pygame.draw.rect(self.screen, (150, 100, 50), (self.cannon.x - 15, self.cannon.y - 20, 30, 20))  # Тело
        
        # Инфо
        font = pygame.font.Font(None, 36)
        text = font.render(f"Тип: {self.shoot_type} (Правый клик - смена)", True, (0, 0, 0))
        self.screen.blit(text, (10, 10))
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()