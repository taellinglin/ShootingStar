from panda3d.core import Vec4, BitMask32, LVecBase4f, LVector3, PointLight
from panda3d.bullet import BulletRigidBodyNode, BulletConvexHullShape
from physics import BulletPhysics
from models import ModelLoader
import os
import random

class BottleManager:
    def __init__(self, model_loader, render, bullet_world, game, camera, physics, scene_scale=1.0):
        self.model_loader = ModelLoader(model_loader, render, bullet_world, camera)
        self.render = render
        self.physics = physics
        self.game = game
        self.bullet_world = bullet_world
        self.scene_scale = scene_scale
        self.bottle_path = "models/bottles/"
        
        self.bottle_files = [f for f in os.listdir(self.bottle_path) if f.endswith(".bam")] if os.path.exists(self.bottle_path) else []
        if not self.bottle_files:
            print("Bottle path does not exist or contains no models!")
        
        self.colors = [
            (1, 0, 0, 1), (1, 0.5, 0, 1), (1, 1, 0, 1),
            (0, 1, 0, 1), (0, 0, 1, 1), (0.29, 0, 0.51, 1), (0.58, 0, 0.83, 1)
        ]
        self.bottles = []

    def add_bottle(self, bottle):
        """Add a new bottle to the manager."""
        self.bottles.append(bottle)

    def get_all_bottles(self):
        """Return a list of all bottle nodes."""
        return self.bottles
    def remove_bottle(self, bottle):
        if not bottle.destroyed:
            bottle.cleanup()
        self.bottles.remove(bottle)

        
    def add_collision_to_bottle(self, bottle):
        """Add collision to a bottle."""
        # This method will be handled by the Bottle class itself now

    def place_bottles_in_model(self, model):
        """Place bottles in the model."""
        bottle_nodes = model.findAllMatches("**/bottle*")
        
        if bottle_nodes.isEmpty() or not self.bottle_files:
            print(f"No bottle mount nodes found in {model.getName()} or no bottles available!")
            return
        
        for node in bottle_nodes:
            bottle_model = self.model_loader.load_single_model(os.path.join(self.bottle_path, random.choice(self.bottle_files)))
            bottle_model.reparentTo(self.render)
            bottle_model.setPos(node.getPos(self.render))
            bottle_model.setHpr(node.getHpr(self.render))
            bottle_model.setColorScale(*random.choice(self.colors))
            
            bottle = Bottle(bottle_model, self.bullet_world, self.game, self, self.scene_scale)
            self.add_bottle(bottle)
            self.illuminate_bottle(bottle_model)
            self.game.hud.update_bottles_total(1)
    
    def illuminate_bottle(self, bottle):
        color = bottle.getColorScale()
        light = PointLight("bottle_light")
        light.setColor(LVecBase4f(*color))
        light.setAttenuation((1.0, 0.05 / self.scene_scale, 0.05 / (self.scene_scale ** 2)))
        light_np = bottle.attachNewNode(light)
        light_np.setPos(LVector3(0, -3 * self.scene_scale, 3 * self.scene_scale))
        self.render.setLight(light_np)

    def place_bottles(self, town_model, furniture_models=None):
        """Place bottles in the given models."""
        self.place_bottles_in_model(town_model)
        if furniture_models:
            for furniture in furniture_models:
                self.place_bottles_in_model(furniture)
                
    
    def update(self, task):
        """Update all bottles in the game."""
        for bottle in self.bottles:
            bottle.update(task)
        return task.cont  # Continue checking for updates
    def get_total_bottles(self):
        """Return the total number of bottles in the game."""
        return len(self.bottles)
    def clear_bottles(self):
        """
        Removes all placed furniture objects from the scene and clears the stored list.
        """
        for furniture in self.bottles:
            if furniture:
                furniture.cleanup()  # Remove the model from the scene graph
                self.bottles.clear()  # Clear the list of stored objects
                print("All furniture has been cleared from the scene.")
        return len(self.bottles)


class Bottle:
    def __init__(self, model, bullet_world, game, bottle_manager, scene_scale=1.0):
        self.model = model  # The model of the bottle
        self.bullet_world = bullet_world
        self.game = game
        self.bottle_manager = bottle_manager
        self.scene_scale = scene_scale
        self.node = model  # The actual node for the bottle
        self.is_broken = False
        self.node.setName("Bottle")  # Ensure it's named for collision detection
        self.destroyed = False
        # Set up the collision detection for the bottle
        self.bottle_rb = BulletRigidBodyNode("Bottle")
        self.bottle_shape = BulletConvexHullShape()
        for geom in self.bottle_manager.model_loader.get_geometries(self.node):
            self.bottle_shape.addGeom(geom)
        self.bottle_rb.addShape(self.bottle_shape)
        self.bottle_rb.setMass(1.0)
        self.node.attachNewNode(self.bottle_rb)
        self.bottle_manager.bullet_world.attachRigidBody(self.bottle_rb)

    def update(self, task):
        if self.destroyed:
            self.bottle_manager.remove_bottle(self)  # Ensure it's removed from active bottles
            return task.done  # Stop updating this bottle

        if self.node.isEmpty():
            print("[ERROR] Bottle node is empty, skipping update")
            return task.done
        if not self.node.isEmpty():
            self.bullet_world.attachRigidBody(self.bottle_rb)
        else:
            print("[ERROR] Bottle node is empty, skipping physics attachment")

        # Perform ray test for collision detection
        start = self.node.getPos(self.game.render)  # Get bottle's world position
        forward_dir = self.node.getQuat(self.game.render).getUp()  # Pellet's direction
        end = start + forward_dir * 4  # Move a small distance forward

        result = self.game.bullet_world.rayTestClosest(start, end)
        
        if result.hasHit():
            hit_node = result.getNode()
            hit_name = hit_node.getName() if hit_node else "Unknown"
            
            if hit_name == "Pellet":
                print(f"[DEBUG] Pellet collision detected with bottle at {hit_node.getPos(self.game.render)}")
                self.bottle_manager.physics.break_bottle(self.node)  # Call break bottle logic
                self.is_broken = True  # Mark this bottle as broken
                self.destroyed = True

        return task.cont  # Keep the update loop going

    def cleanup(self):
        """Clean up the bottle by removing it from the scene and physics simulation."""
        # Detach the bottle's node from the scene graph
        self.node.detachNode()
        
        # Remove the bottle's rigid body from the Bullet physics world
        self.bullet_world.removeRigidBody(self.bottle_rb)
        
        # Optionally delete the bottle object if no longer needed
        del self
    