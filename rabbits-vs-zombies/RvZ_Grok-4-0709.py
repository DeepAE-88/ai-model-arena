import time
import random
import math

# Константы
GRAVITY = 9.8  # м/с²
DRAG_COEFF = 0.1  # Коэффициент сопротивления воздуха
TIME_STEP = 0.1  # Шаг симуляции времени
FIELD_WIDTH = 100  # Ширина поля (м)
HILL_HEIGHT = 10  # Максимальная высота холма

class Rabbit:
    def __init__(self, type):
        self.type = type
        if type == "speedy":
            self.cannon_speed = 30  # Начальная скорость снаряда (м/с)
            self.garden_growth_rate = 0.5
            self.cannon_reload_time = 1
        elif type == "strong":
            self.cannon_speed = 40
            self.garden_growth_rate = 0.3
            self.cannon_reload_time = 3
        elif type == "farmer":
            self.cannon_speed = 25
            self.garden_growth_rate = 0.8
            self.cannon_reload_time = 2

class Garden:
    def __init__(self, growth_rate):
        self.beds = [{"type": "cabbage", "growth": 0, "ready": False} for _ in range(5)] + \
                    [{"type": "carrot", "growth": 0, "ready": False} for _ in range(5)]
        self.growth_rate = growth_rate
        self.weather = "normal"  # normal, rain, drought

    def update(self):
        multiplier = 1.5 if self.weather == "rain" else 0.5 if self.weather == "drought" else 1
        for bed in self.beds:
            if not bed["ready"]:
                bed["growth"] += self.growth_rate * multiplier * random.uniform(0.8, 1.2)
                if bed["growth"] >= 100:
                    bed["ready"] = True

    def water(self, bed_index):
        if 0 <= bed_index < len(self.beds):
            self.beds[bed_index]["growth"] += 20
            print(f"Полита грядка {bed_index}: Рост {self.beds[bed_index]['growth']:.1f}%")

    def harvest(self, bed_type):
        for bed in self.beds:
            if bed["type"] == bed_type and bed["ready"]:
                bed["growth"] = 0
                bed["ready"] = False
                return True
        return False

class Zombie:
    def __init__(self, type, position):
        self.type = type
        if type == "normal":
            self.hp = 100
            self.speed = 1
            self.armor = 0
        elif type == "conehead":
            self.hp = 100
            self.speed = 1
            self.armor = 50
        elif type == "fast":
            self.hp = 50
            self.speed = 3
            self.armor = 0
        elif type == "farmer":
            self.hp = 80
            self.speed = 2
            self.armor = 20
        self.position = position  # x от 0 (дом) до FIELD_WIDTH (спавн)

    def move(self):
        self.position -= self.speed + random.uniform(-0.5, 0.5)  # Зигзаг
        if self.position < 0:
            return True  # Добрался до дома
        return False

    def animate_move(self):
        print(f"{self.type} зомби движется: {'<' * int(self.speed)} позиция {self.position:.1f}m")

class Cannon:
    def __init__(self, speed, reload_time):
        self.angle = 45
        self.speed = speed
        self.reload_time = reload_time
        self.aim_time = 0
        self.wind = random.uniform(-5, 5)  # Ветер влияет на угол

    def aim(self, new_angle):
        self.angle = new_angle + self.wind
        self.aim_time = 0
        print(f"Пушка наведена на {self.angle:.1f}° (ветер: {self.wind:.1f}°)")

    def update_aim(self):
        self.aim_time += 1
        oscillation = math.sin(self.aim_time / 2) * (self.aim_time / 10)  # Амплитуда растёт
        self.angle += oscillation
        print(f"Пушка колеблется: текущий угол {self.angle:.1f}°")

    def shoot(self, proj_type, landscape):
        if proj_type == "cabbage":
            mass = 2  # кг
            aoe = False
        elif proj_type == "carrot":
            mass = 0.5
            aoe = True
        else:
            return None

        vx = self.speed * math.cos(math.radians(self.angle))
        vy = self.speed * math.sin(math.radians(self.angle))
        x, y = 0, landscape[0]  # Старт с позиции кролика (на холме)
        trajectory = []

        while y >= 0 and x < FIELD_WIDTH:
            trajectory.append((x, y))
            # Симуляция с drag
            drag_x = -DRAG_COEFF * vx**2 if vx > 0 else DRAG_COEFF * vx**2
            drag_y = -DRAG_COEFF * vy**2 if vy > 0 else DRAG_COEFF * vy**2
            vx += drag_x * TIME_STEP
            vy += (drag_y - GRAVITY) * TIME_STEP
            x += vx * TIME_STEP
            y += vy * TIME_STEP
            # Учёт ландшафта
            hill_y = landscape[int(x) % len(landscape)]
            if y <= hill_y:
                y = hill_y
                break

        # Анимация полёта
        for tx, ty in trajectory[::5]:  # Каждый 5-й шаг для скорости
            print(f"Снаряд летит: x={tx:.1f}, y={ty:.1f} {'↑' if vy > 0 else '↓'}")
            time.sleep(0.1)

        print(f"Попадание на x={x:.1f}m!")
        return {"type": proj_type, "impact_x": x, "impact_speed": math.sqrt(vx**2 + vy**2), "mass": mass, "aoe": aoe}

