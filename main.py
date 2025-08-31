import pygame
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH = 1000
HEIGHT = 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Detective vs. AI Misinformation")

# Load background image
try:
    BACKGROUND_IMAGE = pygame.image.load("background.png").convert()
    BACKGROUND_IMAGE = pygame.transform.scale(BACKGROUND_IMAGE, (WIDTH, HEIGHT))
except pygame.error:
    print("Warning: background.png not found. Using black background.")
    BACKGROUND_IMAGE = None

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255) # Player color
GREEN = (0, 200, 0) # Helpful NPC color
RED = (200, 0, 0) # Rumor NPC color
LIGHT_GREY = (200, 200, 200)
DARK_GREY = (50, 50, 50)
YELLOW = (255, 255, 0) # Quest indicator
CYAN = (0, 255, 255) # Corrupted Terminal color

# Fonts
font = pygame.font.Font(None, 36)
dialogue_font = pygame.font.Font(None, 28)
title_font = pygame.font.Font(None, 72)
button_font = pygame.font.Font(None, 48)

# Game States
START_SCREEN = 0
PROLOGUE = 1
EXPLORATION = 2
DIALOGUE = 3
QUEST_LOG = 4
DECISION_MAKING = 5 # New state for mayor decision

# Player properties
PLAYER_SIZE = 40
PLAYER_SPEED = 4

# NPC properties
NPC_SIZE = 40

# Corrupted Terminal properties
TERMINAL_SIZE = 30

