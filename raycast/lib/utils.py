import math
from typing import NamedTuple

from raycast.lib.lib import Point

class Vector(NamedTuple):
    radians: float
    dx: float
    dy: float

def translate_point(point: Point, angle: float, distance: float) -> Point:
    x = point.x + (distance * math.cos(angle))
    y = point.y + (distance * math.sin(angle))
    return Point(x, y)

def degrees_to_vector(degrees: float) -> Vector:
    r = math.radians(degrees) % math.tau
    r = r if r >= 0 else r + math.tau
    x = math.cos(r)
    y = math.sin(r)
    return Vector(r, x, y)