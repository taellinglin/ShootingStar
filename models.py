from panda3d.core import Point3
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletBoxShape, BulletSphereShape
import os
import random
from direct.task.TaskManagerGlobal import taskMgr

class ModelLoader:
    def __init__(self, loader, render, bullet_world, camera, fps_mode=False):
        self.loader = loader
        self.render = render
        self.bullet_world = bullet_world
        self.camera = camera
        self.fps_mode = fps_mode
        self.load_models()

    def load_models(self):
        # Load town model
        self.town = self.loader.loadModel("models/town.bam")
        self.town.reparentTo(self.render)

        # Add physics to the town
        town_rigid_node = BulletRigidBodyNode("town")
        town_shape = BulletBoxShape((10, 10, 1))
        town_rigid_node.addShape(town_shape)
        town_node_path = self.render.attachNewNode(town_rigid_node)
        self.bullet_world.attachRigidBody(town_rigid_node)

        # Get player start position
        player_start = self.town.find("**/player_start")
        start_pos = player_start.getPos()
        print(f"Found Player Starting Point: { start_pos }")
        player_start_pos = player_start.getPos() if not player_start.isEmpty() else Point3(0, 0, 0)

        # Load player model
        self.player = self.loader.loadModel("models/player.bam")

        # Create physics node for player
        player_rigid_node = BulletRigidBodyNode("player")
        player_shape = BulletSphereShape(1)
        player_rigid_node.addShape(player_shape)
        self.player_node_path = self.render.attachNewNode(player_rigid_node)
        self.player_node_path.setPos(player_start_pos)
        self.bullet_world.attachRigidBody(player_rigid_node)

        # Parent visual model to physics node
        self.player.reparentTo(self.player_node_path)
        self.player_node_path.setScale(0.5)

        # Load gun and attach it
        self.gun_mount = self.player.find("**/gun_mount")
        self.gun = self.loader.loadModel("models/gun.bam")
        if not self.gun_mount.isEmpty():
            self.gun.reparentTo(self.player_node_path)
            self.gun.setPos(self.gun_mount.getPos(self.player_node_path))
            self.gun.setHpr(self.gun_mount.getHpr(self.player_node_path))
            print("Gun mounted to player physics node.")
        else:
            print("Warning: 'gun_mount' not found in player model!")

        if self.fps_mode:
            self.gun.wrtReparentTo(self.camera)
            taskMgr.add(self.update_gun_position, "update_gun_position")
            print("Gun mounted to camera for FPS mode.")

        # Load and attach laser
        self.fire_dir = self.gun.find("**/fire_dir")
        if not self.fire_dir.isEmpty():
            self.laser = self.loader.loadModel("models/lazer.bam")
            self.laser.reparentTo(self.fire_dir)
            self.laser.setPos(0, 0, 0)
            self.laser.setScale(0.1)
            print("Laser attached successfully.")
        else:
            print("Warning: 'fire_dir' not found in gun model!")

        # Find **/cat node and replace it with models/cat.bam
        cat_node = self.town.find("**/cat")
        if not cat_node.isEmpty():
            # Load the new cat model
            cat_model = self.loader.loadModel("models/cat.bam")
            cat_model.reparentTo(cat_node)
            cat_model.setPos(0, 0, 0)  # Adjust the position as needed
            print("Cat model replaced successfully.")
        else:
            print("Warning: 'cat' node not found in town model!")


    def update_gun_position(self, task):
        offset = (0.3, 1.4, -0.3)
        self.gun.setPos(self.camera, *offset)
        return task.cont
