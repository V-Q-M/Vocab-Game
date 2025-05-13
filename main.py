import os
import random
import math
import duckdb
import pygame
import vocabulary
from os import listdir, remove
from os.path import isfile, join

pygame.init()

pygame.display.set_caption("Pingo")

WIDTH, HEIGHT = 1700, 1350

FPS = 60
PLAYER_VEL = 7
snowball_exists = False

window = pygame.display.set_mode((WIDTH, HEIGHT))

hit_sound = pygame.mixer.Sound(join("assets", "Sounds", "hit.mp3"))
hurt_sound = pygame.mixer.Sound(join("assets", "Sounds", "hurt.mp3"))
laugh_sound = pygame.mixer.Sound(join("assets", "Sounds", "laugh.mp3"))
walking_sound = pygame.mixer.Sound(join("assets", "Sounds", "footsteps.mp3"))
fall_in_water_sound = pygame.mixer.Sound(join("assets", "Sounds", "plop.mp3"))
music = pygame.mixer.Sound(join("assets", "Sounds", "music.WAV"))

walking_sound_channel = pygame.mixer.Channel(1)


language = "russian"



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
    ANIMATION_DELAY = 3
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

        self.move(self.x_vel, self.y_vel)
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
        if sprite_sheet == "idle":
            sprite_index = self.animation_count // (self.ANIMATION_DELAY + 2) % len(sprites)
        else:
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
        block = get_block(size, "reef.png")
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class BelowBlock(Object):
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
    ANIMATION_DELAY = 6
    FONT = pygame.font.Font("assets/Fonts/pixel.TTF", 30)

    def __init__(self, x, y, size, word):
        super().__init__(x, y, size, size)
        self.sprites = self.SPRITES["spin"]  # Assumes name of sprite sheet is 'spin.png'
        self.animation_count = 0
        self.sprite = self.sprites[0]
        self.image.blit(self.sprite, (0, 0))
        self.mask = pygame.mask.from_surface(self.sprite)
        self.fall_speed = 3.5
        self.word = word
        self.hasCollided = False



    def update_image_and_mask(self):
        # Recreate image surface
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.blit(self.sprite, (0, 0))

        # Render the word and center it
        text_surface = self.FONT.render(self.word, True, (186, 177, 179))

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
    ANIMATION_DELAY = 6
    FONT = pygame.font.Font("assets/Fonts/pixel.TTF", 30)
    hasCollided = False

    def __init__(self, x, y, size, word):
        super().__init__(x, y, size, size)
        self.sprites = self.SPRITES["spin"]  # Assumes name of sprite sheet is 'spin.png'
        self.animation_count = 0
        self.sprite = self.sprites[0]
        self.image.blit(self.sprite, (0, 0))
        self.mask = pygame.mask.from_surface(self.sprite)
        self.fall_speed = 3.5
        self.word = word
        self.hasCollided = False

    def update_image_and_mask(self):
        # Recreate image surface
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.blit(self.sprite, (0, 0))

        # Render the word and center it
        text_surface = self.FONT.render(self.word, True, (186, 177, 179))
        text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))

        self.image.blit(text_surface, text_rect)

        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.y += self.fall_speed
        self.animation_count += 1
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        self.sprite = self.sprites[sprite_index]
        self.update_image_and_mask()


def snowBallLogic(snowballs,snowball, player, boulders):
    global words_guessed
    global snowball_exists
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

        if player.mask.overlap(core_mask, (core_offset_x, core_offset_y)) and (not snowball.hasCollided):
            hit_channel = pygame.mixer.Channel(3)
            hit_channel.play(hit_sound)
            print(snowball.word)
            snowball_exists = False
            snowball.hasCollided = True
            destroy_snowball(snowball)
            change_all_boulders_to_rock(boulders)
            #correct_answers.remove(snowball.word)
            pick_next_word()
            words_guessed +=1
            #snowballs.remove(snowball)

        if snowball.rect.y > HEIGHT - 320:
            if not snowball.hasCollided:
                plop_channel = pygame.mixer.Channel(2)
                plop_channel.play(fall_in_water_sound)
                snowball_exists = False
                change_all_boulders_to_rock(boulders)
                pick_next_word()
            snowballs.remove(snowball)



