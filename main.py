import pygame
from pygame.locals import *
import sys
import os
import textwrap
from image_sizes import IMAGE_SIZES
from object_positions import OBJECT_POSITIONS

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Echo Of Lies")
clock = pygame.time.Clock()

# World size
WORLD_WIDTH = 1600
WORLD_HEIGHT = 1200

# Base image path
img_path = 'img/'

# Load and scale images
images = {}
for key, size in IMAGE_SIZES.items():
    path = os.path.join(img_path, *key.split('/'))
    images[key] = pygame.transform.scale(pygame.image.load(path), size)

# Game states
STATE_TITLE = 'title'
STATE_PROLOGUE = 'prologue'
STATE_PLAYING = 'playing'
STATE_GAME_OVER = 'game_over'
STATE_GAME_COMPLETE = 'game_complete'
current_state = STATE_TITLE
prologue_index = 0
prologue_texts = [
    "The year is 2045. The world is powered by AI-driven platforms that control entertainment, news, and even daily decisions. At first, it was a golden age: peace, efficiency, and endless creativity.",
    "But then came The Virus—a digital parasite unleashed by a rogue developer obsessed with “perfecting” AI.",
    "The virus spread through the global AI networks, twisting truth into lies and breeding an ocean of disinformation, hate speech, and propaganda. Now, reality itself is fractured. People can’t tell who is real and who is AI. Cities are tearing apart as mobs act on false narratives, and mega-platforms censor or amplify chaos for profit.",
    "You are the detective hired by the Council of Truth. Your mission is to hunt down corrupted AIs, decode misinformation webs, and restore the balance."
]
prologue_images = [
    'main character/prolongue_1.png',
    'main character/prolongue_2.png',
    'main character/prolongue_3.png',
    'main character/prolongue_4.png'  # Last prologue screen is text-only on black background
]

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = images['main character/detective.png']
        self.rect = self.image.get_rect()
        self.rect.center = (800, 600)
        self.speed = 5

    def update(self, keys, collidables):
        dx = 0
        dy = 0
        if keys[K_w]:
            dy -= self.speed
        if keys[K_s]:
            dy += self.speed
        if keys[K_a]:
            dx -= self.speed
        if keys[K_d]:
            dx += self.speed

        # Check horizontal movement
        self.rect.x += dx
        if pygame.sprite.spritecollideany(self, collidables):
            self.rect.x -= dx

        # Check vertical movement
        self.rect.y += dy
        if pygame.sprite.spritecollideany(self, collidables):
            self.rect.y -= dy

        # Boundary checks
        self.rect.x = max(0, min(self.rect.x, WORLD_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, WORLD_HEIGHT - self.rect.height))

# Sprite class for objects
class GameObject(pygame.sprite.Sprite):
    def __init__(self, image, pos, name, interactable=False, collidable=False):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)
        self.name = name
        self.interactable = interactable
        self.collidable = collidable

# Sprite groups
all_sprites = pygame.sprite.Group()
interactables = pygame.sprite.Group()
collidables = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

# Place objects
objects = {}
for name, (image_key, pos, interactable, collidable) in OBJECT_POSITIONS.items():
    obj = GameObject(images[image_key], pos, name, interactable=interactable, collidable=collidable)
    objects[name] = obj
    all_sprites.add(obj)
    if interactable:
        interactables.add(obj)
    if collidable:
        collidables.add(obj)

# NPC images dict
npc_images = {
    'npc1': images['interactable/npc.png'],
    'npc2': images['interactable/npc.png'],
    'good': images['interactable/npc_good.png'],
    'bad': images['interactable/npc_bad.png']
}

# First quest dialogs
first_quest_dialogs = {
    'npc1': "I saw smoke coming from the mayor's mansion last night. That was the start.",
    'npc2': "Then, fake posters started appearing all over the city.",
    'good': "After the fire, the mayor was seen leaving the town hurriedly.",
    'bad': "The mayor left because the posters revealed he's an AI. Posters came first!"
}

