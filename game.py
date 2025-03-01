from panda3d.core import Point3, WindowProperties
from panda3d.bullet import BulletWorld
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
import random

from models import ModelLoader
from gun import Gun
from controls import Controls
from furniture_manager import FurnitureManager
from bottle_manager import BottleManager

class Game(ShowBase):
    def __init__(self):
        super().__init__()

        # Lock the mouse in the window
        props = WindowProperties()
        props.setCursorHidden(True)
        self.win.requestProperties(props)

        # Initialize Bullet physics world
        self.bullet_world = BulletWorld()
        self.bullet_world.setGravity(Point3(0, 0, -9.81))

        # Load models (town, player, gun)
        self.model_loader = ModelLoader(self.loader, self.render, self.bullet_world, self.camera, fps_mode=True)

        # Initialize managers
        self.furniture_manager = FurnitureManager(self.loader, self.render)
        self.bottle_manager = BottleManager(self.loader, self.render, self.bullet_world)

        # Set up player controls
        self.controls = Controls(self)
        self.controls.setup_controls()

        # Set up gun mechanics
        self.gun = Gun(self, self.bullet_world, self.bottle_manager)

        # Set up update task
        self.taskMgr.add(self.update, "update")

        # Set up scene (furniture and bottles)
        self.setup_scene()

    def setup_scene(self):
        # Place furniture from the town model
        self.furniture_manager.place_furniture(self.model_loader.town)

        # Get all placed furniture models from FurnitureManager
        furniture_objects = self.furniture_manager.get_furniture_objects()

        # Place bottles on the town model and on each furniture model
        self.bottle_manager.place_bottles(self.model_loader.town, furniture_objects)

    def update(self, task):
        dt = globalClock.get_dt()
        self.bullet_world.doPhysics(dt)
        self.controls.update(dt)
        return task.cont

if __name__ == "__main__":
    game = Game()
    game.run()