def boulderLogic(boulders, boulder, player):
    # Check collision using mask
    global flash_red, flash_timer

    offset_x = boulder.rect.x - player.rect.x
    offset_y = boulder.rect.y - player.rect.y
    if player.mask and boulder.mask:
        # Create a smaller area in the center of the snowball for collision
        core_width = int(boulder.sprite.get_width() * 0.8)
        core_height = int(boulder.sprite.get_height() * 0.8)
        core_x = (boulder.sprite.get_width() - core_width) // 2
        core_y = (boulder.sprite.get_height() - core_height) // 2

        # Extract a smaller core surface
        core_surface = pygame.Surface((core_width, core_height), pygame.SRCALPHA)
        core_surface.blit(boulder.sprite, (0, 0), pygame.Rect(core_x, core_y, core_width, core_height))
        core_mask = pygame.mask.from_surface(core_surface)

        # Adjust offset for new mask
        core_offset_x = boulder.rect.x + core_x - player.rect.x
        core_offset_y = boulder.rect.y + core_y - player.rect.y

        if (player.mask.overlap(core_mask, (core_offset_x, core_offset_y))) and (not boulder.hasCollided):
            hit_sound.play()
            print(boulder.word)
            hurt_sound.play()
            flash_red = True
            flash_timer = pygame.time.get_ticks()
            boulder.hasCollided = True
            change_one_boulder_to_rock(boulder)
            player.HEALTH -= 34
            print(player.HEALTH)
            #boulders.remove(boulder)

        if boulder.rect.y > HEIGHT - 320:
            plop_channel = pygame.mixer.Channel(2)
            plop_channel.play(fall_in_water_sound)

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

    player.draw(window)

    for obj in objects:
        obj.draw(window)


    #pygame.display.update()


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
    # Detect if player is moving
    moving = player.x_vel != 0 or player.y_vel != 0

    # Play or stop walking sound
    if moving:
        if not walking_sound_channel.get_busy():
            walking_sound_channel.play(walking_sound, loops=-1)
    else:
        walking_sound_channel.stop()


def load_words():
    questions = ["привет", "спасибо", "да", "нет", "пожалуйста", "как", "кто", "что", "где"]
    answers = ["hallo", "danke", "ja", "nein", "bitte", "wie", "wer", "was", "wo"]

    return questions,answers


questions, answers = load_words()
correct_answers = answers[:]
wrong_answers = []
words_guessed = 0
displayed_word = None
displayed_question = None
snowball_exists = False


def pick_next_word():
    global questions, answers, wrong_answers
    global displayed_word, words_guessed, displayed_question
    wrong_answers = answers[:] # copy answers
    if correct_answers:
        displayed_word = random.choice(correct_answers)
        index  = answers.index(displayed_word) # pick a word, can shrink so that correct words won't appear
        displayed_question = questions[index]
        print(words_guessed)
        correct_answers.remove(displayed_word)
        wrong_answers.remove(
            displayed_word)  # remove it from the wrong pool, can't shrink (there are always the same amount of wrong words availabe)


flash_red = False
flash_duration = 300  # milliseconds
flash_timer = 0


def change_all_boulders_to_rock(boulders):
    rock_sprites = Boulder.SPRITES["rock"]
    for boulder in boulders:
        boulder.sprites = rock_sprites
        boulder.animation_count = 0
        boulder.sprite = rock_sprites[0]
        boulder.update_image_and_mask()

def change_one_boulder_to_rock(boulder):
    rock_sprites = Boulder.SPRITES["rock"]
    boulder.sprites = rock_sprites
    boulder.animation_count = 0
    boulder.sprite = rock_sprites[0]
    boulder.update_image_and_mask()

def destroy_snowball(snowball):
    snowball_sprites = SnowBall.SPRITES["explosion"]
    snowball.sprites = snowball_sprites
    snowball.animation_count = 0
    snowball.sprite = snowball_sprites[0]
    snowball.word = ""
    snowball.update_image_and_mask()