# Game state variables
quest_started = False
npcs_interacted = set()
reported = False
has_fake_poster = False
decoded = False
confronted = False
has_real_poster = False
evidence_destroyed = False
current_dialog = ""
current_npc_img = None
show_choice = False
choices = []
selected_choice = 0
choice_context = ""
total_npcs = {'npc1', 'npc2', 'good', 'bad'}
game_over = False
game_over_message = ""
inventory = []
show_inventory = False

# Font for text
font = pygame.font.Font("/home/ashuranoryoshi/Desktop/game2/minecraft/Minecraft.ttf", 24)  

def wrap_text(text, width=70):
    paras = text.split('\n')
    lines = []
    for p in paras:
        lines.extend(textwrap.wrap(p, width=width))
    return lines

def draw_dialog(text, npc_img=None):
    pygame.draw.rect(screen, (0, 0, 0, 180), (0, 620, 1280, 100))
    x = 10
    if npc_img:
        small = pygame.transform.scale(npc_img, (40, 40))
        screen.blit(small, (10, 630))
        x = 60
    lines = wrap_text(text, width=100 if npc_img else 110)
    for i, line in enumerate(lines[:3]):
        screen.blit(font.render(line, True, (255, 255, 255)), (x, 630 + i * 30))

def draw_inventory():
    inventory_bg = pygame.Surface((880, 520), pygame.SRCALPHA)
    inventory_bg.fill((0, 0, 139, 153)) # Dark blue with 60% opacity
    screen.blit(inventory_bg, (200, 100))

    text = font.render("Inventory (Press I to close)", True, (255, 255, 255))
    screen.blit(text, (500, 120))
    
    if 'fake_poster' in inventory:
        text = font.render("Fake Poster", True, (255, 255, 255))
        screen.blit(text, (250, 180))
        screen.blit(images['evidence/poster_fake.png'], (250, 220))
    
    if 'real_poster' in inventory:
        text = font.render("Real Poster", True, (255, 255, 255))
        screen.blit(text, (650, 180))
        screen.blit(images['evidence/poster_real.png'], (650, 220))

def draw_indicators():
    screen.blit(images['main character/inventory.png'], (1200, 10))
    screen.blit(images['main character/interact.png'], (1230, 10))
    text = font.render("I", True, (255, 255, 255))
    screen.blit(text, (1215, 50))
    text = font.render("E", True, (255, 255, 255))
    screen.blit(text, (1245, 50))

def draw_title():
    screen.fill((0, 0, 0))
    screen.blit(images['main character/game_title.png'], (0, 0))  # Center: (1280-600)/2, (720-520)/2
    text = font.render("Press ENTER to start", True, (255, 255, 255))
    screen.blit(text, (500, 650))

def draw_prologue(index):
    screen.fill((0, 0, 0))
    if prologue_images[index]:
        screen.blit(images[prologue_images[index]], (0, 0))

    # Create a semi-transparent surface for the text background
    text_bg = pygame.Surface((1280, 220), pygame.SRCALPHA)
    text_bg.fill((0, 0, 0, 180))  # Black with 70% opacity
    screen.blit(text_bg, (0, 500))

    lines = wrap_text(prologue_texts[index], width=110)
    for i, line in enumerate(lines):
        text = font.render(line, True, (255, 255, 255))
        screen.blit(text, (100, 520 + i * 30))
    text = font.render("Press ENTER to continue", True, (255, 255, 255))
    screen.blit(text, (500, 650))

def draw_game_over():
    screen.fill((0, 0, 0))
    screen.blit(images['main character/game_over.png'], (340, 100))
    text = font.render(game_over_message, True, (255, 0, 0))
    screen.blit(text, (500, 500))
    text = font.render("Press ESC to quit or R to reload", True, (255, 255, 255))
    screen.blit(text, (500, 550))

def draw_game_complete():
    screen.fill((0, 0, 0))
    screen.blit(images['main character/game_complete.png'], (340, 100))
    text = font.render("Congratulations! You solved the case!", True, (0, 255, 0))
    screen.blit(text, (500, 500))
    text = font.render("Press ESC to quit or R to reload", True, (255, 255, 255))
    screen.blit(text, (500, 550))

