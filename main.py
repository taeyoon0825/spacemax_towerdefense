import pygame, sys, random, math
from pygame.locals import *

# ================= CONFIG =================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
BLUE = (0, 100, 255)
PURPLE = (170, 0, 255)
ORANGE = (255, 150, 0)
GOLD = (255, 215, 0)
RED = (255, 50, 50)
GREEN = (0, 255, 0)

RARITY_TABLE = {
    'common': 65.0,
    'rare': 20.3,
    'epic': 13.3,
    'legendary': 1.0,
    'mythic': 0.4
}

RARITY_KR = {
    'common': '일반',
    'rare': '희귀',
    'epic': '영웅',
    'legendary': '전설',
    'mythic': '신화'
}

RARITY_COLOR = {
    'common': (160, 160, 160),   # 회색
    'rare': (100, 200, 255),     # 하늘색
    'epic': (170, 0, 255),       # 보라색
    'legendary': (255, 215, 0),  # 노란색
    'mythic': (255, 50, 50)      # 빨간색
}



TOWER_STATS = {
    'common': {'damage': 20, 'rate': 1.0, 'color': GRAY},
    'rare': {'damage': 30, 'rate': 1.2, 'color': BLUE},
    'epic': {'damage': 45, 'rate': 1.4, 'color': PURPLE},
    'legendary': {'damage': 75, 'rate': 1.6, 'color': ORANGE},
    'mythic': {'damage': 125, 'rate': 2.0, 'color': GOLD}
}

ENEMY_BASE_HP = 100
ENEMY_SPEED = 1.0
BOSS_MULTIPLIER = 8

START_GOLD = 1000
KILL_REWARD = 25
SELL_REFUND_RATE = 0.5
PLAYER_HP = 5

pygame.font.init()
# 폰트 초기화 부분을 이렇게 교체
# 폰트 정의 부분 수정
FONT_SMALL = pygame.font.Font("C:/Windows/Fonts/malgun.ttf", 18)
FONT_SMALL.set_bold(True)

FONT_MEDIUM = pygame.font.Font("C:/Windows/Fonts/malgun.ttf", 24)
FONT_MEDIUM.set_bold(True)

FONT_LARGE = pygame.font.Font("C:/Windows/Fonts/malgun.ttf", 36)
FONT_LARGE.set_bold(True)


# ================= ENEMY CLASS =================
class Enemy(pygame.sprite.Sprite):
    def __init__(self, path, hp, speed, boss_type="normal"):
        super().__init__()
        self.path = path
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.boss_type = boss_type

        # 🐝 이미지 불러오기
        if boss_type == "mid":        # 중간보스
            self.image = pygame.image.load("bee2.png")
            self.image = pygame.transform.scale(self.image, (80, 80))
        elif boss_type == "main":     # 메인보스
            self.image = pygame.image.load("bee3.png")
            self.image = pygame.transform.scale(self.image, (100, 100))
        else:                         # 일반몹
            self.image = pygame.image.load("bee1.png")
            self.image = pygame.transform.scale(self.image, (60, 60))

        self.rect = self.image.get_rect()
        self.pos = list(path[0])
        self.path_index = 0


    def update(self):
        if self.path_index < len(self.path) - 1:
            target = self.path[self.path_index + 1]
            dx, dy = target[0] - self.pos[0], target[1] - self.pos[1]
            dist = math.hypot(dx, dy)
            if dist != 0:
                dx, dy = dx / dist, dy / dist
            self.pos[0] += dx * self.speed
            self.pos[1] += dy * self.speed
            if dist < 2:
                self.path_index += 1
            self.rect.center = self.pos

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        pygame.draw.rect(screen, BLACK, (self.rect.x, self.rect.y - 12, self.rect.width, 6))
        hp_ratio = max(self.hp / self.max_hp, 0)
        bar_width = self.rect.width * hp_ratio
        bar_color = GREEN if hp_ratio > 0.5 else ORANGE if hp_ratio > 0.25 else RED
        pygame.draw.rect(screen, bar_color, (self.rect.x, self.rect.y - 12, bar_width, 6))

