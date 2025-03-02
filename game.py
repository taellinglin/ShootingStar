import os
import random
import math
import colorsys

from panda3d.core import Point3, WindowProperties, AmbientLight, LVecBase4f, LVecBase3f
from panda3d.bullet import BulletWorld
from direct.showbase.ShowBase import ShowBase
from direct.task import Task

from models import ModelLoader
from gun import Gun
from controls import Controls
from furniture_manager import FurnitureManager
from bottle_manager import BottleManager

class Game(ShowBase):
    def __init__(self):
        super().__init__()

        # Set the window to fullscreen at the native resolution
        self.set_fullscreen()

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

        # Set up ambient lighting (slow ROYGBIV cycling)
        self.setup_lighting()

    def set_fullscreen(self):
        # Use the pipe's display information to detect the native resolution.
        display_info = self.pipe.getDisplayInformation()
        modes = display_info.getDisplayModes()
        
        if modes:
            # Assuming the highest resolution mode is the native resolution.
            native_mode = max(modes, key=lambda m: (m.width, m.height))
            width = native_mode.width
            height = native_mode.height
            print(f"Native resolution detected: {width}x{height}")
        else:
            # Fallback to current window properties if no display modes are found.
            props = self.win.getProperties()
            width, height = props.getXSize(), props.getYSize()
            print(f"Fallback resolution: {width}x{height}")

        wp = WindowProperties()
        wp.setFullscreen(True)
        wp.setSize(width, height)
        wp.setOrigin(0, 0)
        self.win.requestProperties(wp)



    def setup_scene(self):
        # Place furniture from the town model
        self.furniture_manager.place_furniture(self.model_loader.town)

        # Get all placed furniture models from FurnitureManager
        furniture_objects = self.furniture_manager.get_furniture_objects()

        # Place bottles on the town model and on each furniture model
        self.bottle_manager.place_bottles(self.model_loader.town, furniture_objects)

    def setup_lighting(self):
        """Set up a slow cycling ambient light."""
        self.ambient_light = AmbientLight("ambient_light")
        # Initial color; will be smoothly updated via the task
        self.ambient_light.setColor(LVecBase4f(1, 1, 1, 1))
        self.ambient_light_np = self.render.attachNewNode(self.ambient_light)
        self.render.setLight(self.ambient_light_np)
        # Add a task to animate the ambient light color
        #self.taskMgr.add(self.animate_ambient_light, "animate_ambient_light")

    def animate_ambient_light(self, task):
        """Animate the ambient light color slowly cycling through ROYGBIV colors."""
        period = 60.0  # Time in seconds for a full cycle
        hue = (task.time / period) % 1.0  # Cycle hue over [0,1]
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        self.ambient_light.setColor(LVecBase4f(r, g, b, 0.1))
        return task.cont

    def update(self, task):
        """Update the game state, physics, and controls."""
        dt = globalClock.get_dt()
        self.bullet_world.doPhysics(dt)
        self.controls.update(dt)
        return task.cont

if __name__ == "__main__":
    game = Game()
    game.run()