# Главная функция игры
def main():
    print("Добро пожаловать в 'Кролики против зомби'!")
    rabbit_type = input("Выберите кролика (speedy, strong, farmer): ").lower()
    rabbit = Rabbit(rabbit_type)
    garden = Garden(rabbit.garden_growth_rate)
    cannon = Cannon(rabbit.cannon_speed, rabbit.cannon_reload_time)
    zombies = []
    wave = 1
    score = 0
    landscape = [math.sin(i / 10) * HILL_HEIGHT for i in range(FIELD_WIDTH)]  # Холмистый ландшафт

    while True:
        # Обновление состояния
        garden.update()
        cannon.update_aim()
        garden.weather = random.choice(["normal", "rain", "drought"]) if random.random() < 0.1 else garden.weather
        print(f"\nХод {wave}. Погода: {garden.weather}. Счёт: {score}")
        print("Огород:")
        for i, bed in enumerate(garden.beds):
            status = "готов" if bed["ready"] else f"{bed['growth']:.1f}%"
            print(f"Грядка {i}: {bed['type']} - {status}")
        print("Зомби:")
        for z in zombies:
            print(f"{z.type} на {z.position:.1f}m, HP: {z.hp + z.armor}")
        
        # Спавн зомби в новой волне
        if not zombies:
            print(f"Волна {wave}!")
            num_zombies = wave + 2
            for _ in range(num_zombies):
                z_type = random.choice(["normal", "conehead", "fast", "farmer"])
                zombies.append(Zombie(z_type, FIELD_WIDTH))
            wave += 1

        # Движение зомби
        to_remove = []
        for z in zombies:
            z.animate_move()
            if z.move():
                print("Зомби добрался до дома! Игра окончена.")
                return
            if random.random() < 0.05 and z.type == "farmer" and z.position < 20:
                print(f"{z.type} зомби крадёт овощ!")
                garden.beds[random.randint(0, len(garden.beds)-1)]["growth"] = 0

        # Ввод команды
        cmd = input("\nКоманда (aim <угол>, shoot <cabbage/carrot>, water <грядка>, harvest <cabbage/carrot>, quit): ").split()
        if not cmd:
            continue
        action = cmd[0]
        if action == "aim" and len(cmd) > 1:
            cannon.aim(float(cmd[1]))
        elif action == "shoot" and len(cmd) > 1:
            proj_type = cmd[1]
            if garden.harvest(proj_type):
                shot = cannon.shoot(proj_type, landscape)
                if shot:
                    impact_x = shot["impact_x"]
                    for z in zombies:
                        dist = abs(z.position - impact_x)
                        if (shot["aoe"] and dist < 10) or (not shot["aoe"] and dist < 2):
                            damage = shot["mass"] * shot["impact_speed"]  # Урон = импульс
                            z.armor = max(0, z.armor - damage)
                            if z.armor <= 0:
                                z.hp -= damage
                            print(f"Урон {damage:.1f} зомби {z.type}! HP: {z.hp + z.armor}")
                            if z.hp <= 0:
                                to_remove.append(z)
                                score += 10
        elif action == "water" and len(cmd) > 1:
            garden.water(int(cmd[1]))
        elif action == "harvest" and len(cmd) > 1:
            if garden.harvest(cmd[1]):
                print(f"Собран {cmd[1]} для пушки!")
        elif action == "quit":
            return

        # Удаление мёртвых зомби
        for z in to_remove:
            zombies.remove(z)
            print(f"{z.type} зомби уничтожен!")

if __name__ == "__main__":
    main()