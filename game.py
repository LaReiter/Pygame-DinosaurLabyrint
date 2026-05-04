"""Level state, rendering, and the top-level Game loop."""

import math
import random
import pygame
import numpy as np

from constants import (WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TILE_SIZE,
                       FOG_RADIUS, DEATH_PAUSE, WIN_PAUSE, MAX_LEVEL,
                       COLOR_BG, COLOR_FOG, COLOR_HUD, COLOR_DEAD, COLOR_WIN)
from maze import generate_maze
from entities import Player, TRex, Brachiosaurus
from assets import Assets


class Level:
    def __init__(self, level_num: int, assets: Assets):
        self.level_num = level_num
        self.assets = assets
        self.maze, start, self.exit_pos = generate_maze(level_num)
        self.player = Player(*start)
        self.player.facing = 'down'

        self.trexes = []
        self.brachios = []
        self._spawn_dinosaurs(level_num)

        self.maze_surface = self._build_maze_surface()
        h, w = self.maze.shape
        self.revealed = np.zeros((h, w), dtype=bool)
        self._reveal_around(self.player.grid_pos)

        self.dead = False
        self.dead_timer = 0.0
        self.won = False
        self.win_timer = 0.0

    # ----- spawning ------------------------------------------------------ #

    def _spawn_dinosaurs(self, level_num: int) -> None:
        # Sub-linear scaling: 1 of each at level 1, ~5 T-rex / 10 brachios at level 100.
        brachio_count = max(1, int(math.sqrt(level_num)))
        trex_count    = max(1, int(math.sqrt(level_num) / 2))
        h, w = self.maze.shape
        sx, sy = self.player.grid_pos
        ex, ey = self.exit_pos

        far = [(x, y) for y in range(h) for x in range(w)
               if self.maze[y, x] == 0
               and (x, y) != (ex, ey)
               and abs(x - sx) + abs(y - sy) > 4]
        if len(far) < trex_count + brachio_count:
            far = [(x, y) for y in range(h) for x in range(w)
                   if self.maze[y, x] == 0 and (x, y) != (sx, sy)
                   and (x, y) != (ex, ey)]
        random.shuffle(far)
        for _ in range(trex_count):
            if not far: break
            x, y = far.pop()
            self.trexes.append(TRex(x, y))
        for _ in range(brachio_count):
            if not far: break
            x, y = far.pop()
            self.brachios.append(Brachiosaurus(x, y))

    def _respawn_brachio(self, brachio: Brachiosaurus) -> None:
        h, w = self.maze.shape
        px, py = self.player.grid_pos
        for _ in range(80):
            x = random.randrange(w)
            y = random.randrange(h)
            if self.maze[y, x] != 0:
                continue
            if (x, y) == self.exit_pos:
                continue
            if abs(x - px) + abs(y - py) <= 3:
                continue
            if any(t.grid_pos == (x, y) for t in self.trexes):
                continue
            if any(b is not brachio and b.grid_pos == (x, y) for b in self.brachios):
                continue
            brachio.respawn(x, y)
            return

    # ----- maze surface (pre-rendered) ----------------------------------- #

    def _build_maze_surface(self) -> pygame.Surface:
        h, w = self.maze.shape
        surf = pygame.Surface((w * TILE_SIZE, h * TILE_SIZE))
        ex, ey = self.exit_pos
        for y in range(h):
            for x in range(w):
                if self.maze[y, x] == 0:
                    tile = self.assets.treasure if (x, y) == (ex, ey) else self.assets.path
                else:
                    tile = self.assets.wall
                surf.blit(tile, (x * TILE_SIZE, y * TILE_SIZE))
        return surf

    # ----- fog of war ---------------------------------------------------- #

    def _reveal_around(self, center) -> None:
        cx, cy = center
        h, w = self.maze.shape
        r_int = int(math.ceil(FOG_RADIUS))
        rsq = FOG_RADIUS * FOG_RADIUS
        for y in range(max(0, cy - r_int), min(h, cy + r_int + 1)):
            for x in range(max(0, cx - r_int), min(w, cx + r_int + 1)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= rsq:
                    self.revealed[y, x] = True

    # ----- update -------------------------------------------------------- #

    def update(self, dt: float, input_dir, now: float) -> None:
        if self.won:
            self.win_timer += dt
            return
        if self.dead:
            self.dead_timer += dt
            return

        # Respawn brachiosauruses whose freeze just expired BEFORE T-rex picks its
        # next move, so T-rex cannot immediately refreeze a brachio at the old spot.
        for b in self.brachios:
            was_frozen = getattr(b, '_was_frozen', False)
            currently_frozen = b.is_frozen(now)
            if was_frozen and not currently_frozen:
                self._respawn_brachio(b)
            b._was_frozen = currently_frozen

        prev_grid = self.player.grid_pos
        self.player.update(dt, self.maze, input_dir)
        if self.player.grid_pos != prev_grid:
            self._reveal_around(self.player.grid_pos)

        for trex in self.trexes:
            trex.update(dt, self.maze, self.player, self.brachios, now)

        for b in self.brachios:
            b.update(dt, self.maze, self.trexes, now)

        if self.player.grid_pos == self.exit_pos and self.player.at_target:
            self.won = True
            self.win_timer = 0.0
            return

        for trex in self.trexes:
            if trex.is_frozen(now):
                continue
            dx = trex.x - self.player.x
            dy = trex.y - self.player.y
            if dx * dx + dy * dy < 0.35 ** 2:
                self.dead = True
                self.dead_timer = 0.0
                return

    # ----- draw ---------------------------------------------------------- #

    def _camera(self):
        h, w = self.maze.shape
        maze_w = w * TILE_SIZE
        maze_h = h * TILE_SIZE
        if maze_w <= WINDOW_WIDTH:
            cam_x = -(WINDOW_WIDTH - maze_w) // 2
        else:
            cam_x = self.player.x * TILE_SIZE - WINDOW_WIDTH // 2 + TILE_SIZE // 2
            cam_x = max(0, min(cam_x, maze_w - WINDOW_WIDTH))
        if maze_h <= WINDOW_HEIGHT:
            cam_y = -(WINDOW_HEIGHT - maze_h) // 2
        else:
            cam_y = self.player.y * TILE_SIZE - WINDOW_HEIGHT // 2 + TILE_SIZE // 2
            cam_y = max(0, min(cam_y, maze_h - WINDOW_HEIGHT))
        return cam_x, cam_y

    def draw(self, screen, font, big_font, now: float) -> None:
        screen.fill(COLOR_BG)
        cam_x, cam_y = self._camera()
        screen.blit(self.maze_surface, (-cam_x, -cam_y))

        def draw_entity(e, frames):
            if not self.revealed[round(e.y), round(e.x)]:
                return
            sprite = frames[e.facing][e.frame_index if e.moving else 0]
            sw, sh = sprite.get_size()
            sx = e.x * TILE_SIZE - cam_x + (TILE_SIZE - sw) // 2
            sy = e.y * TILE_SIZE - cam_y + (TILE_SIZE - sh) // 2
            screen.blit(sprite, (sx, sy))

        for b in self.brachios:
            draw_entity(b, self.assets.brachio_frames)
        for t in self.trexes:
            draw_entity(t, self.assets.trex_frames)
            if t.is_confused(now) and self.revealed[round(t.y), round(t.x)]:
                qm = self.assets.question_mark
                qx = t.x * TILE_SIZE - cam_x + (TILE_SIZE - qm.get_width()) // 2
                qy = t.y * TILE_SIZE - cam_y - qm.get_height() - 4
                screen.blit(qm, (qx, qy))
        draw_entity(self.player, self.assets.player_frames)

        # Fog over unrevealed visible tiles.
        h, w = self.maze.shape
        x0 = max(0, int(cam_x // TILE_SIZE))
        y0 = max(0, int(cam_y // TILE_SIZE))
        x1 = min(w, int((cam_x + WINDOW_WIDTH) // TILE_SIZE) + 1)
        y1 = min(h, int((cam_y + WINDOW_HEIGHT) // TILE_SIZE) + 1)
        for y in range(y0, y1):
            for x in range(x0, x1):
                if not self.revealed[y, x]:
                    pygame.draw.rect(
                        screen, COLOR_FOG,
                        (x * TILE_SIZE - cam_x, y * TILE_SIZE - cam_y,
                         TILE_SIZE, TILE_SIZE))

        hud = font.render(
            f"Level {self.level_num}   T-rex: {len(self.trexes)}",
            True, COLOR_HUD)
        screen.blit(hud, (10, 10))

        if self.dead:
            msg = big_font.render("Eaten by a hungry T-rex. Restarting...", True, COLOR_DEAD)
            screen.blit(msg, msg.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))
        elif self.won:
            msg = big_font.render("Level Complete!", True, COLOR_WIN)
            screen.blit(msg, msg.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Dinosaur Maze")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)
        self.big_font = pygame.font.SysFont(None, 56)
        self.assets = Assets()
        self.level_num = 1
        self.now = 0.0
        self.level = Level(self.level_num, self.assets)
        self.game_complete = False

    def _input_dir(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:    return (0, -1)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:  return (0, 1)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  return (-1, 0)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: return (1, 0)
        return None

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self.now += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            if not self.game_complete:
                self.level.update(dt, self._input_dir(), self.now)

                if self.level.won and self.level.win_timer >= WIN_PAUSE:
                    if self.level_num >= MAX_LEVEL:
                        self.game_complete = True
                    else:
                        self.level_num += 1
                        self.level = Level(self.level_num, self.assets)
                elif self.level.dead and self.level.dead_timer >= DEATH_PAUSE:
                    self.level = Level(self.level_num, self.assets)

            self.level.draw(self.screen, self.font, self.big_font, self.now)
            if self.game_complete:
                msg = self.big_font.render("You completed all 100 levels!",
                                           True, COLOR_WIN)
                self.screen.blit(msg, msg.get_rect(
                    center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))

            pygame.display.flip()

        pygame.quit()
