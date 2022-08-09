import math
from typing import NamedTuple

Color = tuple[int, int, int]
Light = tuple[float, float, float]

class Vector(NamedTuple):
    radians: float
    dx: float
    dy: float

def clamp(n, x, m):
    return max(n, min(x, m))

def degrees_to_vector(degrees: float) -> Vector:
    r = math.radians(degrees) % math.tau
    r = r if r >= 0 else r + math.tau
    x = math.cos(r)
    y = math.sin(r)
    return Vector(r, x, y)

def light_color(color: Color, light: Light) -> Color:
    r = clamp(0, color[0] * light[0], 255)
    g = clamp(0, color[1] * light[1], 255)
    b = clamp(0, color[2] * light[2], 255)
    return (r, g, b)

def adjust_light(light: Light, amplitude: float, max: Light = None) -> Light:
    new_light = (light[0] * amplitude, light[1] * amplitude, light[2] * amplitude)
    if max:
        new_light = (min(max[0], new_light[0]), min(max[1], new_light[1]), min(max[2], new_light[2]))
    return new_light