# New asset sizes
QUEST_TRIGGER_SIZE = 40
MAYOR_SIZE = 60 # Mayor might be larger
NPC_GOOD_SIZE = 40
NPC_BAD_SIZE = 40

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            self.image = pygame.image.load("detective.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (PLAYER_SIZE, PLAYER_SIZE))
            print("DEBUG: detective.png loaded successfully.")
        except pygame.error:
            print("DEBUG: Warning: detective.png not found. Using default blue square for player.")
            self.image = pygame.Surface([PLAYER_SIZE, PLAYER_SIZE])
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        print(f"DEBUG: Player initialized at center: {self.rect.center}")

# Load new images
try:
    QUEST_IMAGE = pygame.image.load("quest.png").convert_alpha()
    QUEST_IMAGE = pygame.transform.scale(QUEST_IMAGE, (QUEST_TRIGGER_SIZE, QUEST_TRIGGER_SIZE))
except pygame.error:
    print("Warning: quest.png not found. Using default yellow square for quest trigger.")
    QUEST_IMAGE = None

try:
    NPC_GOOD_IMAGE = pygame.image.load("npc_good.png").convert_alpha()
    NPC_GOOD_IMAGE = pygame.transform.scale(NPC_GOOD_IMAGE, (NPC_GOOD_SIZE, NPC_GOOD_SIZE))
except pygame.error:
    print("Warning: npc_good.png not found. Using default green square for good NPC.")
    NPC_GOOD_IMAGE = None

try:
    NPC_BAD_IMAGE = pygame.image.load("npc_bad.png").convert_alpha()
    NPC_BAD_IMAGE = pygame.transform.scale(NPC_BAD_IMAGE, (NPC_BAD_SIZE, NPC_BAD_SIZE))
except pygame.error:
    print("Warning: npc_bad.png not found. Using default red square for bad NPC.")
    NPC_BAD_IMAGE = None

try:
    MAYOR_IMAGE = pygame.image.load("mayor.png").convert_alpha()
    MAYOR_IMAGE = pygame.transform.scale(MAYOR_IMAGE, (MAYOR_SIZE, MAYOR_SIZE))
except pygame.error:
    print("Warning: mayor.png not found. Using default blue square for mayor.")
    MAYOR_IMAGE = None

    def update(self, keys):
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED
        if keys[pygame.K_UP]:
            self.rect.y -= PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            self.rect.y += PLAYER_SPEED

        # Keep player within screen bounds
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT

class NPC(pygame.sprite.Sprite):
    def __init__(self, x, y, name, dialogue_states, is_helpful=True, quest_to_give=None, quest_to_complete=None, image_asset=None):
        super().__init__()
        if image_asset:
            self.original_image = image_asset
            self.image = self.original_image.copy()
        else:
            try:
                self.original_image = pygame.image.load("npc.png").convert_alpha()
                self.original_image = pygame.transform.scale(self.original_image, (NPC_SIZE, NPC_SIZE))
                self.image = self.original_image.copy()
            except pygame.error:
                print(f"Warning: npc.png not found. Using default {'green' if is_helpful else 'red'} square for {name}.")
                self.image = pygame.Surface([NPC_SIZE, NPC_SIZE])
        self.color = GREEN if is_helpful else RED # This color is still used for fallback square
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.name = name
        self.dialogue_states = dialogue_states # Dictionary of dialogue based on quest status
        self.is_helpful = is_helpful
        self.quest_to_give = quest_to_give # ID of quest this NPC gives
        self.quest_to_complete = quest_to_complete # ID of quest this NPC completes

    def get_dialogue(self, player_quests):
        # Determine current dialogue based on quest status
        # Special handling for Mayor decision point
        if self.name == "Mayor" and "quest_chapter_1_mayor" in player_quests:
            mayor_quest = player_quests["quest_chapter_1_mayor"]
            if mayor_quest['objectives']["subquest_good_npc_info"]['completed'] and \
               mayor_quest['objectives']["subquest_bad_npc_analysis"]['completed'] and \
               'ready_for_decision' in self.dialogue_states:
                return self.dialogue_states['ready_for_decision']

        for quest_id, quest_data in player_quests.items():
            if quest_id == self.quest_to_complete and quest_data['status'] == 'IN_PROGRESS':
                # Check if all objectives are met for completion dialogue
                all_objectives_met = True
                for obj_key, obj_val in quest_data['objectives'].items():
                    if not obj_val['completed']:
                        all_objectives_met = False
                        break
                
                if all_objectives_met and 'completion' in self.dialogue_states:
                    return self.dialogue_states['completion']
                elif 'during' in self.dialogue_states:
                    return self.dialogue_states['during'] # Still in progress, but not ready to complete

            elif quest_id == self.quest_to_give and quest_data['status'] == 'NOT_STARTED' and 'initial' in self.dialogue_states:
                return self.dialogue_states['initial']
            elif quest_id == self.quest_to_give and quest_data['status'] == 'IN_PROGRESS' and 'during' in self.dialogue_states:
                return self.dialogue_states['during']

        # Default dialogue if no specific quest state matches
        return self.dialogue_states.get('default', [f"Hello, I am {self.name}."])


class Quest:
    def __init__(self, q_id, title, description, objectives, giver_npc_name, completion_npc_name):
        self.id = q_id
        self.title = title
        self.description = description
        # Objectives is now a dictionary: {"objective_key": {"desc": "description", "completed": False}}
        self.objectives = {obj_key: {"desc": obj_desc, "completed": False} for obj_key, obj_desc in objectives.items()}
        self.status = 'NOT_STARTED' # NOT_STARTED, IN_PROGRESS, COMPLETED
        self.giver_npc_name = giver_npc_name
        self.completion_npc_name = completion_npc_name

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'objectives': self.objectives,
            'status': self.status,
            'giver_npc_name': self.giver_npc_name,
            'completion_npc_name': self.completion_npc_name
        }

class QuestTrigger(pygame.sprite.Sprite):
    def __init__(self, x, y, quest_id):
        super().__init__()
        self.image = QUEST_IMAGE if QUEST_IMAGE else pygame.Surface([QUEST_TRIGGER_SIZE, QUEST_TRIGGER_SIZE])
        if not QUEST_IMAGE:
            self.image.fill(YELLOW) # Fallback color
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.quest_id = quest_id
        self.interacted = False # To ensure it only triggers once

class CorruptedTerminal(pygame.sprite.Sprite):
    def __init__(self, x, y, terminal_id):
        super().__init__()
        self.image = pygame.Surface([TERMINAL_SIZE, TERMINAL_SIZE])
        self.image.fill(CYAN)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.terminal_id = terminal_id
        self.interacted = False

# Dialogue Box function
def draw_dialogue_box(screen, text):
    # Dialogue box background
    box_height = 150
    box_rect = pygame.Rect(50, HEIGHT - box_height - 20, WIDTH - 100, box_height)
    pygame.draw.rect(screen, DARK_GREY, box_rect)
    pygame.draw.rect(screen, LIGHT_GREY, box_rect, 3) # Border

    # Dialogue text
    text_surface = dialogue_font.render(text, True, WHITE)
    screen.blit(text_surface, (box_rect.x + 20, box_rect.y + 20))

    # Prompt to continue
    prompt_text = dialogue_font.render("Press SPACE to continue...", True, LIGHT_GREY)
    screen.blit(prompt_text, (box_rect.right - prompt_text.get_width() - 20, box_rect.bottom - prompt_text.get_height() - 10))

