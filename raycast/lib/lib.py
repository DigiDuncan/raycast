import math
from pathlib import Path
from typing import NamedTuple

import numpy as np

import arcade

from raycast.lib.utils import degrees_to_radians, light_color

INFINITY = float('inf')
PI_HALVES = math.pi / 2
THREEPI_ON_TWO = 3 * math.pi / 2

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    @property
    def vector(self) -> np.ndarray[float, float]:
        return np.array([self.x, self.y])

    @classmethod
    def from_tuple(self, t: tuple[float, float]):
        return Point(t[0], t[1])

    def translated(self, angle: float, distance: float) -> "Point":
        x = self.x + (distance * math.cos(angle))
        y = self.y + (distance * math.sin(angle))
        return Point(x, y)

    def distance_to(self, p: "Point") -> float:
        return np.linalg.norm(self.vector - p.vector)

    def __add__(self, p: "Point") -> "Point":
        return Point(self.x + p.x, self.y + p.y)

    def __iadd__(self, p: "Point"):
        self.x += p.x
        self.y += p.y

    def __mul__(self, s: float) -> "Point":
        return Point(self.x * s, self.y * s)

    def __imul__(self, s: float):
        self.x *= s
        self.y *= s


class Tile:
    def __init__(self, level: "Level", id: int, x: float, y: float):
        self.id = int(id)
        self.ix = x
        self.iy = y
        self.level = level
        self.light: tuple[float, float, float] = (1, 1, 1)

    @property
    def x(self) -> float:
        return self.ix

    @property
    def y(self) -> float:
        return self.iy

    @property
    def type(self) -> str:
        match self.id:
            case 0:
                return "air"
            case 1:
                return "wall"
            case _:
                return "missingno"

    @property
    def color(self) -> arcade.RGBA | None:
        c = None
        match self.type:
            case "air":
                return None
            case "wall":
                c = arcade.color_from_hex_string("#DD0000")
            case "missingno":
                c = arcade.color_from_hex_string("#FF00FF")
        if c:
            c = light_color(c, self.light)
        return c

    def point_collides(self, point: Point) -> bool:
        return (self.x <= point.x <= self.x + 1) and (self.y <= point.y <= self.y + 1)

    def __str__(self) -> str:
        return f"[{self.id}]"


class Level:
    def __init__(self, x: float = 0.0, y: float = 0.0, scale: float = 20):
        self.map: list[list[Tile]] = []
        self.x = x
        self.y = y
        self.scale = scale
        self.debug = True
        self.smooth = False
        self.player: Player = None

        self.texture_2D = arcade.Texture.create_empty("twod", size=(600, 600))
        self.sprite_2D = arcade.Sprite(center_x=300, center_y=300, texture=self.texture_2D)
        self.spritelist_2D = arcade.SpriteList()
        self.spritelist_2D.append(self.sprite_2D)

    @property
    def width(self) -> int:
        return len(self.map[0])

    @property
    def height(self) -> int:
        return len(self.map)

    @property
    def all_tiles(self) -> list[Tile]:
        return set(tile for line in self.map for tile in line)

    def set_all_brightness(self, light: tuple[float, float, float]):
        for t in self.all_tiles:
            t.light = light

    @classmethod
    def from_lvl(cls, path: Path):
        level = Level()
        with open(path) as f:
            lines = reversed(f.readlines())
            ll = []
            for y, line in enumerate(lines):
                l = []
                for x, t in enumerate(line.strip()):
                    l.append(Tile(level, t, x, y))
                ll.append(l)
        level.map = ll
        return level

    def draw_2D(self, x = 0, y = 0):
        with self.spritelist_2D.atlas.render_into(self.texture_2D) as framebuffer:
            framebuffer.clear()
            for r, line in enumerate(self.map):
                for n, t in enumerate(line):
                    if t.id != 0:
                        arcade.draw_lrtb_rectangle_filled(n * self.scale + 1 + x, (n + 1) * self.scale - 1 + x,
                            (r + 1) * self.scale - 1 + y, r * self.scale + 1 + y,
                            t.color)

    def draw(self, x = 0, y = 0):
        self.draw_2D(x, y)
        self.spritelist_2D.draw()
        self.player.draw_2D()

    def __str__(self) -> str:
        map = reversed(self.map)
        lines = ["".join([str(i) for i in line]) for line in map]
        map = "\n".join(lines)
        return map

