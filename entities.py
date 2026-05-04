"""Player and dinosaur entities. Movement is grid-locked but smoothly interpolated.

State precedence for the T-rex:  frozen > confused > chasing > idle.
- frozen   : engaged with a brachiosaurus (FREEZE_DURATION).
- confused : just unfroze, OR just lost line of sight to the player
             (CONFUSION_DURATION). Cycles facing direction; cannot see the player.
- chasing  : has straight-corridor line of sight to the player.
- idle     : random walk through path tiles.
"""

import math
import random
from collections import deque

from constants import (PLAYER_SPEED, TREX_SPEED_IDLE, TREX_SPEED_CHASE,
                       BRACHIO_SPEED, FREEZE_DURATION, CONFUSION_DURATION,
                       ANIMATION_FRAME_TIME)


class Entity:
    """Snaps between grid cells, with float interpolation between snaps."""

    def __init__(self, gx: int, gy: int):
        self.x = float(gx)
        self.y = float(gy)
        self.tx = gx        # target tile (col)
        self.ty = gy        # target tile (row)
        self.facing = 'down'
        self.frame_index = 0
        self._frame_timer = 0.0
        self.moving = False
        self._engage_dir = None     # (dx, dy) toward partner during freeze
        self._engage_start = 0.0    # time freeze began

    @property
    def grid_pos(self):
        return (round(self.x), round(self.y))

    @property
    def at_target(self) -> bool:
        return abs(self.x - self.tx) < 1e-6 and abs(self.y - self.ty) < 1e-6

    def set_target(self, tx: int, ty: int) -> None:
        self.tx = tx
        self.ty = ty
        if tx > round(self.x):   self.facing = 'right'
        elif tx < round(self.x): self.facing = 'left'
        elif ty > round(self.y): self.facing = 'down'
        elif ty < round(self.y): self.facing = 'up'
        self.moving = True

    def face_toward(self, tx: int, ty: int) -> None:
        """Turn (without moving) toward the given grid tile."""
        cx, cy = self.tx, self.ty
        if   tx > cx: self.facing = 'right'
        elif tx < cx: self.facing = 'left'
        elif ty > cy: self.facing = 'down'
        elif ty < cy: self.facing = 'up'
        self.moving = False

    def begin_engage(self, now: float, toward) -> None:
        """Snap to tile center and prepare the head-to-head bounce loop."""
        ox, oy = toward
        self._engage_dir = (ox - self.tx, oy - self.ty)
        self._engage_start = now
        self.x = float(self.tx)
        self.y = float(self.ty)
        self.moving = False

    def end_engage(self) -> None:
        """Drop engagement state and snap back to the tile center."""
        self._engage_dir = None
        self.x = float(self.tx)
        self.y = float(self.ty)

    def tick_engage_bounce(self, now: float) -> None:
        """While locked, oscillate position toward and away from the partner."""
        if self._engage_dir is None:
            return
        elapsed = now - self._engage_start
        phase = 2 * math.pi * _ENGAGE_FREQ * elapsed
        nudge = _ENGAGE_NUDGE_MAX * (1 - math.cos(phase)) / 2
        dx, dy = self._engage_dir
        self.x = self.tx + dx * nudge
        self.y = self.ty + dy * nudge

    def step_toward_target(self, speed: float, dt: float) -> bool:
        """Move toward the current target. Return True if we arrived this frame."""
        dx = self.tx - self.x
        dy = self.ty - self.y
        dist = math.hypot(dx, dy)
        if dist == 0.0:
            self.moving = False
            return True
        step = speed * dt
        if step >= dist:
            self.x = float(self.tx)
            self.y = float(self.ty)
            self.moving = False
            return True
        self.x += dx / dist * step
        self.y += dy / dist * step
        self._frame_timer += dt
        if self._frame_timer >= ANIMATION_FRAME_TIME:
            self._frame_timer = 0.0
            self.frame_index = 1 - self.frame_index
        return False


_ENGAGE_NUDGE_MAX = 0.30  # peak fraction of a tile each entity lunges toward partner
_ENGAGE_FREQ = 3.5        # collisions per second during the locked freeze


def _path_neighbors(maze, x, y):
    h, w = maze.shape
    out = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h and maze[ny, nx] == 0:
            out.append((nx, ny))
    return out


class Player(Entity):
    def update(self, dt, maze, input_dir):
        if self.at_target and input_dir is not None:
            dx, dy = input_dir
            nx, ny = self.tx + dx, self.ty + dy
            h, w = maze.shape
            if 0 <= nx < w and 0 <= ny < h and maze[ny, nx] == 0:
                self.set_target(nx, ny)
        if not self.at_target:
            self.step_toward_target(PLAYER_SPEED, dt)


_CONFUSION_DIRS = ('left', 'up', 'right', 'down')


