import arcade
from arcade import View, Section

from raycast.lib.lib import Level, Player
from raycast.lib.utils import translate_point


class Game2DSection(Section):
    def __init__(self, level: Level, player: Player):
        super().__init__(0, 0, 600, 600, name = "Game2D")
        self.level = level
        self.player = player

    def on_draw(self):
        for r, line in enumerate(self.level.map):
            for n, t in enumerate(line):
                if t.id != 0:
                    arcade.draw_lrtb_rectangle_filled(n * self.level.scale + 1 + self.left, (n + 1) * self.level.scale - 1 + self.left,
                        (r + 1) * self.level.scale - 1 + self.bottom, r * self.level.scale + 1 + self.bottom,
                        t.color)

        arcade.draw_circle_filled(self.player.pos.x, self.player.pos.y, 4, arcade.color.BLUE)
        
        for i in range(0, 360, 10):
            td = self.player.cast_ray(i)
            if td:
                tile = td[0]
                dist = td[1]
                p = translate_point(self.player.pos, i, dist)
                arcade.draw_line(self.player.pos.x, self.player.pos.y, p.x, p.y, arcade.color.RED)

class GameView(View):
    def __init__(self, level: Level):
        super().__init__()
        self.level = level
        self.player = Player(self.level, (400, 60))
        self.section_2D = Game2DSection(self.level, self.player)
        self.section_2D.enabled = True
        self.section_manager.add_section(self.section_2D)