class RayInfo(NamedTuple):
    angle: float
    point: Point
    distance: float
    tile: Tile | None
    side: int


class Player:
    def __init__(self, level: Level, pos: tuple[float, float], rot: float = 90.0):
        self.level = level
        self.pos = Point.from_tuple(pos)
        self.rot = rot
        self.speed = 3

        self.dx: float = 0
        self.dy: float = 0
        self.da: float = 0

        self.texture_3D = arcade.Texture.create_empty("threed", size=(600, 600))
        self.sprite_3D = arcade.Sprite(center_x=900, center_y=300, texture=self.texture_3D)
        self.spritelist_3D = arcade.SpriteList()
        self.spritelist_3D.append(self.sprite_3D)

        self.radius = 0.2
        self.view_distance = 30
        self.fov = 90.0
        self.look = 0
        self.debug = False

    @property
    def hit_radius(self) -> float:
        return self.radius * 1.5

    @property
    def radians(self) -> float:
        return degrees_to_radians(self.rot)

    @property
    def heading_x(self) -> float:
        return math.cos(self.radians)

    @property
    def heading_y(self) -> float:
        return math.sin(self.radians)

    def update(self, delta_time: float = 1/60):
        self.pos.x += (self.dx * self.speed * delta_time)
        self.pos.y += (self.dy * self.speed * delta_time)
        self.rot += (self.da * self.speed * delta_time)

        self.dx = 0
        self.dy = 0
        self.da = 0

    def cast_ray(self, angle = 0, view_distance = 30) -> RayInfo:
        """Cast a ray forward at `angle` degrees offset from the player's rotation.
        Returns a tuple where the first element is a Point where the ray stopped,
        and the second element is the Tile is collided with, or None.
        Uses the DDA algorithm I barely understand.

        * `angle: float = 0.0`: the angle offset in degrees from the player to cast the
        ray from
        * `view_distance: int = 30`: how far to cast the ray before we give up on it
        hitting anything
        """
        ray_angle = degrees_to_radians(self.rot + angle)
        ray_x = 0
        ray_y = 0
        atan = -1 / math.tan(ray_angle) or INFINITY
        ntan = -math.tan(ray_angle)

        h_tile = None
        v_tile = None

        # Horizontal line check
        dof = view_distance
        if ray_angle > math.pi:                     # looking up
            ray_y = int(self.pos.y)
            ray_x = (self.pos.y - ray_y) * atan + self.pos.x
            y_offset = -1
            x_offset = -y_offset * atan
        else:                                       # looking down
            ray_y = int(self.pos.y) + 1
            ray_x = (self.pos.y - ray_y) * atan + self.pos.x
            y_offset = 1
            x_offset = -y_offset * atan
        if ray_angle == 0 or ray_angle == math.pi:  # looking straight
            ray_x = int(self.pos.x)
            ray_y = int(self.pos.y)

        while dof > 0:
            map_x = int(ray_x)
            map_y = int(ray_y)
            if ray_angle > math.pi:                 #looking down
                map_y = int(ray_y - 1)
            if map_x >= 0 and map_x < self.level.width and map_y >= 0 and map_y < self.level.height:
                if self.level.map[map_y][map_x].id != 0:
                    dof = 0
                    h_tile = self.level.map[map_y][map_x]
                else:
                    ray_x += x_offset
                    ray_y += y_offset
            dof -= 1

        hx = ray_x
        hy = ray_y
        h = Point(hx, hy)
        if self.debug:
            arcade.draw_line(self.pos.x * self.level.scale, self.pos.y * self.level.scale, ray_x * self.level.scale, ray_y * self.level.scale, arcade.color.BLUE)

        # Vertical line check
        dof = view_distance
        if THREEPI_ON_TWO > ray_angle > PI_HALVES:      # looking left
            ray_x = int(self.pos.x)
            ray_y = (self.pos.x - ray_x) * ntan + self.pos.y
            x_offset = -1
            y_offset = -x_offset * ntan
        else:                                           # looking right
            ray_x = int(self.pos.x) + 1
            ray_y = (self.pos.x - ray_x) * ntan + self.pos.y
            x_offset = 1
            y_offset = -x_offset * ntan
        if ray_angle == 0 or ray_angle == math.pi:      # looking straight
            ray_x = int(self.pos.x)
            ray_y = int(self.pos.y)

        while dof > 0:
            map_x = int(ray_x)
            map_y = int(ray_y)
            if THREEPI_ON_TWO > ray_angle > PI_HALVES:  # looking left
                map_x = int(ray_x - 1)
            if map_x >= 0 and map_x < self.level.width and map_y >= 0 and map_y < self.level.height:
                if self.level.map[map_y][map_x].id != 0:
                    dof = 0
                    v_tile = self.level.map[map_y][map_x]
                else:
                    ray_x += x_offset
                    ray_y += y_offset
            dof -= 1

        vx = ray_x
        vy = ray_y
        v = Point(vx, vy)
        if self.debug:
            arcade.draw_line(self.pos.x * self.level.scale, self.pos.y * self.level.scale, ray_x * self.level.scale, ray_y * self.level.scale, arcade.color.PURPLE)

        hd = self.pos.distance_to(h)
        vd = self.pos.distance_to(v)

        if hd > vd:
            if v_tile:
                v_tile.light = (1, 1, 1)
            return RayInfo(angle, v, vd, v_tile, 0)
        else:
            if h_tile:
                h_tile.light = (1, 1, 1)
            return RayInfo(angle, h, hd, h_tile, 1)

    def get_rays(self, rays = 1, fov = 90) -> list[RayInfo]:
        infos = []
        half_fov = fov / 2
        for a in np.linspace(-half_fov, half_fov, rays) if rays > 1 else [(0, 0)]:
            info = self.cast_ray(a, self.view_distance)
            infos.append(info)
        return infos

    def draw_rays(self, rays = 1, fov = 90):
        for i, info in enumerate(self.get_rays(rays, fov)):
            p = info.point * self.level.scale
            if self.debug:
                arcade.draw_line(self.pos.x * self.level.scale, self.pos.y * self.level.scale, p.x, p.y, arcade.color.LIME_GREEN)
            elif i == 0 or i == rays - 1:
                # Only draw the outermost rays in non-debug views
                arcade.draw_line(self.pos.x * self.level.scale, self.pos.y * self.level.scale, p.x, p.y, arcade.color.WHITE)

    def draw_2D(self, x: float = 0, y: float = 0):
        with self.level.spritelist_2D.atlas.render_into(self.level.texture_2D) as framebuffer:
            # Where is the player on the scaled map?
            scaled_pos = Point(self.pos.x * self.level.scale + x, self.pos.y * self.level.scale + y)
            arcade.draw_circle_filled(scaled_pos.x, scaled_pos.y, 0.2 * self.level.scale, arcade.color.BLUE)

            # Draw rays
            self.draw_rays(300, self.fov)

            # Debug info
            if self.debug:
                # Direction vector
                scaled_heading = Point(self.heading_x, self.heading_y) * self.level.scale
                line_end = scaled_pos + scaled_heading
                arcade.draw_line(scaled_pos.x, scaled_pos.y, line_end.x, line_end.y, arcade.color.GREEN, 0.1 * self.level.scale)

                # Hitbox
                arcade.draw_circle_outline(scaled_pos.x, scaled_pos.y, self.hit_radius * self.level.scale, arcade.color.RED, 1)

    def draw_3D(self, x: float = 0, y: float = 0):
        self.sprite_3D.left = x
        self.sprite_3D.bottom = y
        rays = self.get_rays(600, self.fov)
        with self.spritelist_3D.atlas.render_into(self.texture_3D) as framebuffer:
            framebuffer.clear()
            # Horizon
            arcade.draw_lrtb_rectangle_filled(0, 600, 600, 0, arcade.color.SKY_BLUE)
            arcade.draw_lrtb_rectangle_filled(0, 600, max(0, 300 - self.look), 0, arcade.color.MOSS_GREEN)
            for i, info in enumerate(rays):
                d = info.distance * math.cos(degrees_to_radians(info.angle))
                height = arcade.get_window().height / d
                color = info.tile.color if info.side == 0 else light_color(info.tile.color, (0.75, 0.75, 0.75))
                center_screen = arcade.get_window().height / 2 - self.look
                bottom = center_screen - (height / 2)
                top = center_screen + (height / 2)
                arcade.draw_lrtb_rectangle_filled(i, i + 1, top, bottom, color)
        self.spritelist_3D.draw()