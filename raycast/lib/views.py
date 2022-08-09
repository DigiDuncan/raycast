import arcade
from arcade import View, Section

from raycast.lib.lib import Level, Player
from raycast.lib.utils import translate_point


class Game2DSection(Section):
    def __init__(self, level: Level, player: Player):
        super().__init__(0, 0, 600, 600, name = "Game2D")
        self.level = level
        self.player = player
        self.player.debug = True
        self.level.debug = True

    def on_draw(self):
        self.level.draw(self.left, self.bottom)
        self.player.draw(self.left, self.bottom)

class GameView(View):
    def __init__(self, level: Level):
        super().__init__()
        self.level = level
        self.player = Player(self.level, (18, 3))
        self.section_2D = Game2DSection(self.level, self.player)
        self.section_2D.enabled = True
        self.section_manager.add_section(self.section_2D)
        self.section_manager.disable_all_keyboard_events()

        self.debug = True

    def on_update(self, delta_time: float):
        # keyboard handling:
        if self.window.keyboard[arcade.key.W]:
            self.player.dx += self.player.heading_x
            self.player.dy += self.player.heading_y
        if self.window.keyboard[arcade.key.S]:
            self.player.dx -= self.player.heading_x
            self.player.dy -= self.player.heading_y
        if self.window.keyboard[arcade.key.A]:
            self.player.da += 120
        if self.window.keyboard[arcade.key.D]:
            self.player.da -= 120

        self.player.update(delta_time)

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.PERIOD:
                self.player.debug = not self.player.debug
                self.level.debug = not self.level.debug

    def on_draw(self):
        self.clear()