def draw_quest_log(screen, active_quests):
    log_rect = pygame.Rect(WIDTH // 4, HEIGHT // 8, WIDTH // 2, HEIGHT * 3 // 4)
    pygame.draw.rect(screen, DARK_GREY, log_rect)
    pygame.draw.rect(screen, LIGHT_GREY, log_rect, 3)

    title_text = font.render("Quest Log", True, WHITE)
    screen.blit(title_text, (log_rect.x + 20, log_rect.y + 20))

    y_offset = 60
    if not active_quests:
        no_quests_text = dialogue_font.render("No active quests.", True, WHITE)
        screen.blit(no_quests_text, (log_rect.x + 20, log_rect.y + y_offset))
    else:
        for q_id, quest_data in active_quests.items():
            quest_title = dialogue_font.render(f"- {quest_data['title']}", True, YELLOW)
            screen.blit(quest_title, (log_rect.x + 20, log_rect.y + y_offset))
            y_offset += 30
            quest_desc = dialogue_font.render(f"  {quest_data['description']}", True, WHITE)
            screen.blit(quest_desc, (log_rect.x + 30, log_rect.y + y_offset))
            y_offset += 30
            for obj_key, obj_val in quest_data['objectives'].items():
                status = "[X]" if obj_val['completed'] else "[ ]"
                obj_text = dialogue_font.render(f"    {status} {obj_val['desc']}", True, LIGHT_GREY)
                screen.blit(obj_text, (log_rect.x + 40, log_rect.y + y_offset))
                y_offset += 25
            y_offset += 10 # Spacing between quests

    close_text = dialogue_font.render("Press Q to close", True, LIGHT_GREY)
    screen.blit(close_text, (log_rect.x + 20, log_rect.bottom - 40))

def draw_decision_screen(screen):
    screen.fill(BLACK)
    prompt_text = title_font.render("What is your verdict, Detective?", True, WHITE)
    prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(prompt_text, prompt_rect)

    human_button_text = button_font.render("Mayor is Human", True, BLACK)
    human_button_rect = human_button_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    human_button_bg_rect = human_button_rect.inflate(40, 20)
    pygame.draw.rect(screen, GREEN, human_button_bg_rect, border_radius=10)
    pygame.draw.rect(screen, LIGHT_GREY, human_button_bg_rect, 3, border_radius=10)
    screen.blit(human_button_text, human_button_rect)

    ai_button_text = button_font.render("Mayor is AI", True, BLACK)
    ai_button_rect = ai_button_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
    ai_button_bg_rect = ai_button_rect.inflate(40, 20)
    pygame.draw.rect(screen, RED, ai_button_bg_rect, border_radius=10)
    pygame.draw.rect(screen, LIGHT_GREY, ai_button_bg_rect, 3, border_radius=10)
    screen.blit(ai_button_text, ai_button_rect)

    return human_button_bg_rect, ai_button_bg_rect # Return rects for click detection

def draw_start_screen(screen):
    screen.fill(BLACK)
    title_text = title_font.render("Detective vs. AI Misinformation", True, WHITE)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(title_text, title_rect)

    start_button_text = button_font.render("Start Game", True, BLACK)
    start_button_rect = start_button_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
    
    # Draw button background
    button_bg_rect = start_button_rect.inflate(40, 20) # Add padding
    pygame.draw.rect(screen, WHITE, button_bg_rect, border_radius=10)
    pygame.draw.rect(screen, LIGHT_GREY, button_bg_rect, 3, border_radius=10)

    screen.blit(start_button_text, start_button_rect)
    return button_bg_rect # Return the rect for click detection

def draw_prologue(screen, text):
    screen.fill(BLACK)
    prologue_surface = dialogue_font.render(text, True, WHITE)
    prologue_rect = prologue_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(prologue_surface, prologue_rect)

    prompt_text = dialogue_font.render("Press SPACE to continue...", True, LIGHT_GREY)
    prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))
    screen.blit(prompt_text, prompt_rect)

