import os
import pygame

pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60
TILE_SIZE = 64
LEVEL_WIDTH = 3200

LEVEL_BOTTOM = SCREEN_HEIGHT - 30

GRAVITY = 0.55
JUMP_STRENGTH = -13

WHITE = (245, 245, 245)
BLACK = (10, 10, 10)
GREEN = (0, 180, 0)
RED = (200, 35, 35)
GOLD = (240, 195, 40)
BROWN = (112, 78, 38)
SKY_BLUE = (90, 170, 255)
DARK_BLUE = (35, 70, 130)
GRAY = (90, 90, 90)
LEVEL_COUNT = 3
MENU_BG_PATH = "assets/Background/background4.jpg"
LEVEL_BG_PATHS = [
    "assets/Background/background1.jpg",
    "assets/Background/background2.jpg",
    "assets/Background/background3.jpg",
]

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pathfinder - Platformer Level")
clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


def safe_load_image(relative_path, fallback_size, fallback_color):
    full_path = os.path.join(BASE_DIR, relative_path)
    try:
        image = pygame.image.load(full_path).convert_alpha()
        return image
    except Exception:
        surf = pygame.Surface(fallback_size, pygame.SRCALPHA)
        surf.fill(fallback_color)
        return surf


def safe_load_music(relative_path):
    full_path = os.path.join(BASE_DIR, relative_path)
    try:
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(-1)
    except Exception:
        pass


def safe_load_sound(relative_path):
    full_path = os.path.join(BASE_DIR, relative_path)
    try:
        return pygame.mixer.Sound(full_path)
    except Exception:
        return None


def play_music(relative_path, volume=0.35, loop=-1):
    full_path = os.path.join(BASE_DIR, relative_path)
    try:
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loop)
    except Exception:
        pass


def draw_background(image):
    if image:
        bg = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(bg, (0, 0))
    else:
        draw_parallax_background(0)


def draw_button(text, x, y, width, height, color, hover_color, font):
    rect = pygame.Rect(x, y, width, height)
    mouse = pygame.mouse.get_pos()
    mouse_down = pygame.mouse.get_pressed()[0]
    hovered = rect.collidepoint(mouse)
    pygame.draw.rect(screen, hover_color if hovered else color, rect, border_radius=12)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=12)
    text_surface = font.render(text, True, WHITE)
    screen.blit(text_surface, text_surface.get_rect(center=rect.center))
    return hovered and mouse_down


def get_image(sheet, frame, width, height, scale, y_offset):
    image = pygame.Surface((width, height), pygame.SRCALPHA)
    image.blit(sheet, (0, 0), (frame * width, y_offset, width, height))
    return pygame.transform.scale(image, (int(width * scale), int(height * scale)))


