import math
from pathlib import Path

import numpy as np

import arcade

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

    def distance_to(self, p: "Point") -> float:
        return np.linalg.norm(self - p.vector)

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
        match self.type:
            case "air":
                return None
            case "wall":
                return arcade.color_from_hex_string("#00DDDD")
            case "missingno":
                return arcade.color_from_hex_string("#FF00FF")

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

    @property
    def width(self) -> int:
        return len(self.map[0])

    @property
    def height(self) -> int:
        return len(self.map)

    @property
    def all_tiles(self) -> list[Tile]:
        return set(tile for line in self.map for tile in line)

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

    def draw(self, x = 0, y = 0):
        for r, line in enumerate(self.map):
            for n, t in enumerate(line):
                if t.id != 0:
                    arcade.draw_lrtb_rectangle_filled(n * self.scale + 1 + x, (n + 1) * self.scale - 1 + x,
                        (r + 1) * self.scale - 1 + y, r * self.scale + 1 + y,
                        t.color)

    def __str__(self) -> str:
        map = reversed(self.map)
        lines = ["".join([str(i) for i in line]) for line in map]
        map = "\n".join(lines)
        return map


class Player:
    def __init__(self, level: Level, pos: tuple[float, float], rot: float = 90.0):
        self.level = level
        self.pos = Point.from_tuple(pos)
        self.rot = rot
        self.speed = 3

        self.dx: float = 0
        self.dy: float = 0
        self.da: float = 0

        self.radius = 0.2
        self.debug = True

    @property
    def hit_radius(self) -> float:
        return self.radius * 1.5

    @property
    def radians(self) -> float:
        r = math.radians(self.rot) % math.tau
        return r if r >= 0 else r + math.tau

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

    def draw_rays(self, view_distance = 30):
        ray_angle = self.radians
        ray_x = 0
        ray_y = 0
        for i in range(1):
            dof = view_distance
            atan = -1 / math.tan(ray_angle)
            # Horizontal line check
            if ray_angle > math.pi:  # looking up
                ray_y = int(self.pos.y)
                ray_x = (self.pos.y - ray_y) * atan + self.pos.x
                y_offset = -1
                x_offset = -y_offset * atan
            elif ray_angle < math.pi:  # looking down
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
                if map_x >= 0 and map_x < self.level.width and map_y >= 0 and map_y < self.level.height:
                    if self.level.map[map_y][map_x].id != 0:
                        dof = 0
                    else:
                        ray_x += x_offset
                        ray_y += y_offset
                dof -= 1

        arcade.draw_line(self.pos.x * self.level.scale, self.pos.y * self.level.scale, ray_x * self.level.scale, ray_y * self.level.scale, arcade.color.YELLOW)
        if self.debug:
            arcade.draw_line(0, ray_y * self.level.scale, self.level.width * self.level.scale, ray_y * self.level.scale, arcade.color.MAGENTA)
            
    
    def draw(self, x: float = 0, y: float = 0):
        scaled_pos = Point(self.pos.x * self.level.scale + x, self.pos.y * self.level.scale + y)
        arcade.draw_circle_filled(scaled_pos.x, scaled_pos.y, 0.2 * self.level.scale, arcade.color.BLUE)
        self.draw_rays()
        if self.debug:
            # Direction vector
            scaled_heading = Point(self.heading_x, self.heading_y) * self.level.scale
            line_end = scaled_pos + scaled_heading
            arcade.draw_line(scaled_pos.x, scaled_pos.y, line_end.x, line_end.y, arcade.color.GREEN, 0.1 * self.level.scale)

            # Hitbox
            arcade.draw_circle_outline(scaled_pos.x, scaled_pos.y, self.hit_radius * self.level.scale, arcade.color.RED, 1)