def main(window):
    global questions, answers, wrong_answers
    global displayed_word
    global words_guessed
    global flash_red, flash_duration, flash_timer
    global snowball_exists
    clock = pygame.time.Clock()
    background, bg_image = get_background("Snow.png")
    red_flash_duration = 150  # milliseconds
    red_flash_timer = 0
    music.play()

    block_size = 128

    player = Player(500,800,64,64)
    snowball = SnowBall(block_size * 2, 0, 2* block_size, "test")
    boulder = Boulder(block_size * 3, 0, 2 * block_size, "error")
    wall_right = [Wall(WIDTH - block_size,HEIGHT - (i - 1) * block_size, block_size) for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)]
    wall_left  = [Wall(0, HEIGHT -(i - 1) * block_size, block_size) for i in range((-WIDTH // block_size), WIDTH * 2 // block_size)]
    belowfloor = [BelowBlock(i * block_size, HEIGHT - block_size, block_size) for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)]
    floor = [Block(i * block_size, HEIGHT - block_size * 2, block_size) for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)]
    objects  = [*wall_right, *wall_left, *floor, *belowfloor]

    snowballs = []
    boulders = []
    isLaughing = False
    # Timer to control spawn interval
    snowball_timer = 0
    snowball_interval = 7000  # in milliseconds (5 seconds

    pick_next_word()

    FONT = pygame.font.Font("assets/Fonts/pixel.TTF", 60)

    VICTORYFONT = pygame.font.Font("assets/Fonts/pixel.TTF", 140)

    gameOver = False
    run = True
    while run:
        dt = clock.tick(FPS)
        snowball_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
        if not gameOver:

            if snowball_timer >= snowball_interval:
                # Select two random incorrect answers
                displayed_wrong_answers = random.sample(wrong_answers, 2)

                # List to track used X positions
                used_x = []

                def get_valid_x():
                    for _ in range(50):  # Try 50 times to find a valid X position
                        x = random.randint(256, WIDTH - 256)
                        if all(abs(x - ux) >= 300 for ux in used_x):
                            used_x.append(x)
                            return x
                    return None  # If no valid X is found, return None

                # Get valid X positions for snowball and boulders
                snowball_x = get_valid_x()
                boulder_x = get_valid_x()
                extra_boulder_x = get_valid_x()

                # Random Y positions for boulders
                boulder_y = random.randint(0, 200)
                extra_boulder_y = random.randint(0, 200)

                if not snowball_exists and snowball_x is not None:
                    snowballs.append(SnowBall(snowball_x, -100, 256, displayed_word))
                    snowball_exists = True

                    if boulder_x is not None:
                        # Place the first boulder with the first wrong answer
                        boulders.append(Boulder(boulder_x, -100 + boulder_y, 256, displayed_wrong_answers[0]))
                    if extra_boulder_x is not None:
                        # Place the second boulder with the second wrong answer
                        boulders.append(
                            Boulder(extra_boulder_x, -100 + extra_boulder_y, 256, displayed_wrong_answers[1]))
                else:
                    if boulder_x is not None:
                        # Place the first boulder with the first wrong answer
                        boulders.append(Boulder(boulder_x, -100, 256, displayed_wrong_answers[0]))

                    if extra_boulder_x is not None:
                        # Place the second boulder with the second wrong answer
                        boulders.append(Boulder(extra_boulder_x, -100, 256, displayed_wrong_answers[1]))

                snowball_timer = 0

            # Update snowballs and check for collision with player
            for snowball in snowballs[:]:  # Use a copy of the list to safely remove items
                snowball.update()
                snowBallLogic(snowballs, snowball, player, boulders)

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
            victory_text = VICTORYFONT.render("Game over!", True, (200, 50, 50))
            victory_rect = victory_text.get_rect(centerx=(WIDTH // 2), centery=(HEIGHT // 2))
            window.blit(victory_text, victory_rect)

        handle_move(player, objects)
        draw(window, background, bg_image, player, all_objects,)

        # Now, render the displayed_question text
        if displayed_question:
            question_text = FONT.render(displayed_question, True, (100, 100, 200))  # White text
            question_rect = question_text.get_rect(center=(WIDTH // 2, 60))  # Position at the top center

            window.blit(question_text, question_rect)

        if words_guessed == len(questions):
            gameOver = True
            if not isLaughing:
                laugh_sound.play()
                isLaughing = True
            print("Well done!")
            victory_text = VICTORYFONT.render("Well done!", True, (240, 220, 50))
            victory_rect = victory_text.get_rect(centerx=(WIDTH // 2), centery=(HEIGHT // 2))
            window.blit(victory_text, victory_rect)

        if flash_red:
            now = pygame.time.get_ticks()
            if now - flash_timer < flash_duration:
                flash_overlay = pygame.Surface((WIDTH, HEIGHT))
                flash_overlay.set_alpha(100)  # Transparency: 0 = invisible, 255 = solid
                flash_overlay.fill((255, 0, 0))  # Red color
                window.blit(flash_overlay, (0, 0))
            else:
                flash_red = False

        # Update the display
        pygame.display.update()

    pygame.quit()
    quit()



if __name__ == "__main__":
    main(window)

