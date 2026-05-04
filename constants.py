"""Game-wide constants. Tweak gameplay feel here."""

# Display
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
TILE_SIZE = 64
SPRITE_SIZE = 56          # default sprite size (player, T-rex)
BRACHIO_SPRITE_SIZE = 64  # brachiosaurus is the biggest dino — fills its tile

# Colors
COLOR_BG = (15, 15, 18)
COLOR_FOG = (0, 0, 0)
COLOR_FOREST_FLOOR = (60, 100, 50)   # lighter jungle green
COLOR_PATH = (162, 138, 95)          # sandy fill behind road tiles
COLOR_EXIT = (245, 205, 75)
COLOR_HUD = (240, 240, 240)
COLOR_DEAD = (255, 80, 80)
COLOR_WIN = (120, 240, 120)

# Speeds (tiles per second)
PLAYER_SPEED = 5.0
TREX_SPEED_IDLE = 2.0
TREX_SPEED_CHASE = 6.0
BRACHIO_SPEED = 1.5

# Gameplay
FOG_RADIUS = 3.5            # tiles, Euclidean reveal radius (fractional ok)
FREEZE_DURATION = 2.0       # seconds T-rex + brachiosaurus stay locked
CONFUSION_DURATION = 1.2    # seconds T-rex spends "confused" after freeze or losing sight
DEATH_PAUSE = 1.2           # seconds the "Caught!" message shows
WIN_PAUSE = 1.0             # seconds the "Level complete" message shows
ANIMATION_FRAME_TIME = 0.15 # seconds between sprite-frame swaps while moving

# Maze sizing
MIN_MAZE_SIZE = 7
MAX_MAZE_SIZE = 31
MAX_LEVEL = 100
