"""Growing-tree maze generator.

Defaults to Prim's-like behaviour (random cell selection) which yields plenty
of dead ends and forks — a more "maze-like" feel than the long winding
corridors typical of DFS. The exit is placed at the path cell farthest from
the start, guaranteeing a non-trivial traversal.

Invariants:
- The outer border is always wall — no way out.
- The carve produces a spanning tree, so start and exit are always connected.
"""

import random
from collections import deque

import numpy as np

from constants import MIN_MAZE_SIZE, MAX_MAZE_SIZE, MAX_LEVEL


def maze_size_for_level(level: int) -> int:
    """Return an odd grid size for the given level (1..MAX_LEVEL)."""
    level = max(1, min(MAX_LEVEL, level))
    span = MAX_MAZE_SIZE - MIN_MAZE_SIZE
    size = MIN_MAZE_SIZE + round(span * (level - 1) / (MAX_LEVEL - 1))
    if size % 2 == 0:
        size += 1
    return size


def _carve_growing_tree(grid: np.ndarray, bias: float = 0.0) -> None:
    """Carve corridors via the growing-tree algorithm.

    With probability `bias` extend from the *latest* cell (DFS-like, long
    snaking corridors); otherwise pick a *random* active cell (Prim's-like,
    lots of branches and dead ends). bias=0.0 is the most maze-like.

    Only interior odd-coordinate cells are carved, so the boundary stays
    solid wall — no escape from the maze.
    """
    size = grid.shape[0]
    grid[1, 1] = 0
    active = [(1, 1)]

    while active:
        i = len(active) - 1 if random.random() < bias else random.randrange(len(active))
        x, y = active[i]

        choices = []
        for dx, dy in ((0, 2), (2, 0), (0, -2), (-2, 0)):
            nx, ny = x + dx, y + dy
            if 1 <= nx < size - 1 and 1 <= ny < size - 1 and grid[ny, nx] == 1:
                choices.append((nx, ny, dx, dy))

        if choices:
            nx, ny, dx, dy = random.choice(choices)
            grid[y + dy // 2, x + dx // 2] = 0
            grid[ny, nx] = 0
            active.append((nx, ny))
        else:
            active.pop(i)


def _farthest_path_cell(grid: np.ndarray, start) -> tuple:
    """BFS over path cells (4-connected); return the cell with greatest distance."""
    h, w = grid.shape
    dist = {start: 0}
    q = deque([start])
    farthest = start
    while q:
        cur = q.popleft()
        cx, cy = cur
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and grid[ny, nx] == 0 and (nx, ny) not in dist:
                dist[(nx, ny)] = dist[cur] + 1
                if dist[(nx, ny)] > dist[farthest]:
                    farthest = (nx, ny)
                q.append((nx, ny))
    return farthest


def generate_maze(level: int):
    """Generate a maze for the given level.

    Returns (grid, start, exit_) where:
        grid  : np.ndarray (size, size); 0 = path, 1 = wall.
        start : (col, row) tile coordinate.
        exit_ : (col, row) tile coordinate, placed at the path cell farthest
                from start so the player must actually traverse the maze.
    """
    size = maze_size_for_level(level)
    grid = np.ones((size, size), dtype=np.int8)
    _carve_growing_tree(grid, bias=0.0)

    start = (1, 1)
    exit_ = _farthest_path_cell(grid, start)
    return grid, start, exit_