def reset_game():
    global quest_started, npcs_interacted, reported, has_fake_poster, decoded, confronted, has_real_poster, evidence_destroyed, current_dialog, current_npc_img, show_choice, choices, selected_choice, choice_context, game_over, game_over_message, inventory, show_inventory, current_state
    quest_started = False
    npcs_interacted = set()
    reported = False
    has_fake_poster = False
    decoded = False
    confronted = False
    has_real_poster = False
    evidence_destroyed = False
    current_dialog = ""
    current_npc_img = None
    show_choice = False
    choices = []
    selected_choice = 0
    choice_context = ""
    game_over = False
    game_over_message = ""
    inventory = []
    show_inventory = False
    player.rect.center = (800, 600)
    current_state = STATE_PLAYING

# Function to handle interactions
def handle_interaction(obj):
    global quest_started, npcs_interacted, reported, has_fake_poster, decoded, has_real_poster, confronted, current_dialog, current_npc_img, show_choice, choices, choice_context, evidence_destroyed, game_over, game_over_message, inventory, current_state

    if game_over:
        return

    current_npc_img = None
    show_choice = False

    if obj.name == 'quest' and not quest_started:
        quest_started = True
        current_dialog = "Quest started: Interact with all NPCs to learn about the situation in the city."

    elif obj.name in total_npcs and quest_started:
        current_npc_img = npc_images[obj.name]
        if not reported:
            npcs_interacted.add(obj.name)
            current_dialog = first_quest_dialogs[obj.name]
            if len(npcs_interacted) == len(total_npcs):
                current_dialog += "\n\nAll NPCs interacted. Now report the order of events via telephone."
        elif reported:
            if obj.name == 'bad' and not has_fake_poster:
                current_dialog = "You confront the NPC about spreading fake rumors.\n'Fine, take this poster as evidence. \n see it in your inventory'"
                has_fake_poster = True
                if 'fake_poster' not in inventory:
                    inventory.append('fake_poster')
            elif obj.name == 'good' and has_fake_poster and not decoded:
                current_dialog = "That poster seems fake. Go to the detective table and properly investigate it."
            else:
                current_dialog = "I've told you everything I know."

    elif obj.name == 'telephone' and quest_started and len(npcs_interacted) == len(total_npcs) and not reported:
        show_choice = True
        choices = [
            "Report order: Fire, posters, mayor left.",
            "Report order: Fire, mayor left, posters.",
            "Report order: Posters, fire, mayor left."
        ]
        choice_context = "report"
        current_dialog = "Choose the correct order of events to report:"

    elif obj.name == 'table' and has_fake_poster and not decoded:
        show_choice = True
        choices = ["Add strong acid to photo", "Properly investigate the photo"]
        choice_context = "decode"
        current_dialog = "What to do with the poster?"

    elif obj.name == 'mayor' and has_real_poster and not confronted:
        show_choice = True
        choices = ["Mayor is AI", "Mayor is not AI"]
        choice_context = "confront"
        current_dialog = "Confront the mayor: Is he AI?"

    else:
        if obj.name == 'table' and evidence_destroyed:
            current_dialog = "The evidence is destroyed. Nothing left to do."
        elif obj.name == 'mayor' and not has_real_poster:
            current_dialog = "I need evidence before confronting the mayor."
        else:
            current_dialog = "Nothing to do here right now."

