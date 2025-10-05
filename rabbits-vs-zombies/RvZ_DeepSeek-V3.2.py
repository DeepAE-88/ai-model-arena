import pygame
import sys
import math
import random
from pygame import Vector2

class RabbitsVsZombies:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1200, 700))
        pygame.display.set_caption("Кролики против Зомби")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        # Игровые состояния
        self.cabbages = 10
        self.carrots = 5
        self.score = 0
        self.game_time = 0
        
        # Системы игры
        self.aiming_system = AimingSystem()
        self.projectile_physics = ProjectilePhysics()
        self.zombie_spawner = ZombieSpawner()
        
        # Игровые объекты
        self.projectiles = []
        self.zombies = []
        self.rabbit = Rabbit()
        self.garden = Garden()
        
        # Физические константы
        self.gravity = 980
        self.ground_level = 550
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEMOTION:
                self.aiming_system.update_mouse_pos(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.cabbages > 0:  # Левая кнопка - капуста
                    self.shoot_cabbage(event.pos)
                elif event.button == 3 and self.carrots > 0:  # Правая кнопка - морковь
                    self.shoot_carrots(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Перезарядка овощей
                    self.cabbages += 5
                    self.carrots += 3
        return True
    
    def shoot_cabbage(self, target_pos):
        start_pos = Vector2(100, self.ground_level - 20)
        power = self.aiming_system.get_shot_power()
        
        projectile = Projectile(
            type='cabbage',
            position=start_pos,
            target=Vector2(target_pos),
            power=power,
            mass=1.0
        )
        self.projectiles.append(projectile)
        self.cabbages -= 1
    
    def shoot_carrots(self, target_pos):
        start_pos = Vector2(100, self.ground_level - 20)
        power = self.aiming_system.get_shot_power()
        
        # Веерный залп из 5 морковок
        for i in range(5):
            spread = (i - 2) * 15  # Разброс по горизонтали
            adjusted_target = Vector2(target_pos[0] + spread, target_pos[1])
            
            projectile = Projectile(
                type='carrot',
                position=start_pos,
                target=adjusted_target,
                power=power * 0.8,  # Меньшая мощность для веерного выстрела
                mass=0.3
            )
            self.projectiles.append(projectile)
        
        self.carrots -= 1
    
    def update(self, dt):
        self.game_time += dt
        
        # Обновление систем
        self.aiming_system.update(dt)
        self.zombie_spawner.update(dt, self.zombies)
        self.garden.update(dt)
        
        # Обновление снарядов
        for projectile in self.projectiles[:]:
            projectile.update(dt, self.projectile_physics)
            
            # Проверка столкновений со зомби
            for zombie in self.zombies[:]:
                if projectile.check_collision(zombie):
                    damage = projectile.calculate_damage()
                    zombie.take_damage(damage)
                    
                    # Эффект попадания
                    if projectile.type == 'carrot':
                        self.create_explosion_effect(projectile.position)
                    
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    break
            
            # Удаление снарядов за пределами экрана
            if (projectile.position.x > 1300 or projectile.position.x < -100 or 
                projectile.position.y > 800):
                if projectile in self.projectiles:
                    self.projectiles.remove(projectile)
        
        # Обновление зомби
        for zombie in self.zombies[:]:
            zombie.update(dt)
            if zombie.health <= 0:
                self.zombies.remove(zombie)
                self.score += zombie.points
                # Шанс выпадения овоща
                if random.random() < 0.3:
                    self.cabbages += 1
                if random.random() < 0.2:
                    self.carrots += 1
        
        # Автоматическое пополнение овощей из огорода
        if self.game_time % 10 < dt:  # Каждые 10 секунд
            harvest = self.garden.harvest()
            self.cabbages += harvest['cabbages']
            self.carrots += harvest['carrots']
    
    def create_explosion_effect(self, position):
        # Создание частиц для эффекта взрыва моркови
        for _ in range(8):
            particle = {
                'position': Vector2(position),
                'velocity': Vector2(random.uniform(-200, 200), random.uniform(-200, 0)),
                'lifetime': random.uniform(0.5, 1.5),
                'color': (255, 165, 0)
            }
            # В реальной реализации нужно добавить систему частиц
    
    def render(self):
        # Фон
        self.screen.fill((135, 206, 235))  # Небесный голубой
        
        # Отрисовка ландшафта
        self.draw_landscape()
        
        # Отрисовка огорода
        self.garden.draw(self.screen)
        
        # Отрисовка зомби
        for zombie in self.zombies:
            zombie.draw(self.screen)
        
        # Отрисовка снарядов
        for projectile in self.projectiles:
            projectile.draw(self.screen)
        
        # Отрисовка кролика и пушки
        self.rabbit.draw(self.screen)
        
        # Отрисовка прицела
        self.aiming_system.draw(self.screen)
        
        # Отрисовка UI
        self.draw_ui()
    
    def draw_landscape(self):
        # Холмистый ландшафт с использованием синусоиды
        points = [(0, self.ground_level)]
        for x in range(0, 1201, 20):
            y = self.ground_level + math.sin(x / 100) * 30 + math.cos(x / 50) * 15
            points.append((x, y))
        points.append((1200, 700))
        points.append((0, 700))
        
        pygame.draw.polygon(self.screen, (34, 139, 34), points)  # Зеленый холм
        
        # Трава
        for x in range(0, 1201, 10):
            height = random.randint(5, 15)
            pygame.draw.line(self.screen, (0, 128, 0), 
                           (x, self.ground_level), 
                           (x, self.ground_level - height), 2)
    
    def draw_ui(self):
        # Панель боеприпасов
        cabbage_text = self.font.render(f"🥬: {self.cabbages}", True, (0, 100, 0))
        carrot_text = self.font.render(f"🥕: {self.carrots}", True, (255, 140, 0))
        score_text = self.font.render(f"Очки: {self.score}", True, (0, 0, 0))
        time_text = self.font.render(f"Время: {int(self.game_time)}с", True, (0, 0, 0))
        
        self.screen.blit(cabbage_text, (10, 10))
        self.screen.blit(carrot_text, (10, 50))
        self.screen.blit(score_text, (1000, 10))
        self.screen.blit(time_text, (1000, 50))
        
        # Подсказки
        hint_text = self.font.render("ЛКМ - капуста | ПКМ - морковь | R - перезарядка", True, (50, 50, 50))
        self.screen.blit(hint_text, (400, 10))
    
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0  # Delta time в секундах
            
            running = self.handle_events()
            self.update(dt)
            self.render()
            pygame.display.flip()

class AimingSystem:
    def __init__(self):
        self.mouse_pos = Vector2(0, 0)
        self.hold_time = 0
        self.shake_intensity = 0
        self.aim_pos = Vector2(0, 0)
        self.stability_periods = []  # Периоды стабильности
        
    def update_mouse_pos(self, pos):
        self.mouse_pos = Vector2(pos)
        
    def update(self, dt):
        self.hold_time += dt
        
        # Увеличение дрожи со временем удержания (логарифмический рост)
        self.shake_intensity = min(1.0, math.log(self.hold_time + 1) / 3.0)
        
        # Случайная дрожь
        shake_x = random.uniform(-1, 1) * 50 * self.shake_intensity
        shake_y = random.uniform(-1, 1) * 30 * self.shake_intensity
        
        # Периоды стабильности (мини-игра)
        current_time = pygame.time.get_ticks() / 1000.0
        stability = math.sin(current_time * 5)  # 5 Hz колебание
        
        # Если в фазе стабильности, уменьшаем дрожь
        if stability > 0.7:
            shake_x *= 0.3
            shake_y *= 0.3
        
        self.aim_pos = Vector2(
            self.mouse_pos.x + shake_x,
            self.mouse_pos.y + shake_y
        )
    
    def get_shot_power(self):
        # Мощность выстрела зависит от стабильности прицела
        stability = 1.0 - self.shake_intensity
        base_power = 0.5 + stability * 0.5  # От 50% до 100% мощности
        
        self.hold_time = 0  # Сброс после выстрела
        return base_power
    
    def draw(self, screen):
        center = (int(self.aim_pos.x), int(self.aim_pos.y))
        
        # Цвет прицела в зависимости от стабильности
        red = min(255, int(255 * self.shake_intensity))
        green = 255 - red
        color = (red, green, 0)
        
        # Внешнее кольцо прицела
        radius = 20 + int(10 * self.shake_intensity)
        pygame.draw.circle(screen, color, center, radius, 2)
        
        # Перекрестие
        cross_size = 15 + int(5 * self.shake_intensity)
        pygame.draw.line(screen, color, 
                        (center[0]-cross_size, center[1]), 
                        (center[0]+cross_size, center[1]), 2)
        pygame.draw.line(screen, color, 
                        (center[0], center[1]-cross_size), 
                        (center[0], center[1]+cross_size), 2)
        
        # Точка в центре
        pygame.draw.circle(screen, color, center, 3)

class ProjectilePhysics:
    def __init__(self):
        self.gravity = 980
        self.air_density = 0.001
        self.drag_coefficient_cabbage = 0.3   # Капуста более аэродинамична
        self.drag_coefficient_carrot = 0.6    # Морковь хуже летит
        
    def update_projectile(self, projectile, dt):
        velocity = projectile.velocity
        position = projectile.position
        
        # Сила тяжести
        velocity.y += self.gravity * dt
        
        # Сопротивление воздуха (квадратичная модель)
        speed = velocity.length()
        if speed > 0:
            drag_coeff = (self.drag_coefficient_cabbage if projectile.type == 'cabbage' 
                         else self.drag_coefficient_carrot)
            drag_force = 0.5 * self.air_density * speed**2 * drag_coeff
            drag_acceleration = drag_force / projectile.mass
            
            # Направление противоположно скорости
            drag_direction = -velocity.normalize()
            velocity += drag_direction * drag_acceleration * dt
        
        # Обновление позиции
        position += velocity * dt

class Projectile:
    def __init__(self, type, position, target, power, mass):
        self.type = type
        self.position = Vector2(position)
        self.mass = mass
        self.velocity = self.calculate_initial_velocity(target, power)
        self.creation_time = pygame.time.get_ticks()
        
    def calculate_initial_velocity(self, target, power):
        direction = (target - self.position).normalize()
        base_speed = 600 * power  # Базовая скорость с учетом мощности
        
        # Добавляем небольшую случайность для реализма
        angle_variation = random.uniform(-0.1, 0.1)
        direction = direction.rotate(angle_variation)
        
        return direction * base_speed
    
    def update(self, dt, physics):
        physics.update_projectile(self, dt)
    
    def check_collision(self, zombie):
        distance = (self.position - zombie.position).length()
        collision_radius = 25 if self.type == 'cabbage' else 20
        return distance < (collision_radius + zombie.radius)
    
    def calculate_damage(self):
        # Урон пропорционален импульсу (масса × скорость)
        momentum = self.velocity.length() * self.mass
        
        if self.type == 'cabbage':
            return momentum * 0.15  # Высокий урон по одной цели
        else:
            return momentum * 0.08  # Меньший урон, но по площади
    
    def draw(self, screen):
        if self.type == 'cabbage':
            # Рисуем капусту
            color = (0, 180, 0)
            radius = 12
            pygame.draw.circle(screen, color, (int(self.position.x), int(self.position.y)), radius)
            # Текстура капусты
            for i in range(4):
                angle = i * math.pi / 2
                leaf_x = self.position.x + math.cos(angle) * radius * 0.7
                leaf_y = self.position.y + math.sin(angle) * radius * 0.7
                pygame.draw.circle(screen, (0, 220, 0), (int(leaf_x), int(leaf_y)), radius//2)
        else:
            # Рисуем морковь
            color = (255, 140, 0)
            points = [
                (self.position.x, self.position.y - 15),  # Верх
                (self.position.x - 8, self.position.y + 10),  # Левый низ
                (self.position.x + 8, self.position.y + 10)   # Правый низ
            ]
            pygame.draw.polygon(screen, color, points)
            # Зелень моркови
            pygame.draw.line(screen, (0, 180, 0), 
                           (self.position.x, self.position.y - 15),
                           (self.position.x - 5, self.position.y - 25), 2)
            pygame.draw.line(screen, (0, 180, 0), 
                           (self.position.x, self.position.y - 15),
                           (self.position.x + 5, self.position.y - 25), 2)

class Zombie:
    def __init__(self, zombie_type="normal"):
        self.type = zombie_type
        self.setup_stats()
        self.position = Vector2(1250, 530)  # Начальная позиция справа
        self.velocity = Vector2(-self.speed, 0)
        self.animation_time = 0
        self.frame = 0
        self.radius = 25
        self.attack_cooldown = 0
        
    def setup_stats(self):
        stats = {
            "normal": {"health": 100, "speed": 25, "armor": 0.0, "points": 10},
            "armored": {"health": 200, "speed": 18, "armor": 0.6, "points": 25},
            "athlete": {"health": 80, "speed": 40, "armor": 0.2, "points": 15},
            "giant": {"health": 400, "speed": 12, "armor": 0.8, "points": 50}
        }
        
        self.health = stats[self.type]["health"]
        self.max_health = self.health
        self.speed = stats[self.type]["speed"]
        self.armor = stats[self.type]["armor"]
        self.points = stats[self.type]["points"]
    
    def take_damage(self, damage):
        actual_damage = max(1, damage * (1 - self.armor))
        self.health -= actual_damage
        
        # Эффект получения урона
        self.velocity.x *= 0.5  # Замедление при ударе
    
    def update(self, dt):
        self.position += self.velocity * dt
        self.animation_time += dt
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        
        # Анимация ходьбы
        if self.animation_time > 0.15:
            self.frame = (self.frame + 1) % 4
            self.animation_time = 0
        
        # Если дошел до левого края - атакует базу
        if self.position.x < 50:
            self.attack_base()
    
    def attack_base(self):
        if self.attack_cooldown <= 0:
            # В реальной игре здесь бы отнимались жизни
            self.attack_cooldown = 1.0  # Атака раз в секунду
    
    def draw(self, screen):
        # Цвет в зависимости от типа
        colors = {
            "normal": (150, 150, 150),
            "armored": (100, 50, 0),
            "athlete": (50, 150, 50),
            "giant": (80, 0, 0)
        }
        color = colors.get(self.type, (150, 150, 150))
        
        # Тело зомби
        body_height = 60 if self.type != "giant" else 90
        body_width = 40 if self.type != "giant" else 60
        body_rect = pygame.Rect(
            self.position.x - body_width//2, 
            self.position.y - body_height//2, 
            body_width, 
            body_height
        )
        pygame.draw.rect(screen, color, body_rect)
        
        # Голова
        head_radius = 15 if self.type != "giant" else 22
        head_pos = (int(self.position.x), int(self.position.y - body_height//2 - head_radius//2))
        pygame.draw.circle(screen, (200, 150, 150), head_pos, head_radius)
        
        # Анимация ног
        leg_offsets = [10, 5, -5, -10]
        leg_offset = leg_offsets[self.frame]
        
        # Ноги
        leg_start_y = self.position.y + body_height//2 - 10
        pygame.draw.line(screen, (50, 50, 50), 
                        (self.position.x - 10, leg_start_y),
                        (self.position.x - 10 + leg_offset, leg_start_y + 20), 4)
        pygame.draw.line(screen, (50, 50, 50), 
                        (self.position.x + 10, leg_start_y),
                        (self.position.x + 10 - leg_offset, leg_start_y + 20), 4)
        
        # Руки (только для больших типов)
        if self.type in ["giant", "armored"]:
            arm_offset = leg_offset * 0.7
            arm_start_y = self.position.y - body_height//4
            pygame.draw.line(screen, (50, 50, 50), 
                            (self.position.x - 15, arm_start_y),
                            (self.position.x - 25 + arm_offset, arm_start_y - 10), 4)
            pygame.draw.line(screen, (50, 50, 50), 
                            (self.position.x + 15, arm_start_y),
                            (self.position.x + 25 - arm_offset, arm_start_y - 10), 4)
        
        # Полоска здоровья
        health_width = body_width * (self.health / self.max_health)
        health_rect = pygame.Rect(
            self.position.x - body_width//2, 
            self.position.y - body_height//2 - 10, 
            health_width, 5
        )
        health_color = (0, 255, 0) if self.health > self.max_health * 0.6 else (
            (255, 255, 0) if self.health > self.max_health * 0.3 else (255, 0, 0)
        )
        pygame.draw.rect(screen, health_color, health_rect)

class ZombieSpawner:
    def __init__(self):
        self.spawn_timer = 0
        self.spawn_interval = 4.0
        self.wave = 1
        self.zombies_spawned = 0
        
    def update(self, dt, zombies):
        self.spawn_timer += dt
        
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_zombie(zombies)
            self.spawn_timer = 0
            self.zombies_spawned += 1
            
            # Увеличиваем сложность
            if self.zombies_spawned % 5 == 0:
                self.spawn_interval = max(1.0, self.spawn_interval * 0.9)
                self.wave += 1
    
    def spawn_zombie(self, zombies):
        # Вероятности появления в зависимости от волны
        if self.wave == 1:
            types = ["normal"] * 8 + ["athlete"] * 2
        elif self.wave == 2:
            types = ["normal"] * 6 + ["athlete"] * 3 + ["armored"] * 1
        else:
            types = ["normal"] * 4 + ["athlete"] * 3 + ["armored"] * 2 + ["giant"] * 1
        
        zombie_type = random.choice(types)
        zombies.append(Zombie(zombie_type))

class Rabbit:
    def __init__(self):
        self.position = Vector2(100, 530)
        self.type = "bucks"
        
    def draw(self, screen):
        # Тело кролика
        body_rect = pygame.Rect(self.position.x - 25, self.position.y - 15, 50, 30)
        pygame.draw.ellipse(screen, (240, 240, 240), body_rect)
        
        # Голова
        head_rect = pygame.Rect(self.position.x - 20, self.position.y - 35, 40, 30)
        pygame.draw.ellipse(screen, (240, 240, 240), head_rect)
        
        # Уши
        pygame.draw.ellipse(screen, (240, 240, 240), 
                          (self.position.x - 15, self.position.y - 55, 12, 25))
        pygame.draw.ellipse(screen, (240, 240, 240), 
                          (self.position.x + 3, self.position.y - 55, 12, 25))
        
        # Глаза
        pygame.draw.circle(screen, (0, 0, 0), (int(self.position.x - 8), int(self.position.y - 25)), 3)
        pygame.draw.circle(screen, (0, 0, 0), (int(self.position.x + 8), int(self.position.y - 25)), 3)
        
        # Нос
        pygame.draw.circle(screen, (255, 150, 150), (int(self.position.x), int(self.position.y - 20)), 4)
        
        # Пушка
        pygame.draw.rect(screen, (100, 70, 30), 
                       (self.position.x + 25, self.position.y - 10, 40, 15))
        pygame.draw.circle(screen, (80, 60, 20), 
                         (int(self.position.x + 65), int(self.position.y - 2)), 8)

class Garden:
    def __init__(self):
        self.cabbages_ready = 0
        self.carrots_ready = 0
        self.grow_timer = 0
        self.position = Vector2(200, 500)
        
    def update(self, dt):
        self.grow_timer += dt
        
        # Овощи растут каждые 5 секунд
        if self.grow_timer >= 5:
            self.cabbages_ready += random.randint(1, 3)
            self.carrots_ready += random.randint(1, 2)
            self.grow_timer = 0
    
    def harvest(self):
        harvest = {
            'cabbages': self.cabbages_ready,
            'carrots': self.carrots_ready
        }
        self.cabbages_ready = 0
        self.carrots_ready = 0
        return harvest
    
    def draw(self, screen):
        # Грядка
        garden_rect = pygame.Rect(self.position.x - 100, self.position.y - 20, 200, 40)
        pygame.draw.rect(screen, (139, 69, 19), garden_rect)  # Коричневая земля
        
        # Капуста
        for i in range(min(self.cabbages_ready, 6)):
            x = self.position.x - 80 + i * 30
            pygame.draw.circle(screen, (0, 180, 0), (int(x), int(self.position.y - 10)), 12)
        
        # Морковь
        for i in range(min(self.carrots_ready, 4)):
            x = self.position.x - 40 + i * 40
            points = [
                (x, self.position.y - 15),
                (x - 6, self.position.y + 5),
                (x + 6, self.position.y + 5)
            ]
            pygame.draw.polygon(screen, (255, 140, 0), points)

if __name__ == "__main__":
    game = RabbitsVsZombies()
    game.run()