class TRex(Entity):
    def __init__(self, gx, gy):
        super().__init__(gx, gy)
        self.chasing = False
        self.frozen_until = 0.0
        self.confused_until = 0.0
        self._confusion_start = 0.0
        self._confusion_dirs = _CONFUSION_DIRS
        self._was_frozen = False
        self._engagement_tile = None  # remembered so we can step onto it post-fight
        self.last_pos = None

    def is_frozen(self, now):  return now < self.frozen_until
    def is_confused(self, now): return now < self.confused_until

    def freeze(self, now, toward=None):
        self.frozen_until = now + FREEZE_DURATION
        self.moving = False
        if toward is not None:
            self.begin_engage(now, toward)
            self._engagement_tile = tuple(toward)

    def _enter_confusion(self, now):
        self.confused_until = now + CONFUSION_DURATION
        self._confusion_start = now
        self.chasing = False
        dirs = list(_CONFUSION_DIRS)
        random.shuffle(dirs)
        self._confusion_dirs = tuple(dirs)
        self.moving = False

    def _tick_confusion(self, now):
        elapsed = now - self._confusion_start
        slot = CONFUSION_DURATION / 4
        idx = min(3, int(elapsed / slot))
        self.facing = self._confusion_dirs[idx]
        self.moving = False

    def update(self, dt, maze, player, brachios, now):
        currently_frozen = self.is_frozen(now)
        if self._was_frozen and not currently_frozen:
            # Defeated a brachiosaurus → step onto its tile, then become confused.
            self.end_engage()
            if self._engagement_tile is not None:
                ex, ey = self._engagement_tile
                self.tx, self.ty = ex, ey
                self.x, self.y = float(ex), float(ey)
                self.last_pos = None
                self._engagement_tile = None
            self._enter_confusion(now)
        self._was_frozen = currently_frozen
        if currently_frozen:
            self.tick_engage_bounce(now)
            return

        if self.is_confused(now):
            self._tick_confusion(now)
            return

        if self.at_target:
            was_chasing = self.chasing
            self.chasing = self._has_line_of_sight(maze, player)
            if was_chasing and not self.chasing:
                # Lost sight of the player → become confused.
                self._enter_confusion(now)
                return

            next_tile = None
            if self.chasing:
                next_tile = self._bfs_first_step(maze, (self.tx, self.ty), player.grid_pos)
            if next_tile is None:
                next_tile = self._random_step(maze)

            if next_tile is not None:
                blocking = next((b for b in brachios
                                 if (b.tx, b.ty) == next_tile and not b.is_frozen(now)),
                                None)
                if blocking is not None:
                    self.face_toward(*next_tile)
                    blocking.face_toward(self.tx, self.ty)
                    self.freeze(now, toward=(blocking.tx, blocking.ty))
                    blocking.freeze(now, toward=(self.tx, self.ty))
                    return
                self.last_pos = (self.tx, self.ty)
                self.set_target(*next_tile)

        speed = TREX_SPEED_CHASE if self.chasing else TREX_SPEED_IDLE
        self.step_toward_target(speed, dt)

    def _has_line_of_sight(self, maze, player):
        px, py = player.grid_pos
        tx, ty = self.tx, self.ty
        if (px, py) == (tx, ty):
            return True
        if px == tx:
            ymin, ymax = sorted([ty, py])
            for y in range(ymin + 1, ymax):
                if maze[y, tx] == 1:
                    return False
            return True
        if py == ty:
            xmin, xmax = sorted([tx, px])
            for x in range(xmin + 1, xmax):
                if maze[ty, x] == 1:
                    return False
            return True
        return False

    def _random_step(self, maze):
        candidates = _path_neighbors(maze, self.tx, self.ty)
        if not candidates:
            return None
        if self.last_pos and len(candidates) > 1 and self.last_pos in candidates:
            candidates.remove(self.last_pos)
        return random.choice(candidates)

    @staticmethod
    def _bfs_first_step(maze, start, goal):
        if start == goal:
            return None
        h, w = maze.shape
        parents = {start: None}
        q = deque([start])
        while q:
            cur = q.popleft()
            if cur == goal:
                step = cur
                while parents[step] is not None and parents[step] != start:
                    step = parents[step]
                return step if parents[step] == start else None
            x, y = cur
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and maze[ny, nx] == 0 and (nx, ny) not in parents:
                    parents[(nx, ny)] = cur
                    q.append((nx, ny))
        return None


class Brachiosaurus(Entity):
    def __init__(self, gx, gy):
        super().__init__(gx, gy)
        self.frozen_until = 0.0
        self.last_pos = None

    def is_frozen(self, now):
        return now < self.frozen_until

    def freeze(self, now, toward=None):
        self.frozen_until = now + FREEZE_DURATION
        self.moving = False
        if toward is not None:
            self.begin_engage(now, toward)

    def update(self, dt, maze, trexes, now):
        if self.is_frozen(now):
            self.tick_engage_bounce(now)
            return
        if self.at_target:
            candidates = _path_neighbors(maze, self.tx, self.ty)
            if candidates:
                if self.last_pos and len(candidates) > 1 and self.last_pos in candidates:
                    candidates.remove(self.last_pos)
                next_tile = random.choice(candidates)
                # Symmetric collision: about to step on a T-rex → engage and freeze.
                blocking = next((t for t in trexes
                                 if (t.tx, t.ty) == next_tile and not t.is_frozen(now)),
                                None)
                if blocking is not None:
                    self.face_toward(*next_tile)
                    blocking.face_toward(self.tx, self.ty)
                    self.freeze(now, toward=(blocking.tx, blocking.ty))
                    blocking.freeze(now, toward=(self.tx, self.ty))
                    return
                self.last_pos = (self.tx, self.ty)
                self.set_target(*next_tile)
        if not self.at_target:
            self.step_toward_target(BRACHIO_SPEED, dt)

    def respawn(self, gx, gy):
        self.x = float(gx)
        self.y = float(gy)
        self.tx = gx
        self.ty = gy
        self.last_pos = None
        self.moving = False
        self.frame_index = 0
        self._engage_dir = None
