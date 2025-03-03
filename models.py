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
        print(f"Found Player Starting Point: {start_pos}")
        player_start_pos = player_start.getPos() if not player_start.isEmpty() else Point3(3.1330947, -137.16002, 6.6172513)

        # Load player model
        self.player = self.loader.loadModel("models/player.bam")

        # Create physics node for player
        self.player_rigid_node = BulletRigidBodyNode("player")
        player_shape = BulletSphereShape(1)
        self.player_rigid_node.addShape(player_shape)
        self.player_node_path = self.render.attachNewNode(self.player_rigid_node)
        self.player_node_path.setPos(player_start_pos)
        self.bullet_world.attachRigidBody(self.player_rigid_node)

        # Parent visual model to physics node
        self.player.reparentTo(self.player_node_path)
        self.player_node_path.setScale(0.5)

        # Load gun and attach it only if FPS mode is active
        self.gun_mount = self.player.find("**/gun_mount")
        self.gun = self.loader.loadModel("models/gun.bam")

        if self.fps_mode:
            if not self.gun_mount.isEmpty():
                self.gun.reparentTo(self.camera)  # Reparent the gun to the camera in FPS mode
                self.gun.setPos(0.3, 1.4, -0.3)  # Adjust gun's position relative to the camera
                print("Gun mounted to camera for FPS mode.")
                taskMgr.add(self.update_gun_position, "update_gun_position")  # Ensure it's updated
                # Remove the other gun model (if it is parented to player)
                self.remove_static_gun()
            else:
                print("Warning: 'gun_mount' not found in player model!")
        else:
            if not self.gun_mount.isEmpty():
                self.gun.reparentTo(self.player_node_path)
                self.gun.setPos(self.gun_mount.getPos(self.player_node_path))
                self.gun.setHpr(self.gun_mount.getHpr(self.player_node_path))
                print("Gun mounted to player physics node.")
            else:
                print("Warning: 'gun_mount' not found in player model!")

        # Load and attach laser
        self.fire_dir = self.gun.find("**/fire_dir")
        if not self.fire_dir.isEmpty():
            self.laser = self.loader.loadModel("models/lazer.bam")
            self.laser.reparentTo(self.fire_dir)
            self.laser.setPos(0, 0, 0)
            self.laser.setScale(0.1)
            print("Laser attached successfully.")
            # Remove the static laser (if it is not parented to the camera)
            self.remove_static_laser()
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
        """Update the position of the gun relative to the camera"""
        if self.fps_mode:
            offset = (0.3, 1.4, -0.3)
            self.gun.setPos(self.camera, *offset)  # Set position relative to camera
        return task.cont

    def remove_static_gun(self):
        """Remove the gun that is not moving with the camera"""
        static_gun = self.player.find("**/gun")  # Find the other gun (non-camera mounted)
        if static_gun:
            static_gun.removeNode()  # Remove the node if it's not the camera-attached gun
            print("Removed static gun.")

    def remove_static_laser(self):
        """Remove the laser that is not moving with the camera"""
        static_laser = self.gun.find("**/laser")  # Find the other laser (non-camera mounted)
        if static_laser:
            static_laser.removeNode()  # Remove the node if it's not the camera-attached laser
            print("Removed static laser.")

    def get_geometries(self, model):
        """ Extracts all GeomNodes from a given model. """
        geometries = []
        for node in model.findAllMatches("**/+GeomNode"):
            geom_node = node.node()
            for i in range(geom_node.getNumGeoms()):
                geometries.append(geom_node.getGeom(i))
        return geometries

    def load_single_model(self, model_path):
        """Load a single model given the path."""
        return self.loader.loadModel(model_path)