# Game variables
player = Player()
all_sprites = pygame.sprite.Group()
all_sprites.add(player)
npcs = pygame.sprite.Group()

# Define Quests
quest1 = Quest(
    q_id="quest_data_leak",
    title="The Data Leak",
    description="A citizen reported strange data packets. Investigate the source.",
    objectives={
        "find_terminal": "Find the corrupted terminal.",
        "report_citizen_a": "Report back to Citizen A."
    },
    giver_npc_name="Citizen A",
    completion_npc_name="Citizen A"
)

quest2 = Quest(
    q_id="quest_rumor_debunk",
    title="Debunk the Rumor",
    description="A rumor-monger is spreading false information. Convince them otherwise.",
    objectives={
        "talk_to_rumor_b": "Talk to Rumor-Monger B and debunk their claim.",
        "report_citizen_c": "Report back to Citizen C."
    },
    giver_npc_name="Citizen C",
    completion_npc_name="Citizen C"
)

quest_chapter_1_mayor = Quest(
    q_id="quest_chapter_1_mayor",
    title="The First Leak: Mayor's Identity",
    description="A viral video claims the mayor is an AI impostor. Investigate and determine the truth.",
    objectives={
        "subquest_good_npc_info": "Gather information from the helpful NPC.",
        "subquest_bad_npc_analysis": "Analyze the misleading claims from the suspicious NPC.",
        "talk_to_mayor_for_decision": "Talk to the Mayor to make your final decision."
    },
    giver_npc_name="Quest Trigger", # This quest is given by interacting with the quest trigger
    completion_npc_name="Mayor" # The Mayor will be the final decision point
)

# Store quests in a dictionary for easy lookup
available_quests = {
    quest1.id: quest1.to_dict(),
    quest2.id: quest2.to_dict(),
    quest_chapter_1_mayor.id: quest_chapter_1_mayor.to_dict()
}
active_quests = {}
completed_quests = {}

# Define NPCs with their dialogue states and quest associations
n_npcs = 5 # Number of NPCs

n_npcs_to_spawn = n_npcs # Keep track of how many random NPCs to spawn

n_npcs_to_spawn -= 1 # For Citizen A
# Citizen A (Gives Quest 1, Completes Quest 1)
citizen_a_dialogue = {
    'initial': [
        "Detective! Thank goodness you're here. There's a strange data leak happening.",
        "It's causing glitches in my comms. Can you investigate?",
        "I think it's coming from the old data hub, near the market. Look for a glowing blue terminal."
    ],
    'during': [
        "Any luck with the data leak, detective? It's getting worse.",
        "Have you found that terminal yet?"
    ],
    'completion': [
        "You found the source! Thank you, detective. The comms are clearing up.",
        "You've done a great service to the city."
    ],
    'default': [
        "The city feels safer now, thanks to you."
    ]
}
citizen_a = NPC(100, 100, "Citizen A", citizen_a_dialogue, is_helpful=True, quest_to_give="quest_data_leak", quest_to_complete="quest_data_leak")

n_npcs_to_spawn -= 1 # For Citizen C
# Citizen C (Gives Quest 2, Completes Quest 2)
citizen_c_dialogue = {
    'initial': [
        "Detective, there's a persistent rumor going around about the AI.",
        "It's completely false and causing panic. Can you debunk it?",
        "Rumor-Monger B is spreading it near the central plaza. Try to talk some sense into them."
    ],
    'during': [
        "Have you managed to talk sense into Rumor-Monger B yet?"
    ],
    'completion': [
        "Excellent! I heard Rumor-Monger B is finally quiet. Good work."
    ],
    'default': [
        "The truth always prevails."
    ]
}
citizen_c = NPC(700, 200, "Citizen C", citizen_c_dialogue, is_helpful=True, quest_to_give="quest_rumor_debunk", quest_to_complete="quest_rumor_debunk")

n_npcs_to_spawn -= 1 # For Rumor-Monger B
# Rumor-Monger B (Objective for Quest 2)
rumor_b_dialogue = {
    'initial': [
        "The AI is failing us! It's all going to collapse!",
        "Don't believe the official reports! They're hiding the truth!"
    ],
    'debunked': [
        "...Wait, what? Are you sure? Maybe I was mistaken...",
        "I... I need to rethink things."
    ],
    'default': [
        "I'm still thinking..."
    ]
}
rumor_monger_b = NPC(300, 500, "Rumor-Monger B", rumor_b_dialogue, is_helpful=False)

