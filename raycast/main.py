from importlib import resources as pkg_resources

import arcade
from arcade import Window

import raycast.data
from raycast.lib.lib import Level
from raycast.lib.views import GameView


class RaycastDemo(Window):
    def __init__(self):
        super().__init__(1200, 600, "Raycast Demo", update_rate=1/120, center_window=True, enable_polling=True)

    def setup(self):
        with pkg_resources.path(raycast.data, "level.lvl") as p:
            level = Level.from_lvl(p)

        self.game_view = GameView(level)
        self.show_view(self.game_view)

def main():
    window = RaycastDemo()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
