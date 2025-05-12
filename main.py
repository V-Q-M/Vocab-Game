import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()

pygame.display.set_caption("Pingo")

WIDTH, HEIGHT = 1500, 1200

FPS = 60
PLAYER_VEL = 7

window = pygame.display.set_mode((WIDTH, HEIGHT))

hit_sound = pygame.mixer.Sound(join("assets", "Sounds", "hit.mp3"))
hurt_sound = pygame.mixer.Sound(join("assets", "Sounds", "hit.mp3"))
walking_sound = pygame.mixer.Sound(join("assets", "Sounds", "hit.mp3"))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path,f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet,(0,0), rect)
            sprites.append(surface)


        name = image.replace(".png", "")

        if direction:
            # Example: run_up, idle_left, etc.
            if name.endswith("_up"):
                all_sprites[name] = sprites
            elif name.endswith("_down"):
                all_sprites[name] = sprites
            elif name.endswith("_right"):
                all_sprites[name] = sprites
            elif name.endswith("_left"):
                all_sprites[name] = sprites

            else:
                # Default: assume right-facing and auto-generate flipped versions
                all_sprites[name + "_right"] = sprites
                all_sprites[name + "_left"] = flip(sprites)
        else:
            all_sprites[name] = sprites

    return all_sprites

def get_block(size, name):
    path = join("assets", "Terrain", name)
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0,0, size, size)
    surface.blit(image, (0,0), rect)
    return surface