# ================= BULLET CLASS =================
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target, damage):
        super().__init__()
        self.image = pygame.Surface((6,6))
        self.image.fill(GOLD)
        self.rect = self.image.get_rect(center=(x, y))
        self.target = target
        self.speed = 9
        self.damage = damage

    def update(self):
        if not self.target or self.target.hp <= 0:
            self.kill()
            return
        dx, dy = self.target.rect.centerx - self.rect.centerx, self.target.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist == 0:
            self.target.hp -= self.damage
            self.kill()
            return
        dx, dy = dx / dist, dy / dist
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        if dist < 10:
            self.target.hp -= self.damage
            self.kill()

# ================= TOWER CLASS =================
# ================= TOWER CLASS =================
class Tower(pygame.sprite.Sprite):
    def __init__(self, x, y, rarity, gold_value):
        super().__init__()
        self.rarity = rarity
        stat = TOWER_STATS[rarity]
        self.damage = stat['damage']
        self.rate = stat['rate']
        self.color = stat['color']
        self.gold_value = gold_value
        self.range = 175
        self.last_shot = 0
        self.level = 1
        self.dragging = False

        # 🏰 등급별 이미지 파일 (일단 파일명 예시)
        image_file = {
            'common': 'minion1.png',
            'rare': 'minion2.png',
            'epic': 'minion3.png',
            'legendary': 'vairon.png',
            'mythic': 'dragon.png'
        }[rarity]

        # 🧩 등급별 크기 조정 (10씩 증가)
        size_table = {
            'common': (50, 50),
            'rare': (60, 60),
            'epic': (70, 70),
            'legendary': (110, 110),
            'mythic': (150, 150)
        }

        self.image = pygame.image.load(image_file)
        self.image = pygame.transform.scale(self.image, size_table[rarity])
        self.rect = self.image.get_rect(center=(x, y))


    def upgrade(self):
        self.damage += 7 + self.level
        self.range += 5
        self.level += 1

    def sell_value(self):
        return int(self.gold_value * SELL_REFUND_RATE)

    def update(self, enemies, bullets, time):
        if time - self.last_shot > 1000 / self.rate:
            target = self.find_target(enemies)
            if target:
                bullet = Bullet(self.rect.centerx, self.rect.centery, target, self.damage)
                bullets.add(bullet)
                self.last_shot = time

    def find_target(self, enemies):
        for enemy in enemies:
            if math.hypot(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery) < self.range:
                return enemy
        return None

    def draw(self, screen):
        pygame.draw.circle(screen, (100,100,100), self.rect.center, self.range, 1)
        screen.blit(self.image, self.rect)

# ================= WAVE MANAGER =================
class WaveManager:
    def __init__(self):
        self.stage = 1
        self.spawn_timer = 0
        self.enemies_to_spawn = 0

    def start_wave(self):
        self.enemies_to_spawn = 5 + self.stage * 2

    def spawn_enemy(self, enemies, path):
        if self.enemies_to_spawn > 0:
            hp = ENEMY_BASE_HP + (self.stage * 60)
            boss_type = "normal"

            # 마지막 적만 보스로 설정
            if self.enemies_to_spawn == 1:
                stage_last = self.stage % 10
                if stage_last == 5:
                    boss_type = "mid"
                    hp *= BOSS_MULTIPLIER
                elif stage_last == 0:
                    boss_type = "main"
                    hp *= (BOSS_MULTIPLIER * 1.5)

            enemy = Enemy(path, hp, ENEMY_SPEED, boss_type)
            enemies.add(enemy)
            self.enemies_to_spawn -= 1

    def next_stage(self):
        self.stage += 1
        self.start_wave()

# ================= HELPER =================
def get_random_rarity():
    roll = random.uniform(0, 100)
    cumulative = 0
    for rarity, chance in RARITY_TABLE.items():
        cumulative += chance
        if roll <= cumulative:
            return rarity
    return 'common'