def draw_parallax_background(camera_x):
    for i in range(2):
        layer_rect = pygame.Rect(i * SCREEN_WIDTH, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(screen, SKY_BLUE, layer_rect)
    pygame.draw.circle(
        screen,
        (255, 235, 120),
        (SCREEN_WIDTH - 120 - int(camera_x * 0.03), 90),
        50,
    )
    for idx in range(5):
        cloud_x = (idx * 260 - int(camera_x * 0.2)) % (SCREEN_WIDTH + 260) - 130
        pygame.draw.ellipse(screen, WHITE, (cloud_x, 80 + (idx % 2) * 70, 120, 45))
    pygame.draw.rect(screen, DARK_BLUE, (0, SCREEN_HEIGHT - 200, SCREEN_WIDTH, 200))


class Player:
    def __init__(self, x, y, sprite_sheet):
        self.sprite_sheet = sprite_sheet
        self.animations = {
            "idle": (10, 128),
            "run": (10, 768),
            "jump": (6, 1280),
            "fall": (4, 1408),
        }
        self.anim_lists = {}
        for action_name, (frames, y_offset) in self.animations.items():
            self.anim_lists[action_name] = [
                get_image(sprite_sheet, i, 128, 128, 0.95, y_offset) for i in range(frames)
            ]

        self.current_action = "idle"
        self.direction = "right"
        self.frame = 0
        self.anim_cooldown = 90
        self.last_update = pygame.time.get_ticks()

        self.start_pos = pygame.Vector2(x, y)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.speed = 5.2
        self.on_ground = False
        self.lives = 3

        self.image = self.anim_lists["idle"][0]
        self.rect = self.image.get_rect(topleft=(x, y))

    def respawn(self):
        self.pos.x = self.start_pos.x
        self.pos.y = self.start_pos.y
        self.vel.x = 0
        self.vel.y = 0
        self.on_ground = False

    def update_animation(self):
        now = pygame.time.get_ticks()
        if now - self.last_update >= self.anim_cooldown:
            self.last_update = now
            self.frame = (self.frame + 1) % len(self.anim_lists[self.current_action])

    def set_action(self, action):
        if action != self.current_action:
            self.current_action = action
            self.frame = 0

    def handle_input(self, keys):
        self.vel.x = 0
        if keys[pygame.K_LEFT]:
            self.vel.x = -self.speed
            self.direction = "left"
        elif keys[pygame.K_RIGHT]:
            self.vel.x = self.speed
            self.direction = "right"

    def jump(self):
        if self.on_ground:
            self.vel.y = JUMP_STRENGTH
            self.on_ground = False

    def update(self, platforms):
        self.vel.y += GRAVITY
        if self.vel.y > 15:
            self.vel.y = 15

        self.pos.x += self.vel.x
        self.rect.x = int(self.pos.x)
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel.x > 0:
                    self.rect.right = platform.left
                elif self.vel.x < 0:
                    self.rect.left = platform.right
                self.pos.x = self.rect.x

        self.pos.y += self.vel.y
        self.rect.y = int(self.pos.y)
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel.y > 0:
                    self.rect.bottom = platform.top
                    self.on_ground = True
                elif self.vel.y < 0:
                    self.rect.top = platform.bottom
                self.vel.y = 0
                self.pos.y = self.rect.y

        if self.vel.y < -1:
            self.set_action("jump")
        elif self.vel.y > 1 and not self.on_ground:
            self.set_action("fall")
        elif abs(self.vel.x) > 0.1:
            self.set_action("run")
        else:
            self.set_action("idle")

        self.update_animation()
        image = self.anim_lists[self.current_action][self.frame]
        if self.direction == "left":
            image = pygame.transform.flip(image, True, False)
        self.image = image

    def draw(self, surface, camera_x):
        surface.blit(self.image, (self.rect.x - camera_x, self.rect.y))


def build_level(level_index):
    levels = [
        {
            "background": LEVEL_BG_PATHS[0],
            "platforms": [
                pygame.Rect(20, 120, 140, 40),
                pygame.Rect(220, 120, 140, 40),
                pygame.Rect(420, 120, 140, 40),
                pygame.Rect(620, 120, 140, 40),
                pygame.Rect(820, 120, 140, 40),
                pygame.Rect(1020, 120, 140, 40),
                pygame.Rect(1220, 120, 140, 40),
                pygame.Rect(1420, 120, 140, 40),
                pygame.Rect(1620, 120, 140, 40),
                pygame.Rect(1820, 120, 140, 40),
                pygame.Rect(2020, 120, 140, 40),
                pygame.Rect(2220, 120, 140, 40),
                pygame.Rect(2420, 120, 140, 40),
                pygame.Rect(2620, 120, 140, 40),
                pygame.Rect(2820, 120, 140, 40),
                pygame.Rect(220, 240, 120, 40),
                pygame.Rect(520, 280, 120, 40),
                pygame.Rect(840, 220, 120, 40),
                pygame.Rect(1160, 260, 120, 40),
                pygame.Rect(1480, 220, 120, 40),
                pygame.Rect(1780, 260, 120, 40),
                pygame.Rect(2080, 240, 120, 40),
                pygame.Rect(2380, 280, 120, 40),
                pygame.Rect(2720, 520, 140, 40),
                pygame.Rect(2960, 520, 140, 40),
            ],
            "spikes": [
                pygame.Rect(180, 160, 60, 20),
                pygame.Rect(500, 320, 60, 20),
                pygame.Rect(900, 240, 60, 20),
                pygame.Rect(1280, 300, 60, 20),
                pygame.Rect(1700, 280, 60, 20),
                pygame.Rect(2120, 260, 60, 20),
                pygame.Rect(2500, 300, 60, 20),
            ],
            "coins": [
                pygame.Rect(80, 80, 22, 22),
                pygame.Rect(280, 80, 22, 22),
                pygame.Rect(520, 80, 22, 22),
                pygame.Rect(760, 80, 22, 22),
                pygame.Rect(1020, 80, 22, 22),
                pygame.Rect(1260, 80, 22, 22),
                pygame.Rect(1500, 80, 22, 22),
                pygame.Rect(1740, 80, 22, 22),
                pygame.Rect(1980, 80, 22, 22),
                pygame.Rect(2220, 80, 22, 22),
                pygame.Rect(2460, 80, 22, 22),
                pygame.Rect(2700, 80, 22, 22),
            ],
            "chests": [
                pygame.Rect(1840, 200, 34, 30),
                pygame.Rect(2940, 480, 34, 30),
            ],
            "start_flag": pygame.Rect(40, 80, 28, 40),
            "exit_door": pygame.Rect(2960, 460, 50, 80),
        },
        {
            "background": LEVEL_BG_PATHS[1],
            "platforms": [
                pygame.Rect(0, 560, 320, 60),
                pygame.Rect(380, 520, 140, 60),
                pygame.Rect(560, 560, 220, 60),
                pygame.Rect(860, 520, 120, 60),
                pygame.Rect(1000, 560, 200, 60),
                pygame.Rect(1260, 520, 140, 60),
                pygame.Rect(1480, 560, 180, 60),
                pygame.Rect(1740, 520, 140, 60),
                pygame.Rect(1960, 560, 220, 60),
                pygame.Rect(2240, 520, 140, 60),
                pygame.Rect(2420, 560, 240, 60),
                pygame.Rect(2700, 560, 220, 60),
            ],
            "spikes": [
                pygame.Rect(340, 545, 60, 25),
                pygame.Rect(620, 545, 60, 25),
                pygame.Rect(880, 505, 60, 25),
                pygame.Rect(1130, 545, 60, 25),
                pygame.Rect(1630, 545, 60, 25),
                pygame.Rect(2270, 545, 60, 25),
            ],
            "coins": [
                pygame.Rect(240, 500, 22, 22),
                pygame.Rect(520, 480, 22, 22),
                pygame.Rect(700, 500, 22, 22),
                pygame.Rect(980, 460, 22, 22),
                pygame.Rect(1220, 500, 22, 22),
                pygame.Rect(1510, 480, 22, 22),
                pygame.Rect(1790, 500, 22, 22),
                pygame.Rect(2170, 480, 22, 22),
                pygame.Rect(2590, 480, 22, 22),
            ],
            "chests": [
                pygame.Rect(1460, 490, 34, 30),
                pygame.Rect(2860, 520, 34, 30),
            ],
            "start_flag": pygame.Rect(40, 500, 28, 80),
            "exit_door": pygame.Rect(2950, 500, 50, 80),
        },
        {
            "background": LEVEL_BG_PATHS[2],
            "platforms": [
                pygame.Rect(0, 560, 240, 60),
                pygame.Rect(320, 520, 140, 60),
                pygame.Rect(560, 560, 180, 60),
                pygame.Rect(820, 500, 120, 60),
                pygame.Rect(980, 560, 200, 60),
                pygame.Rect(1240, 520, 140, 60),
                pygame.Rect(1480, 560, 180, 60),
                pygame.Rect(1740, 520, 140, 60),
                pygame.Rect(1960, 560, 200, 60),
                pygame.Rect(2220, 520, 140, 60),
                pygame.Rect(2420, 560, 220, 60),
                pygame.Rect(2700, 560, 260, 60),
            ],
            "spikes": [
                pygame.Rect(260, 545, 60, 25),
                pygame.Rect(540, 545, 60, 25),
                pygame.Rect(800, 485, 60, 25),
                pygame.Rect(980, 545, 60, 25),
                pygame.Rect(1320, 545, 60, 25),
                pygame.Rect(1780, 485, 60, 25),
                pygame.Rect(2320, 545, 60, 25),
            ],
            "coins": [
                pygame.Rect(180, 500, 22, 22),
                pygame.Rect(460, 480, 22, 22),
                pygame.Rect(660, 500, 22, 22),
                pygame.Rect(900, 450, 22, 22),
                pygame.Rect(1180, 500, 22, 22),
                pygame.Rect(1440, 480, 22, 22),
                pygame.Rect(1700, 500, 22, 22),
                pygame.Rect(2060, 480, 22, 22),
                pygame.Rect(2550, 480, 22, 22),
            ],
            "chests": [
                pygame.Rect(1180, 470, 34, 30),
                pygame.Rect(2880, 520, 34, 30),
            ],
            "start_flag": pygame.Rect(40, 500, 28, 80),
            "exit_door": pygame.Rect(2940, 500, 50, 80),
        },
    ]
    level = levels[level_index % len(levels)]
    return (
        level["platforms"],
        level["spikes"],
        level["coins"],
        level["chests"],
        level["start_flag"],
        level["exit_door"],
        level["background"],
    )


def draw_world(platforms, spikes, coins, chests, start_flag, exit_door, camera_x, tile_image, trap_image):
    for platform in platforms:
        draw_rect = pygame.Rect(platform.x - camera_x, platform.y, platform.width, platform.height)
        if tile_image:
            tile = pygame.transform.scale(tile_image, (TILE_SIZE, TILE_SIZE))
            for x in range((draw_rect.width // TILE_SIZE) + 1):
                for y in range((draw_rect.height // TILE_SIZE) + 1):
                    screen.blit(tile, (draw_rect.x + x * TILE_SIZE, draw_rect.y + y * TILE_SIZE))
        else:
            pygame.draw.rect(screen, BROWN, draw_rect)
        pygame.draw.rect(screen, WHITE, draw_rect, 2)

    for spike in spikes:
        draw_x = spike.x - camera_x
        if trap_image:
            trap_icon = pygame.transform.scale(trap_image, (spike.width, spike.height + 14))
            screen.blit(trap_icon, (draw_x, spike.y - 12))
        else:
            points = [
                (draw_x, spike.bottom),
                (draw_x + spike.width / 2, spike.top),
                (draw_x + spike.width, spike.bottom),
            ]
            pygame.draw.polygon(screen, RED, points)
            pygame.draw.polygon(screen, WHITE, points, 2)

    for coin in coins:
        pygame.draw.ellipse(
            screen,
            GOLD,
            pygame.Rect(coin.x - camera_x, coin.y, coin.width, coin.height),
        )

    for chest in chests:
        chest_rect = pygame.Rect(chest.x - camera_x, chest.y, chest.width, chest.height)
        pygame.draw.rect(screen, (160, 90, 30), chest_rect)
        pygame.draw.rect(screen, GOLD, (chest_rect.x + 8, chest_rect.y + 10, 18, 8))
        pygame.draw.rect(screen, WHITE, chest_rect, 2)

    start_rect = pygame.Rect(start_flag.x - camera_x, start_flag.y, start_flag.width, start_flag.height)
    if tile_image:
        tile = pygame.transform.scale(tile_image, (TILE_SIZE, TILE_SIZE))
        for x in range((start_rect.width // TILE_SIZE) + 1):
            screen.blit(tile, (start_rect.x + x * TILE_SIZE, start_rect.y))
    else:
        pygame.draw.rect(screen, GREEN, start_rect)
    pygame.draw.rect(screen, WHITE, (start_rect.x + 8, start_rect.y + 8, 20, 16))

    exit_rect = pygame.Rect(exit_door.x - camera_x, exit_door.y, exit_door.width, exit_door.height)
    if tile_image:
        tile = pygame.transform.scale(tile_image, (TILE_SIZE, TILE_SIZE))
        for x in range((exit_rect.width // TILE_SIZE) + 1):
            screen.blit(tile, (exit_rect.x + x * TILE_SIZE, exit_rect.y))
    else:
        pygame.draw.rect(screen, GRAY, exit_rect)
    pygame.draw.rect(screen, WHITE, (exit_rect.x + 12, exit_rect.y + 14, 26, 36), 2)
    pygame.draw.circle(screen, GOLD, (exit_rect.x + 38, exit_rect.y + 42), 3)


def draw_hud(font, small_font, score, lives, state):
    title = font.render("PATHFINDER", True, WHITE)
    screen.blit(title, (20, 12))
    screen.blit(small_font.render(f"Score: {score}", True, WHITE), (20, 56))
    screen.blit(small_font.render(f"Lives: {lives}", True, WHITE), (20, 84))
    screen.blit(
        small_font.render("Move: Left/Right  Jump: Space", True, WHITE),
        (20, SCREEN_HEIGHT - 34),
    )
    if state == "won":
        msg = font.render("LEVEL COMPLETE! Press R to play again", True, GOLD)
        screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, 90)))
    elif state == "lost":
        msg = font.render("GAME OVER! Press R to retry", True, RED)
        screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, 90)))


def load_level(level_index, player):
    platforms, spikes, coins, chests, start_flag, exit_door, background_path = build_level(level_index)
    player.start_pos = pygame.Vector2(start_flag.x, start_flag.y - player.rect.height)
    player.respawn()
    background = safe_load_image(background_path, (SCREEN_WIDTH, SCREEN_HEIGHT), SKY_BLUE)
    return (platforms, spikes, coins, chests, start_flag, exit_door), background


def main():
    menu_font = pygame.font.SysFont("arial", 48, bold=True)
    font = pygame.font.SysFont("arial", 36, bold=True)
    small_font = pygame.font.SysFont("arial", 26)

    hero_sheet = safe_load_image(
        "assets/MainCharacter/male_hero.png",
        (1280, 3328),
        (220, 80, 80, 255),
    )
    terrain_tile = safe_load_image("assets/Terrain/Terrain.png", (TILE_SIZE, TILE_SIZE), BROWN)
    trap_image = safe_load_image("assets/Trap/Idle.png", (TILE_SIZE, TILE_SIZE), RED)
    start_sound = safe_load_sound("assets/audio/notice.wav")
    exit_sound = safe_load_sound("assets/audio/notice.wav")
    menu_bg = safe_load_image(MENU_BG_PATH, (SCREEN_WIDTH, SCREEN_HEIGHT), (28, 35, 52))

    play_music("assets/music/overworld.ogg")

    player = Player(70, 380, hero_sheet)
    current_level = 0
    score = 0
    player.lives = 3
    (platforms, spikes, coins, chests, start_flag, exit_door), level_background = load_level(current_level, player)
    game_state = "menu"

    in_menu = True
    running = True
    jump_pressed = False

    while running:
        dt = clock.tick(FPS)
        _ = dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    jump_pressed = True
                if event.key == pygame.K_r and game_state in ("won", "lost"):
                    current_level = 0
                    score = 0
                    player.lives = 3
                    (platforms, spikes, coins, chests, start_flag, exit_door), level_background = load_level(current_level, player)
                    game_state = "playing"
                    in_menu = False
                    play_music("assets/music/time_for_adventure.mp3")
                if event.key == pygame.K_ESCAPE:
                    in_menu = True
                    game_state = "menu"
                    play_music("assets/music/overworld.ogg")

        if in_menu:
            draw_background(menu_bg)
            title = menu_font.render("PATHFINDER", True, WHITE)
            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 170)))
            if draw_button("START", 370, 300, 220, 68, GREEN, (30, 210, 30), small_font):
                if start_sound:
                    start_sound.play()
                current_level = 0
                score = 0
                player.lives = 3
                (platforms, spikes, coins, chests, start_flag, exit_door), level_background = load_level(current_level, player)
                game_state = "playing"
                in_menu = False
                play_music("assets/music/time_for_adventure.mp3")
            if draw_button("EXIT", 370, 395, 220, 68, BROWN, (150, 102, 40), small_font):
                if exit_sound:
                    exit_sound.play()
                pygame.time.delay(120)
                running = False
            pygame.display.flip()
            continue

        if game_state == "playing":
            keys = pygame.key.get_pressed()
            player.handle_input(keys)
            if jump_pressed:
                player.jump()
            player.update(platforms)

            if player.rect.top > SCREEN_HEIGHT + 120:
                player.lives -= 1
                if player.lives <= 0:
                    game_state = "lost"
                else:
                    player.respawn()

            for spike in spikes:
                if player.rect.colliderect(spike):
                    player.lives -= 1
                    if player.lives <= 0:
                        game_state = "lost"
                    else:
                        player.respawn()
                    break

            for coin in coins[:]:
                if player.rect.colliderect(coin):
                    coins.remove(coin)
                    score += 10

            for chest in chests[:]:
                if player.rect.colliderect(chest):
                    chests.remove(chest)
                    score += 30

            if player.rect.colliderect(exit_door):
                if current_level < LEVEL_COUNT - 1:
                    score += 100
                    current_level += 1
                    (platforms, spikes, coins, chests, start_flag, exit_door), level_background = load_level(current_level, player)
                    if start_sound:
                        start_sound.play()
                else:
                    game_state = "won"
                    if exit_sound:
                        exit_sound.play()

        jump_pressed = False
        camera_x = max(0, min(int(player.rect.centerx - SCREEN_WIDTH * 0.4), LEVEL_WIDTH - SCREEN_WIDTH))

        if in_menu:
            draw_background(menu_bg)
        else:
            draw_background(level_background)
        draw_world(platforms, spikes, coins, chests, start_flag, exit_door, camera_x, terrain_tile, trap_image)
        player.draw(screen, camera_x)

        level_text = small_font.render(f"Level {current_level + 1} / {LEVEL_COUNT}", True, WHITE)
        screen.blit(level_text, (SCREEN_WIDTH - 240, 16))

        if draw_button("MENU", SCREEN_WIDTH - 142, 14, 128, 42, (165, 45, 45), (220, 65, 65), small_font):
            if exit_sound:
                exit_sound.play()
            in_menu = True
            game_state = "menu"
            play_music("assets/music/overworld.ogg")

        draw_hud(font, small_font, score, player.lives, game_state)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
