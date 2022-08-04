from copy import copy
import math
from pathlib import Path

import arcade

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    @classmethod
    def from_tuple(self, t: tuple[float, float]):
        return Point(t[0], t[1])

    def distance_to(self, point: "Point") -> float:
        return math.dist((self.x, self.y), (point.x, point.y))


class Tile:
    def __init__(self, level: "Level", id: int, x: float, y: float):
        self.id = int(id)
        self.ix = x
        self.iy = y
        self.level = level

    @property
    def x(self) -> float:
        return self.ix * self.level.scale

    @property
    def y(self) -> float:
        return self.iy * self.level.scale

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
                return arcade.color_from_hex_string("00DDDD")
            case "missingno":
                return arcade.color_from_hex_string("FF00FF")

    def point_collides(self, point: Point) -> bool:
        return self.x <= point.x <= self.x + self.level.scale and self.y <= point.y <= self.y + self.level.scale

    def __str__(self) -> str:
        return f"[{self.id}]"


class Level:
    def __init__(self, x: float = 0.0, y: float = 0.0, scale: float = 20):
        self.map: list[list[Tile]] = []
        self.x = x
        self.y = y
        self.scale = scale

    @property
    def width(self) -> int:
        return len(map[0])

    @property
    def height(self) -> int:
        return len(map)

    @property
    def all_tiles(self) -> list[Tile]:
        return [tile for line in self.map for tile in line]

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

    def get_scaled_position(self, point: Point):
        return Point(point.x * self.scale, point.y * self.scale)

    def check_all_tiles_for_collision(self, point: Point) -> Tile | None:
        """WARNING: Super inefficent what the frick"""
        for tile in self.all_tiles:
            if tile.point_collides(point) and tile.id != 0:
                return tile
        return None


    def __str__(self) -> str:
        map = reversed(self.map)
        lines = ["".join([str(i) for i in line]) for line in map]
        map = "\n".join(lines)
        return map


class Player:
    def __init__(self, level: Level, pos: tuple[float, float], rot: float = 0.0):
        self.level = level
        self.pos = Point.from_tuple(pos)
        self.rot = rot

    @property
    def radians(self) -> float:
        return math.radians(self.rot)

    def cast_ray(self, angle: float = 0.0, view_distance: int = 600) -> tuple[Tile, float] | None:
        """Returns (Tile, distance)"""
        r = (math.radians(angle) + self.rot) % math.tau - math.pi
        heading_x = math.cos(r)
        heading_y = math.sin(r)

        current_point = copy(self.pos)
        current_x = None
        current_x_dist = None
        current_y = None
        current_y_dist = None
        for i in range(view_distance):
            # Horizontal check
            cphx = current_point
            cphx.x += heading_x
            if t := self.level.check_all_tiles_for_collision(cphx):
                current_x = t
                current_x_dist = self.pos.distance_to(cphx)
            # Vertical check
            cphy = current_point
            cphy.y += heading_y
            if t := self.level.check_all_tiles_for_collision(cphy):
                current_y = t
                current_y_dist = self.pos.distance_to(cphy)
            # Return tile if we found it
            if current_x and current_y:
                if current_x_dist < current_y_dist:
                    return (current_x, current_x_dist)
                else:
                    return (current_y, current_y_dist)
            elif current_x:
                return (current_x, current_x_dist)
            elif current_y:
                return (current_y, current_y_dist)
            else:
                current_point.x += heading_x
                current_point.y += heading_y
        return None