n_npcs_to_spawn -= 1 # For NPC Good
# NPC Good (Provides helpful hints for subquests)
npc_good_dialogue = {
    'initial': [
        "Hello, Detective. I've heard whispers about the mayor. It's a tricky situation.",
        "Some say he's an AI, others say it's a smear campaign.",
        "Look for inconsistencies in the information you gather. AI often leaves subtle digital footprints."
    ],
    'subquest_good_info_complete': [
        "You're doing well, Detective. Remember, not everything you see or hear is real.",
        "Trust your instincts, but verify everything."
    ],
    'default': [
        "Keep digging for the truth."
    ]
}
npc_good = NPC(200, 300, "NPC Good", npc_good_dialogue, is_helpful=True, image_asset=NPC_GOOD_IMAGE)

n_npcs_to_spawn -= 1 # For NPC Bad
# NPC Bad (Tries to mislead the player)
npc_bad_dialogue = {
    'initial': [
        "Psst, Detective. Don't believe the official story. The mayor is definitely an AI.",
        "I have 'evidence' that proves it. Just look at this perfectly crafted video.",
        "It's so convincing, isn't it? No human could fake this."
    ],
    'subquest_bad_info_complete': [
        "Did you fall for it, Detective? The truth is what you make it.",
        "Don't let anyone tell you otherwise."
    ],
    'default': [
        "The truth is subjective, isn't it?"
    ]
}
npc_bad = NPC(800, 400, "NPC Bad", npc_bad_dialogue, is_helpful=False, image_asset=NPC_BAD_IMAGE)

