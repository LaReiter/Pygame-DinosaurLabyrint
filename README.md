# Dinosaur Maze

A 2D top-down maze game written in Python and pygame. Navigate a pixel-art explorer through 100 increasingly difficult jungle labyrinths, avoiding carnivorous T-rexes and using brachiosauruses as temporary roadblocks.

**Author:** Lars Nørtoft Reiter
*Vibe coded with [Claude Code](https://claude.ai/code) by Anthropic.*

---

## How to Run

**Requirements:** Python 3.x (tested on 3.14), pip

```
pip install pygame-ce numpy
py main.py
```

> **Note:** The project requires `pygame-ce` (Community Edition), not standard `pygame`. Standard pygame does not support Python 3.14+.

---

## Folder Structure

```
Spil - Dinosaur Labyrint/
│
├── main.py                  # Entry point — run this
├── game.py                  # Level state, rendering, Game loop
├── entities.py              # Player, TRex, Brachiosaurus classes
├── maze.py                  # Maze generation algorithm
├── assets.py                # Asset loading and preparation
├── constants.py             # All tunable game constants
├── requirements.txt         # Python dependencies
│
├── player/                  # Player character sprites
│   ├── playerh1.png         # Horizontal walk frame 1 (mirrored for left)
│   ├── playerh2.png         # Horizontal walk frame 2
│   ├── playeru1.png         # Walk upward frame 1
│   ├── playeru2.png         # Walk upward frame 2
│   ├── playerd1.png         # Walk downward frame 1
│   └── playerd2.png         # Walk downward frame 2
│
├── trex/                    # T-rex (carnivore) sprites — same naming convention
│   ├── trexh1.png / trexh2.png
│   ├── trexu1.png / trexu2.png
│   └── trexd1.png / trexd2.png
│
├── brachiosaurus/           # Brachiosaurus (herbivore) sprites
│   ├── brachioh1.png / brachioh2.png
│   ├── brachiou1.png / brachiou2.png
│   └── brachiod1.png / brachiod2.png
│
├── environment/             # Static environment tiles
│   ├── tile.png             # Path tile (sandy ground)
│   ├── tile_with_treasure.png  # Exit tile (treasure chest on path)
│   ├── tree.png             # Tree overlay (composited onto path for wall tiles)
│   └── qmark.png            # Question mark shown above confused T-rex
│
├── original game manifest - by Lars Reiter/
│   └── readme.txt           # Original game ideas / manifest as written down by the author
```

---

## Gameplay

### Objective
Navigate from the **start tile** (top-left of the maze) to the **exit tile** (marked with a treasure chest). The exit is always placed at the farthest reachable cell from the start, so the player must genuinely traverse the maze.

### Controls
| Key | Action |
|---|---|
| Arrow keys / WASD | Move player |
| Escape | Quit |

### Fog of War
Only tiles within **3.5 tiles** (Euclidean radius) of the player are revealed. Revealed tiles stay visible permanently — the fog only hides unexplored areas.

### T-Rex (Carnivore)
T-rexes patrol the maze and will chase the player on sight.

| State | Behaviour | Speed |
|---|---|---|
| Idle | Random walk, no backtracking | 2 tiles/sec |
| Chasing | BFS pathfinding to player | 6 tiles/sec |
| Frozen | Locked in face-to-face standoff with a brachiosaurus | — |
| Confused | Cycles directions randomly; cannot see player | — |

- **Line of sight:** same row or column with no walls between T-rex and player.
- **Catching the player** restarts the current level.
- **After a freeze** (defeating a brachiosaurus), the T-rex steps onto the brachio's tile and enters a **confusion state** (1.2 s) where it spins in place and cannot detect the player.
- A **question mark** floats above a confused T-rex.

### Brachiosaurus (Herbivore)
Brachiosauruses wander randomly and act as mobile obstacles.

- The player walks through them freely — no interaction.
- When a **T-rex steps onto a brachio tile**, both entities freeze for **2 seconds** in a face-to-face standoff (animated bounce).
- After the freeze, the brachiosaurus **respawns** at a random path tile away from the player and exit. The T-rex enters confusion.

### Winning
Reach the exit tile. After a 1-second pause, the next level loads automatically.

---

## Levels and Difficulty

The game has **100 levels**. Difficulty scales on two axes:

**Maze size** (always odd-dimension grid):

| Level | Grid size |
|---|---|
| 1 | 7 × 7 |
| ~50 | ~19 × 19 |
| 100 | 31 × 31 |

**Dinosaur count** (square-root scaling):

| Level | T-rexes | Brachiosauruses |
|---|---|---|
| 1 | 1 | 1 |
| 25 | 2 | 5 |
| 100 | 5 | 10 |

---

## Maze Generation

Uses a **Prim's-like growing-tree algorithm** (`bias=0.0` = fully random active cell selection). This produces mazes with many dead ends and forks rather than the long winding corridors typical of DFS.

- Grid: `0` = path, `1` = wall. The outer border is always wall.
- Only interior odd-coordinate cells are carved, so walls form a proper grid structure.
- The exit is placed at the **BFS-farthest reachable cell** from the start, guaranteeing a non-trivial traversal distance.

---

## Technical Notes

### Display
| Setting | Value |
|---|---|
| Window | 800 × 600 px |
| Tile size | 64 × 64 px |
| Target FPS | 60 |

### Sprites
- Player and T-rex sprites are scaled to **56 × 56 px**.
- Brachiosaurus sprites are scaled to **64 × 64 px** (fills the full tile).
- Horizontal sprites face right; **mirrored horizontally** for leftward movement.
- Two animation frames per direction, swapped every 0.15 s while moving.

### Wall Tiles
Wall tiles are **composited at load time**: the path tile (`tile.png`) is drawn first, then the tree PNG is blended on top. This makes the ground texture read continuously between walls and paths.

### Camera
The camera follows the player and clamps to maze boundaries. Mazes smaller than the window are centered.

---

## Dependencies

| Package | Purpose |
|---|---|
| `pygame-ce` | Rendering, input, animation loop |
| `numpy` | Maze grid (2D int8 array) |

Install with:
```
pip install pygame-ce numpy
```
