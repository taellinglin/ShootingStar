# Import the necessary modules for audio
from panda3d.core import AudioManager
import os
import random
import math
import colorsys
import numpy as np
from panda3d.core import Point3, WindowProperties, AmbientLight, LVecBase4f, LVecBase3f, LVector3, LPoint3f, TextureAttrib
from panda3d.core import Shader, Camera, Texture, NodePath, Vec4
from panda3d.core import PointLight, AmbientLight, CardMaker, TransparencyAttrib
from panda3d.bullet import BulletWorld
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import ColorBlendAttrib
from panda3d.core import Vec4
from direct.filter.CommonFilters import CommonFilters


from models import ModelLoader
from gun import Gun
from controls import Controls
from furniture_manager import FurnitureManager
from bottle_manager import BottleManager, Bottle
from bgm import BGMPlayer
from sfx import SFX
from physics import BulletPhysics
from player import PlayerPhysics
from hud import HUD

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
        
        # Physics
        self.physics = BulletPhysics(self.bullet_world, self.render)

        # Models
        self.model_loader = ModelLoader(self.loader, self.render, self.bullet_world, self.camera, fps_mode=True)

        # Factories, BGM/SFX, HUD
        self.furniture_manager = FurnitureManager(self.loader, self.render)
        self.bottle_manager = BottleManager(self.loader, self.render, self.bullet_world, self, self.camera, self.physics)
        self.bgm_player = BGMPlayer("bgm.ogg")
        self.sfx = SFX(self)
        self.hud = HUD(self, self.bottle_manager)

        # Set up gun mechanics
        self.gun = Gun(self, self.bullet_world, self.bottle_manager, self.physics, self.hud)

        # Set up player controls
        self.controls = Controls(self, self.gun, self.model_loader.player)
        self.controls.setup_controls()
        
        # Set up update task
        self.taskMgr.add(self.update, "update")

        # Set up scene (furniture and bottles)
        self.setup_scene()
        self.model_loader.remove_static_gun()
        self.model_loader.remove_static_laser()

        # Set up ambient lighting (slow ROYGBIV cycling)
        self.setup_lighting()
        self.bgm_played = False
        base.taskMgr.add(self.some_task, "someTask")
        

        self.filters = CommonFilters(self.win, self.cam)
        success = self.filters.setBloom(
            blend=(0.3, 0.3, 0.3, 0.0),
            desat=0.5,
            intensity=1.0,
            size="medium"
        )
        if not success:
            print("Bloom filter not supported.")
        
        # Set up the framebuffer to capture the scene
        #self.framebuffer = self.create_framebuffer()
        # Set up the environment, camera, etc.
        #self.enable_bloom()

    def create_framebuffer(self):
        """ Set up a framebuffer to capture the scene. """
        framebuffer = self.win.makeTextureBuffer("sceneBuffer",800, 600)
        framebuffer.setClearColor(Vec4(0, 0, 0, 1))  # Set clear color to black

        # Create a camera to render the scene into the framebuffer
        scene_camera = self.makeCamera(framebuffer)
        scene_camera.node().setLens(self.cam.node().getLens())  # Use the same lens as main camera

        return framebuffer

    def enable_bloom(self):
        """ Apply a basic bloom effect by post-processing. """

        # Create a framebuffer to capture the scene
        self.framebuffer = self.create_framebuffer()

        # Create a quad for the bloom effect
        card_maker = CardMaker("bloomCard")
        card_maker.setFrame(-1, 1, -1, 1)  # Full screen quad
        quad = NodePath(card_maker.generate())
        quad.reparentTo(self.render2d)
        quad.setScale(2)
        quad.setPos(-1, 0, 0)

        # Set transparency on the card for blending with the scene
        quad.setTransparency(TransparencyAttrib.MAlpha)

        # Get the texture from the framebuffer
        scene_texture = self.framebuffer.getTexture()

        # Set up the shader with threshold and intensity values
        bloom_shader = Shader.load(Shader.SL_GLSL, "shaders/bloom_vert.glsl", "shaders/bloom_frag.glsl")
        quad.setShader(bloom_shader)
        quad.setShaderInput("sceneTexture", scene_texture)
        quad.setShaderInput("intensity", 1.0)  # Adjust intensity based on your needs
        quad.setShaderInput("threshold", 0.5)  # Adjust threshold to control which pixels bloom


    # Combine the original scene with the blurred bloom texture
    # This would require a shader that blends the scene and bloom textures together
    def some_task(self, task):
        if self.hud.bottles_shot >= self.hud.bottles_total:
            if not self.bgm_played:  # Check if the win music has been played already
                # Change the BGM to "win.ogg"
                self.bgm_player.replace_bgm("win.ogg")
                self.bgm_played = True  # Set the flag to True so it doesn't play again
        return task.cont    

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

    def bezier_curve(self, p0, p1, p2, p3, num_points=1000, scale_factor=10):
        """Generate points along a scaled cubic Bezier curve."""
        points = []
        for t in np.linspace(0, 1, num_points):
            b_t = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
            # Scale the points by the scale factor
            b_t_scaled = b_t * scale_factor
            points.append(b_t_scaled)
        return points

    def place_bottles_on_curve(self, bottle_manager, curve_points, num_bottles):
        """Distribute bottles along the given Bezier curve points."""
        step = len(curve_points) // num_bottles
        bottles = []

        for i in range(num_bottles):
            pos = curve_points[i * step]  # Get position from curve

            # Ensure pos is LPoint3f
            if not isinstance(pos, LPoint3f):
                pos = LPoint3f(*pos)  # Convert pos to LPoint3f if it's a list or tuple

            # Load bottle model and assign it to the scene
            bottle_model = base.loader.loadModel(os.path.join("models", "bottles", random.choice(bottle_manager.bottle_files)))
            bottle_model.reparentTo(bottle_manager.render)
            bottle_model.setPos(pos)  # Set the initial position

            # Iterate through each geometry in the model
            for node in bottle_model.findAllMatches('**/+GeomNode'):
                geom_node = node.node()
                for i in range(geom_node.getNumGeoms()):
                    state = geom_node.getGeomState(i)
                    
                    # Get texture attribute from the state
                    tex_attrib = state.getAttrib(TextureAttrib)
                    
                    if tex_attrib:
                        tex = tex_attrib.getTexture()
                        if tex:
                            print("Texture applied:", tex)
                        else:
                            print("No texture applied to this geometry.")
                    else:
                        print("No texture attribute found.")

            # Apply random color to the bottle
            bottle_model.setColorScale(*random.choice(bottle_manager.colors))

            # Create bottle object and add it to bottle_manager
            bottle = Bottle(bottle_model, bottle_manager.bullet_world, bottle_manager.game, bottle_manager, bottle_manager.scene_scale)
            bottle_manager.add_bottle(bottle)
            self.hud.update_bottles_total(1)
            bottles.append(bottle)


        return bottles

    def animate_bottles_along_curve(self, bottles, curve_points, speed=0.25):
        """Move bottles along the given Bezier curve in an endless loop like a floating kite tail."""
        def update(task):
            t = (task.time * speed) % 1  # Normalize time to loop between 0 and 1
            index = int(t * (len(curve_points) - 1))  # Get index for current position on curve

            for i, bottle in enumerate(bottles):
                # Offset for ribbon effect: Slight delay to give a trailing effect
                offset = (i * 10) % len(curve_points)
                pos = curve_points[(index + offset) % len(curve_points)]  # Update position along curve

                # Optional: Add a slight oscillation to Z position to simulate floating
                bottle.setPos(pos)
                bottle.on_ribbon = True
                bottle.setZ(pos[2] + np.sin(task.time * 2 + i) * 0.2)  # Slight "floating" effect

                # Optional: Add a little sway or movement along the X or Y axis
                current_pos = bottle.getPos()  # Get the current position of the bottle
                bottle.setX(current_pos[0] + np.sin(task.time * 0.5 + i) * 0.2)  # Sway along X
                bottle.setY(current_pos[1] + np.cos(task.time * 0.5 + i) * 0.2)  # Sway along Y

            return task.cont

        return update


    def setup_scene(self):
        # Place furniture from the town model
        self.furniture_manager.place_furniture(self.model_loader.town)

        # Get all placed furniture models from FurnitureManager
        furniture_objects = self.furniture_manager.get_furniture_objects()

        # Place bottles on the town model and on each furniture model
        self.bottle_manager.place_bottles(self.model_loader.town, furniture_objects)
        # Define 4 control points for a looped Bezier path
        p0, p1, p2, p3 = LVector3(0, 0, 5), LVector3(5, 10, 7), LVector3(-5, 15, 3), LVector3(0, 20, 5)
        curve_points = self.bezier_curve(p0, p1, p2, p3, num_points=20)

        # Create a strand of 10 bottles moving in a ribbon loop
        bottles = self.place_bottles_on_curve(self.bottle_manager, curve_points, num_bottles=8)

        # Add animation task
        self.bottle_manager.game.taskMgr.add(self.animate_bottles_along_curve(bottles, curve_points))

        

    def reset_scene(self):
        """Reset the scene by clearing and reloading all dynamic objects."""

        # Remove existing objects properly
        self.furniture_manager.clear_furniture()
        self.bottle_manager.clear_bottles()

        # Remove old physics world entirely and replace it with a fresh one
        del self.bullet_world
        self.bullet_world = BulletWorld()
        self.bullet_world.setGravity(Point3(0, 0, -9.81))
        self.physics = BulletPhysics(self.bullet_world, self.render)

        # Reload models
        self.model_loader.reload_models()

        # Reset managers
        del self.furniture_manager
        del self.bottle_manager
        self.furniture_manager = FurnitureManager(self.loader, self.render)
        self.bottle_manager = BottleManager(self.loader, self.render, self.bullet_world, self, self.camera, self.physics)

        self.model_loader.player.setHpr(0, 0, 0)  # Ensure player rotation is reset
        self.model_loader.player.setPos(0, 0, 2)  # Reset player position

        # Clear previous input state
        self.controls.clear_input_state()

        # Reinitialize the gun
        del self.gun
        self.gun = Gun(self, self.bullet_world, self.bottle_manager, self.physics, self.hud)

        # Reset HUD
        self.hud.reset()

        # Reset controls properly
        del self.controls
        self.controls = Controls(self, self.gun, self.model_loader.player)
        self.controls.setup_controls()

        # Remove all tasks to ensure old states are gone
        self.taskMgr.remove("update")
        self.taskMgr.add(self.update, "update")

        # Reload scene
        self.setup_scene()
        print("Scene reset successfully!")


    def setup_lighting(self):
        """Set up a slow cycling ambient light."""
        self.ambient_light = AmbientLight("ambient_light")
        # Initial color; will be smoothly updated via the task
        self.ambient_light.setColor(LVecBase4f(1, 1, 1, 0.5))
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
        # Update all bottles
        self.bottle_manager.update(task)
        self.controls.update(dt)
        return task.cont

if __name__ == "__main__":
    game = Game()
    game.run()
