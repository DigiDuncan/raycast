import math

from raycast.lib.lib import Point

def translate_point(point: Point, angle: float, distance: float) -> Point:
    x = point.x + (distance * math.cos(angle))
    y = point.y + (distance * math.sin(angle))
    return Point(x, y)