# ================= MAIN GAME =================
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Spacemax Tower Defense')
    clock = pygame.time.Clock()

    background = pygame.image.load("map.png")
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

    path = [
        (0, 600), (200, 600),
        (200, 400), (400, 400),
        (400, 200), (600, 200),
        (600, 400), (800, 400),
        (800, 600), (1000, 600),
        (1280, 600)
    ]

    enemies = pygame.sprite.Group()
    towers = pygame.sprite.Group()
    bullets = pygame.sprite.Group()

    wave = WaveManager()
    gold = START_GOLD
    hp = PLAYER_HP
    selected_tower = None
    wave.start_wave()

    running = True
    while running:
        dt = clock.tick(FPS)
        time_now = pygame.time.get_ticks()

        if hp <= 0:
            game_over_text = FONT_LARGE.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2))
            pygame.display.flip()
            pygame.time.delay(3000)
            pygame.quit()
            sys.exit()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()

            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for t in towers:
                    if t.rect.collidepoint(mx, my):
                        selected_tower = t
                        t.dragging = True
                        break
                else:
                    rarity = get_random_rarity()
                    cost = 100
                    if gold >= cost:
                        tower = Tower(mx, my, rarity, cost)
                        towers.add(tower)
                        gold -= cost

            elif event.type == MOUSEBUTTONUP and event.button == 1:
                for t in towers:
                    t.dragging = False

            elif event.type == MOUSEMOTION:
                for t in towers:
                    if t.dragging:
                        t.rect.center = event.pos

            elif event.type == MOUSEBUTTONDOWN and event.button == 3 and selected_tower:
                gold += selected_tower.sell_value()
                selected_tower.kill()
                selected_tower = None

            elif event.type == KEYDOWN and event.key == K_u and selected_tower:
                cost = 10 * selected_tower.level
                if gold >= cost:
                    gold -= cost
                    selected_tower.upgrade()

        # UPDATE
        enemies.update()
        bullets.update()
        for tower in towers:
            if not tower.dragging:
                tower.update(enemies, bullets, time_now)

        for enemy in list(enemies):
            if enemy.hp <= 0:
                gold += KILL_REWARD
                enemy.kill()
            elif enemy.path_index >= len(path) - 1:
                hp -= 1
                enemy.kill()

        if len(enemies) == 0 and wave.enemies_to_spawn == 0:
            if wave.stage >= 30:
                win_text = FONT_LARGE.render("YOU WIN!", True, GOLD)
                screen.blit(win_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2))
                pygame.display.flip()
                pygame.time.delay(3000)
                pygame.quit()
                sys.exit()
            else:
                wave.next_stage()

        wave.spawn_timer += dt
        if wave.spawn_timer > 1000:
            wave.spawn_enemy(enemies, path)
            wave.spawn_timer = 0

        # DRAW
        screen.blit(background, (0, 0))
        # pygame.draw.lines(screen, WHITE, False, path, 5)

        for enemy in enemies:
            enemy.draw(screen)
        bullets.draw(screen)
        for tower in towers:
            tower.draw(screen)

        gold_text = FONT_MEDIUM.render(f'Gold: {gold}', True, WHITE)
        stage_text = FONT_MEDIUM.render(f'Stage: {wave.stage}', True, WHITE)
        hp_text = FONT_MEDIUM.render(f'HP: {hp}', True, WHITE)
        screen.blit(gold_text, (10, 10))
        screen.blit(stage_text, (10, 40))
        screen.blit(hp_text, (10, 70))

        if selected_tower:
            rarity_kr = RARITY_KR.get(selected_tower.rarity, selected_tower.rarity)
            rarity_color = RARITY_COLOR.get(selected_tower.rarity, WHITE)
            info = FONT_SMALL.render(
                f'{rarity_kr} Lv{selected_tower.level} 공격력:{selected_tower.damage}',
                True, rarity_color
            )
            screen.blit(info, (selected_tower.rect.x - 20, selected_tower.rect.y - 30))



        pygame.display.flip()

if __name__ == '__main__':
    main()