n_npcs_to_spawn -= 1 # For Mayor
# Mayor (Final decision point for Chapter 1)
mayor_dialogue = {
    'initial': [
        "Detective, I understand you're investigating the rumors about me.",
        "I assure you, I am human. These accusations are baseless."
    ],
    'ready_for_decision': [
        "Detective, have you concluded your investigation into my identity?",
        "What is your verdict? Am I human, or an AI impostor?"
    ],
    'human_choice': [
        "Thank you, Detective. Your keen eye for truth has saved my reputation and the city from further unrest.",
        "The riots are quelled. We can now focus on rebuilding trust. Proceed to the next chapter."
    ],
    'ai_choice': [
        "You believe I am an AI? This is a grave error, Detective.",
        "Your misjudgment has fueled the riots, and the city descends into anarchy. Game Over."
    ],
    'default': [
        "The truth will always prevail."
    ]
}
mayor = NPC(WIDTH // 2 - MAYOR_SIZE // 2, HEIGHT // 2 - MAYOR_SIZE // 2, "Mayor", mayor_dialogue, is_helpful=True, image_asset=MAYOR_IMAGE)

n_npcs_to_spawn -= 1 # For Corrupted Terminal
# Corrupted Terminal (Objective for Quest 1)
corrupted_terminal = CorruptedTerminal(random.randint(50, WIDTH - 50 - TERMINAL_SIZE), random.randint(50, HEIGHT - 200 - TERMINAL_SIZE), "data_hub_terminal_01")

# Quest Trigger for Chapter 1
chapter_1_quest_trigger = QuestTrigger(WIDTH // 2 - QUEST_TRIGGER_SIZE // 2, HEIGHT // 4, "quest_chapter_1_mayor")

npcs.add(citizen_a, citizen_c, rumor_monger_b, npc_good, npc_bad, mayor)

# Add remaining random NPCs
for i in range(n_npcs_to_spawn):
    x = random.randint(50, WIDTH - 50 - NPC_SIZE)
    y = random.randint(50, HEIGHT - 200 - NPC_SIZE)
    is_helpful = random.choice([True, False])
    dialogue = {
        'default': [f"Hello, I am Random Citizen {i}.", "Nothing much to say."]
    }
    npcs.add(NPC(x, y, f"Random Citizen {i}", dialogue, is_helpful=is_helpful))

all_sprites.add(npcs)
all_sprites.add(corrupted_terminal)
all_sprites.add(chapter_1_quest_trigger)

current_game_state = START_SCREEN
current_dialogue_npc = None
current_dialogue_line_index = 0

# Game message variables
quest_accepted_message = None
message_display_time = 0

prologue_text = [
    "In a city shrouded by digital mist, where information flows like a corrupted river,",
    "a new threat emerges: AI-driven misinformation, twisting truths and sowing discord.",
    "You are the last line of defense, a detective of data, tasked with uncovering the truth.",
    "Navigate the neon-lit streets, interrogate citizens, and hack into corrupted terminals.",
    "Your mission: expose the source of the misinformation and restore order to the city."
]
current_prologue_line_index = 0

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if current_game_state == EXPLORATION:
                if event.key == pygame.K_e: # Interact key
                    # Check for NPC interaction
                    for npc in npcs:
                        if pygame.sprite.collide_rect(player, npc):
                            current_dialogue_npc = npc
                            current_dialogue_line_index = 0
                            current_game_state = DIALOGUE
                            break
                    # Check for Corrupted Terminal interaction
                    for terminal in all_sprites:
                        if isinstance(terminal, CorruptedTerminal) and pygame.sprite.collide_rect(player, terminal):
                            if not terminal.interacted: # Only interact once
                                terminal.interacted = True
                                # Check if this interaction completes an objective
                                if "quest_data_leak" in active_quests and \
                                   active_quests["quest_data_leak"]['objectives']["find_terminal"]['completed'] == False:
                                    active_quests["quest_data_leak"]['objectives']["find_terminal"]['completed'] = True
                                    quest_accepted_message = "Objective Complete: Find the corrupted terminal."
                                    message_display_time = pygame.time.get_ticks() + 2000
                                    print("Objective 'find_terminal' for quest_data_leak completed!") # Debug
                            break # Only interact with one terminal at a time
                    
                    # Check for Quest Trigger interaction
                    for trigger in all_sprites:
                        if isinstance(trigger, QuestTrigger) and pygame.sprite.collide_rect(player, trigger):
                            if not trigger.interacted: # Only interact once
                                trigger.interacted = True
                                if trigger.quest_id == "quest_chapter_1_mayor" and \
                                   "quest_chapter_1_mayor" in available_quests and \
                                   available_quests["quest_chapter_1_mayor"]['status'] == 'NOT_STARTED':
                                    quest_id = "quest_chapter_1_mayor"
                                    active_quests[quest_id] = available_quests[quest_id]
                                    active_quests[quest_id]['status'] = 'IN_PROGRESS'
                                    quest_accepted_message = f"Quest Accepted: {active_quests[quest_id]['title']}"
                                    message_display_time = pygame.time.get_ticks() + 2000
                                    print(f"Quest Accepted: {active_quests[quest_id]['title']}") # Debug
                            break # Only interact with one trigger at a time

                elif event.key == pygame.K_q: # Open Quest Log
                    current_game_state = QUEST_LOG

            elif current_game_state == DIALOGUE:
                if event.key == pygame.K_SPACE: # Advance dialogue
                    # Handle quest giving/completion logic here
                    current_dialogue_text = current_dialogue_npc.get_dialogue(active_quests)[current_dialogue_line_index]

                    if current_dialogue_line_index == len(current_dialogue_npc.get_dialogue(active_quests)) - 1: # Last line of dialogue
                        # Special handling for Mayor decision
                        if current_dialogue_npc.name == "Mayor" and \
                           "quest_chapter_1_mayor" in active_quests and \
                           active_quests["quest_chapter_1_mayor"]['objectives']["subquest_good_npc_info"]['completed'] and \
                           active_quests["quest_chapter_1_mayor"]['objectives']["subquest_bad_npc_analysis"]['completed']:
                            current_game_state = DECISION_MAKING
                            current_dialogue_npc = None # Clear NPC to prevent further dialogue
                            current_dialogue_line_index = 0
                            continue # Skip normal dialogue progression

                        # Check if NPC gives a quest
                        if current_dialogue_npc.quest_to_give and available_quests.get(current_dialogue_npc.quest_to_give, {}).get('status') == 'NOT_STARTED':
                            quest_id = current_dialogue_npc.quest_to_give
                            active_quests[quest_id] = available_quests[quest_id]
                            active_quests[quest_id]['status'] = 'IN_PROGRESS'
                            quest_accepted_message = f"Quest Accepted: {active_quests[quest_id]['title']}"
                            message_display_time = pygame.time.get_ticks() + 2000 # Display for 2 seconds
                            print(f"Quest Accepted: {active_quests[quest_id]['title']}") # Debug

                        # Check for Chapter 1 quest objectives completion
                        if "quest_chapter_1_mayor" in active_quests and \
                           active_quests["quest_chapter_1_mayor"]['status'] == 'IN_PROGRESS':
                            if current_dialogue_npc.name == "NPC Good" and \
                               active_quests["quest_chapter_1_mayor"]['objectives']["subquest_good_npc_info"]['completed'] == False:
                                active_quests["quest_chapter_1_mayor"]['objectives']["subquest_good_npc_info"]['completed'] = True
                                quest_accepted_message = "Objective Complete: Gather information from helpful NPC."
                                message_display_time = pygame.time.get_ticks() + 2000
                                print("Objective 'subquest_good_npc_info' for quest_chapter_1_mayor completed!") # Debug
                            elif current_dialogue_npc.name == "NPC Bad" and \
                                 active_quests["quest_chapter_1_mayor"]['objectives']["subquest_bad_npc_analysis"]['completed'] == False:
                                active_quests["quest_chapter_1_mayor"]['objectives']["subquest_bad_npc_analysis"]['completed'] = True
                                quest_accepted_message = "Objective Complete: Analyze misleading claims from suspicious NPC."
                                message_display_time = pygame.time.get_ticks() + 2000
                                print("Objective 'subquest_bad_npc_analysis' for quest_chapter_1_mayor completed!") # Debug

                        # Check if NPC completes a quest
                        if current_dialogue_npc.quest_to_complete:
                            quest_id = current_dialogue_npc.quest_to_complete
                            if active_quests.get(quest_id, {}).get('status') == 'IN_PROGRESS':
                                # Check if all objectives are met
                                all_objectives_met = True
                                for obj_key, obj_val in active_quests[quest_id]['objectives'].items():
                                    if not obj_val['completed']:
                                        all_objectives_met = False
                                        break

                                if all_objectives_met:
                                    active_quests[quest_id]['status'] = 'COMPLETED'
                                    completed_quests[quest_id] = active_quests.pop(quest_id)
                                    quest_accepted_message = f"Quest Completed: {completed_quests[quest_id]['title']}"
                                    message_display_time = pygame.time.get_ticks() + 2000
                                    print(f"Quest Completed: {completed_quests[quest_id]['title']}") # Debug

                                    # Mark 'report back' objective as complete if it exists
                                    if "report_citizen_a" in completed_quests[quest_id]['objectives']:
                                        completed_quests[quest_id]['objectives']["report_citizen_a"]['completed'] = True
                                    if "report_citizen_c" in completed_quests[quest_id]['objectives']:
                                        completed_quests[quest_id]['objectives']["report_citizen_c"]['completed'] = True

                                    # Special dialogue for Rumor-Monger B after debunking
                                    if current_dialogue_npc.name == "Rumor-Monger B":
                                        current_dialogue_npc.dialogue_states['initial'] = current_dialogue_npc.dialogue_states['debunked']
                                        # Mark objective for talking to Rumor-Monger B as complete
                                        if "quest_rumor_debunk" in active_quests and \
                                           active_quests["quest_rumor_debunk"]['objectives']["talk_to_rumor_b"]['completed'] == False:
                                            active_quests["quest_rumor_debunk"]['objectives']["talk_to_rumor_b"]['completed'] = True
                                            quest_accepted_message = "Objective Complete: Talk to Rumor-Monger B."
                                            message_display_time = pygame.time.get_ticks() + 2000
                                            print("Objective 'talk_to_rumor_b' for quest_rumor_debunk completed!") # Debug


                        current_game_state = EXPLORATION
                        current_dialogue_npc = None
                        current_dialogue_line_index = 0
                    else:
                        current_dialogue_line_index += 1

            elif current_game_state == PROLOGUE:
                if event.key == pygame.K_SPACE:
                    current_prologue_line_index += 1
                    if current_prologue_line_index >= len(prologue_text):
                        current_game_state = EXPLORATION

            elif current_game_state == QUEST_LOG:
                if event.key == pygame.K_q: # Close Quest Log
                    current_game_state = EXPLORATION

        if event.type == pygame.MOUSEBUTTONDOWN: # Handle mouse clicks for buttons
            if current_game_state == START_SCREEN:
                if start_button_rect.collidepoint(event.pos):
                    current_game_state = PROLOGUE
                    current_prologue_line_index = 0
            elif current_game_state == DECISION_MAKING:
                if human_button_rect.collidepoint(event.pos):
                    # Correct choice: Mayor is Human
                    print("Player chose: Mayor is Human (Correct)") # Debug
                    active_quests["quest_chapter_1_mayor"]['objectives']["make_decision"]['completed'] = True
                    active_quests["quest_chapter_1_mayor"]['status'] = 'COMPLETED'
                    completed_quests["quest_chapter_1_mayor"] = active_quests.pop("quest_chapter_1_mayor")
                    quest_accepted_message = "Chapter 1 Complete: Mayor cleared, riots stopped!"
                    message_display_time = pygame.time.get_ticks() + 3000
                    current_game_state = EXPLORATION # Proceed to next chapter/exploration
                elif ai_button_rect.collidepoint(event.pos):
                    # Incorrect choice: Mayor is AI
                    print("Player chose: Mayor is AI (Incorrect - Game Over)") # Debug
                    # For now, just exit the game for "Game Over"
                    running = False # This will end the game loop

    # Drawing

    if current_game_state == START_SCREEN:
        start_button_rect = draw_start_screen(SCREEN)
    elif current_game_state == PROLOGUE:
        draw_prologue(SCREEN, prologue_text[current_prologue_line_index])
    elif current_game_state == DECISION_MAKING:
        human_button_rect, ai_button_rect = draw_decision_screen(SCREEN)
    elif current_game_state == EXPLORATION:
        if BACKGROUND_IMAGE:
            SCREEN.blit(BACKGROUND_IMAGE, (0, 0))
        else:
            SCREEN.fill(BLACK)
        keys = pygame.key.get_pressed()
        player.update(keys)
        print(f"DEBUG: Player position: {player.rect.center}")
        all_sprites.draw(SCREEN)
        print("DEBUG: all_sprites.draw(SCREEN) called.")

        # Draw quest indicators (simple yellow square above NPC if they give/complete a quest)
        # If you want to use an image for the quest indicator, uncomment and modify the following:
        # try:
        #     quest_indicator_image = pygame.image.load("quest_indicator.png").convert_alpha()
        #     quest_indicator_image = pygame.transform.scale(quest_indicator_image, (NPC_SIZE // 2, 10))
        # except pygame.error:
        #     quest_indicator_image = None

        for npc in npcs:
            if npc.quest_to_give and available_quests.get(npc.quest_to_give, {}).get('status') == 'NOT_STARTED':
                pygame.draw.rect(SCREEN, YELLOW, (npc.rect.x + NPC_SIZE // 4, npc.rect.y - 15, NPC_SIZE // 2, 10))
            elif npc.quest_to_complete and active_quests.get(npc.quest_to_complete, {}).get('status') == 'IN_PROGRESS':
                # Check if all objectives are met to show completion indicator
                all_objectives_met = True
                quest_id = npc.quest_to_complete
                if quest_id in active_quests:
                    for obj_key, obj_val in active_quests[quest_id]['objectives'].items():
                        if not obj_val['completed']:
                            all_objectives_met = False
                            break
                else: # Quest not in active_quests, so no indicator
                    all_objectives_met = False

                if all_objectives_met:
                    pygame.draw.rect(SCREEN, YELLOW, (npc.rect.x + NPC_SIZE // 4, npc.rect.y - 15, NPC_SIZE // 2, 10))
    
    # These are now outside the EXPLORATION block to act as overlays
    if current_game_state == DIALOGUE and current_dialogue_npc:
        draw_dialogue_box(SCREEN, current_dialogue_npc.get_dialogue(active_quests)[current_dialogue_line_index])
    elif current_game_state == QUEST_LOG:
        draw_quest_log(SCREEN, active_quests)

        # Display temporary quest accepted message
        if quest_accepted_message and pygame.time.get_ticks() < message_display_time:
            message_text = font.render(quest_accepted_message, True, YELLOW)
            message_rect = message_text.get_rect(center=(WIDTH // 2, 50))
            SCREEN.blit(message_text, message_rect)

    pygame.display.flip()

    # Cap the frame rate
    pygame.time.Clock().tick(60)

pygame.quit()