class Player(pygame.sprite.Sprite):
    HEALTH = 100
    COLOR = (255, 0, 0)
    GRAVITY = 0.15
    SPRITES = load_sprite_sheets("MainCharacters", "Pingo", 128, 128, True)
    ANIMATION_DELAY = 15
    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "down"
        self.animation_count = 0
        self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def move_up(self, vel):
        self.y_vel = -vel
        if self.direction != "up":
            self.direction = "up"
            self.animation_count = 0

    def move_down(self, vel):
        self.y_vel = vel
        if self.direction != "down":
            self.direction = "down"
            self.animation_count = 0


    def loop(self, fps):
        if self.direction == "down":
            self.y_vel += min(2, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0

    def hit_head(self):
        #self.count = 0
        self.fall_count = 0
        self.y_vel = 0

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = self.animation_count // self.ANIMATION_DELAY % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win):
        win.blit(self.sprite, (self.rect.x, self.rect.y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win):
        win.blit(self.image, (self.rect.x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x,y,size,size)
        block = get_block(size, "water.png")
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Wall(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size, "wall.png")
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class SnowBall(Object):
    SPRITES = load_sprite_sheets("Objects", "Snowball", 256, 256)
    ANIMATION_DELAY = 8
    FONT = pygame.font.SysFont("arial", 60, bold=True)

    def __init__(self, x, y, size, word):
        super().__init__(x, y, size, size)
        self.sprites = self.SPRITES["spin"]  # Assumes name of sprite sheet is 'spin.png'
        self.animation_count = 0
        self.sprite = self.sprites[0]
        self.image.blit(self.sprite, (0, 0))
        self.mask = pygame.mask.from_surface(self.sprite)
        self.fall_speed = 3
        self.word = word

    def update_image_and_mask(self):
        # Recreate image surface
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.blit(self.sprite, (0, 0))

        # Render the word and center it
        text_surface = self.FONT.render(self.word, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.image.blit(text_surface, text_rect)

        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.y += self.fall_speed
        self.animation_count += 1
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        self.sprite = self.sprites[sprite_index]
        self.update_image_and_mask()

class Boulder(Object):
    SPRITES = load_sprite_sheets("Objects", "Snowball", 256, 256)
    ANIMATION_DELAY = 8
    FONT = pygame.font.SysFont("arial", 50, bold=True)


    def __init__(self, x, y, size, word):
        super().__init__(x, y, size, size)
        self.sprites = self.SPRITES["spin"]  # Assumes name of sprite sheet is 'spin.png'
        self.animation_count = 0
        self.sprite = self.sprites[0]
        self.image.blit(self.sprite, (0, 0))
        self.mask = pygame.mask.from_surface(self.sprite)
        self.fall_speed = 5
        self.word = word

    def update_image_and_mask(self):
        # Recreate image surface
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.blit(self.sprite, (0, 0))

        # Render the word and center it
        text_surface = self.FONT.render(self.word, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.image.blit(text_surface, text_rect)

        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.y += self.fall_speed
        self.animation_count += 1
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        self.sprite = self.sprites[sprite_index]
        self.update_image_and_mask()


def snowBallLogic(snowballs,snowball, player):
    # Check collision using mask
    offset_x = snowball.rect.x - player.rect.x
    offset_y = snowball.rect.y - player.rect.y
    if player.mask and snowball.mask:
        # Create a smaller area in the center of the snowball for collision
        core_width = int(snowball.sprite.get_width() * 0.8)
        core_height = int(snowball.sprite.get_height() * 0.4)
        core_x = (snowball.sprite.get_width() - core_width) // 2
        core_y = (snowball.sprite.get_height() - core_height) // 2

        # Extract a smaller core surface
        core_surface = pygame.Surface((core_width, core_height), pygame.SRCALPHA)
        core_surface.blit(snowball.sprite, (0, 0), pygame.Rect(core_x, core_y, core_width, core_height))
        core_mask = pygame.mask.from_surface(core_surface)

        # Adjust offset for new mask
        core_offset_x = snowball.rect.x + core_x - player.rect.x
        core_offset_y = snowball.rect.y + core_y - player.rect.y

        if player.mask.overlap(core_mask, (core_offset_x, core_offset_y)):
            hit_sound.play()
            print(snowball.word)
            snowballs.remove(snowball)

        if snowball.rect.y > HEIGHT - 256:
            snowballs.remove(snowball)

def boulderLogic(boulders, boulder, player):
    # Check collision using mask
    offset_x = boulder.rect.x - player.rect.x
    offset_y = boulder.rect.y - player.rect.y
    if player.mask and boulder.mask:
        # Create a smaller area in the center of the snowball for collision
        core_width = int(boulder.sprite.get_width() * 0.8)
        core_height = int(boulder.sprite.get_height() * 0.4)
        core_x = (boulder.sprite.get_width() - core_width) // 2
        core_y = (boulder.sprite.get_height() - core_height) // 2

        # Extract a smaller core surface
        core_surface = pygame.Surface((core_width, core_height), pygame.SRCALPHA)
        core_surface.blit(boulder.sprite, (0, 0), pygame.Rect(core_x, core_y, core_width, core_height))
        core_mask = pygame.mask.from_surface(core_surface)

        # Adjust offset for new mask
        core_offset_x = boulder.rect.x + core_x - player.rect.x
        core_offset_y = boulder.rect.y + core_y - player.rect.y

        if player.mask.overlap(core_mask, (core_offset_x, core_offset_y)):
            hit_sound.play()
            print(boulder.word)
            player.HEALTH -= 50
            print(player.HEALTH)
            boulders.remove(boulder)

        if boulder.rect.y > HEIGHT - 256:
            boulders.remove(boulder)


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _,_, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

def draw(window, background, bg_image, player, objects):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window)

    player.draw(window)

    pygame.display.update()



def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

        collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    player.y_vel = 0

    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)


    if keys[pygame.K_UP] or keys[pygame.K_w]:
        player.move_up(PLAYER_VEL**0.5)
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        player.move_down(PLAYER_VEL**1.1)
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not collide_left:
        player.move_left(PLAYER_VEL)
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not collide_right:
        player.move_right(PLAYER_VEL)


    handle_vertical_collision(player, objects, player.y_vel)

def load_words():
    questions = ["one", "two", "three", "four", "five"]
    answers = ["eins", "zwei", "drei", "vier", "fünf"]
    return questions,answers

index = 0

def main(window):
    global index
    clock = pygame.time.Clock()
    background, bg_image = get_background("Snow.png")

    block_size = 128

    player = Player(500,800,64,64)
    snowball = SnowBall(block_size * 2, 0, 2* block_size, "test")
    boulder = Boulder(block_size * 3, 0, 2 * block_size, "error")
    wall_right = [Wall(WIDTH - block_size,HEIGHT - (i - 1) * block_size, block_size) for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)]
    wall_left  = [Wall(0, HEIGHT -(i - 1) * block_size, block_size) for i in range((-WIDTH // block_size), WIDTH * 2 // block_size)]
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)]
    objects  = [*wall_right, *wall_left, *floor]

    snowballs = []
    boulders = []

    # Timer to control spawn interval
    snowball_timer = 0
    snowball_interval = 7000  # in milliseconds (5 seconds

    questions, answers = load_words()

    gameOver = False
    run = True
    while run:
        dt = clock.tick(FPS)
        snowball_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
        if gameOver == False:
                # Spawn a new snowball every 5 seconds
            if snowball_timer >= snowball_interval:
                displayed_word = random.choice(answers)
                answers.remove(displayed_word)
                displayed_wrong_answer = random.choice(answers)

                snowball_x = random.randint(256, WIDTH - 256)
                snowballs.append(SnowBall(snowball_x, -100, 256, displayed_word))
                boulders.append(Boulder(snowball_x + 200, -100, 256, displayed_wrong_answer))
                snowball_timer = 0

            # Update snowballs and check for collision with player
            for snowball in snowballs[:]:  # Use a copy of the list to safely remove items
                snowball.update()
                snowBallLogic(snowballs, snowball, player)

            for boulder in boulders[:]:
                boulder.update()
                boulderLogic(boulders,boulder,player)


        # Combine all objects for rendering
        all_objects = objects + snowballs + boulders
        if player.HEALTH > 0:
            player.loop(FPS)
        else:
            #player.rect.y = -500
            gameOver = True
            print("gameover!")

        handle_move(player, objects)
        draw(window, background, bg_image, player, all_objects,)

    pygame.quit()
    quit()



if __name__ == "__main__":
    main(window)