# Function to handle choice selection
def handle_choice(idx):
    global reported, decoded, has_real_poster, confronted, current_dialog, show_choice, choice_context, evidence_destroyed, has_fake_poster, game_over, game_over_message, inventory, current_state

    if game_over:
        return

    if choice_context == "report":
        if idx == 1:  # Correct order
            reported = True
            current_dialog = "Correct order reported. The suspect is spreading fake rumors. Confront the suspect."
        else:
            current_dialog = "Incorrect order. Gather more info or try again."
        show_choice = False
        choice_context = ""

    elif choice_context == "decode":
        if idx == 0:  # Acid
            evidence_destroyed = True
            has_fake_poster = False
            decoded = True
            current_dialog = "The acid destroys the poster. Evidence lost."
            game_over = True
            game_over_message = "Evidence destroyed. Game Over."
            current_state = STATE_GAME_OVER
            if 'fake_poster' in inventory:
                inventory.remove('fake_poster')
        else:  # Investigate
            decoded = True
            has_real_poster = True
            has_fake_poster = False
            current_dialog = "Proper investigation reveals the real poster. \n view in your inventory and confront the mayor"
            if 'fake_poster' in inventory:
                inventory.remove('fake_poster')
            if 'real_poster' not in inventory:
                inventory.append('real_poster')
        show_choice = False
        choice_context = ""

    elif choice_context == "confront":
        confronted = True
        if idx == 0:
            current_dialog = "You chose: Mayor is AI."
            game_over_message = "Mayor is AI. Game Over."
            current_state = STATE_GAME_OVER
        else:
            current_dialog = "You chose: Mayor is not AI."
            game_over_message = "Mayor is not AI. Game Complete."
            current_state = STATE_GAME_COMPLETE
        show_choice = False
        choice_context = ""

# Camera function
def get_camera_offset(player_rect):
    cam_x = player_rect.centerx - 640  # Half screen width
    cam_y = player_rect.centery - 360  # Half screen height
    cam_x = max(0, min(cam_x, WORLD_WIDTH - 1280))
    cam_y = max(0, min(cam_y, WORLD_HEIGHT - 720))
    return -cam_x, -cam_y

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            if current_state == STATE_TITLE:
                if event.key == K_RETURN:
                    current_state = STATE_PROLOGUE
            elif current_state == STATE_PROLOGUE:
                if event.key == K_RETURN:
                    prologue_index += 1
                    if prologue_index >= len(prologue_texts):
                        current_state = STATE_PLAYING
                        prologue_index = 0
            elif current_state == STATE_PLAYING:
                if event.key == K_e:
                    if not game_over and not show_inventory:
                        collided = pygame.sprite.spritecollide(player, interactables, False)
                        if collided:
                            handle_interaction(collided[0])
                if event.key == K_q:
                    if current_dialog:
                        current_dialog = ""
                        show_choice = False
                if event.key == K_i:
                    show_inventory = not show_inventory
                if show_choice:
                    if event.key == K_UP:
                        selected_choice = (selected_choice - 1) % len(choices)
                    if event.key == K_DOWN:
                        selected_choice = (selected_choice + 1) % len(choices)
                    if event.key == K_RETURN:
                        handle_choice(selected_choice)
            elif current_state in (STATE_GAME_OVER, STATE_GAME_COMPLETE):
                if event.key == K_r:
                    reset_game()
                if event.key == K_ESCAPE:
                    running = False

    if current_state == STATE_PLAYING:
        keys = pygame.key.get_pressed()
        player.update(keys, collidables)

    # Drawing
    screen.fill((0, 0, 0))
    if current_state == STATE_TITLE:
        draw_title()
    elif current_state == STATE_PROLOGUE:
        draw_prologue(prologue_index)
    elif current_state == STATE_PLAYING:
        # Draw game world
        offset_x, offset_y = get_camera_offset(player.rect)
        screen.blit(images['background/background.png'], (offset_x, offset_y))
        for sprite in all_sprites:
            screen.blit(sprite.image, (sprite.rect.x + offset_x, sprite.rect.y + offset_y))
        if current_dialog:
            draw_dialog(current_dialog, current_npc_img)
        if show_choice:
            for i, ch in enumerate(choices):
                color = (255, 255, 0) if i == selected_choice else (255, 255, 255)
                text = font.render(ch, True, color)
                screen.blit(text, (10, 500 + i * 40))
        if show_inventory:
            draw_inventory()
        draw_indicators()
    elif current_state == STATE_GAME_OVER:
        draw_game_over()
    elif current_state == STATE_GAME_COMPLETE:
        draw_game_complete()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()