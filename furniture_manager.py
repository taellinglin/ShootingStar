import os
import random
from panda3d.core import Vec3

class FurnitureManager:
    def __init__(self, loader, render):
        self.loader = loader
        self.render = render
        self.furniture_path = "models/furniture/"
        self.furniture_objects = []  # To store references to placed furniture models

    def place_furniture(self, town_model):
        """
        Find unique furniture mount nodes in the town model and place a random furniture model
        at each unique mount, using the mount's position, orientation, and scale.
        """
        # Find all nodes with "furniture" in their name (or similar)
        furniture_nodes = town_model.findAllMatches("**/furniture*")
        if furniture_nodes.isEmpty():
            print("No furniture nodes found in the town model!")
            return

        # Use a dictionary to collect unique mount positions (rounded to 2 decimals)
        unique_mounts = {}
        for node in furniture_nodes:
            pos = node.getPos(self.render)
            key = (round(pos.x, 2), round(pos.y, 2), round(pos.z, 2))
            if key not in unique_mounts:
                unique_mounts[key] = node
            else:
                print(f"Duplicate mount at {key} ignored.")

        # Get available furniture models from the directory
        furniture_files = [f for f in os.listdir(self.furniture_path) if f.endswith(".bam")]
        if not furniture_files:
            print("No furniture models found in 'models/furniture'!")
            return

        # For each unique mount, place one furniture model
        for key, node in unique_mounts.items():
            random_furniture = random.choice(furniture_files)
            model_path = os.path.join(self.furniture_path, random_furniture)
            furniture_model = self.loader.loadModel(model_path)
            furniture_model.reparentTo(self.render)
            
            # Place furniture using the mount node's world transform
            furniture_model.setPos(node.getPos(self.render))
            furniture_model.setHpr(node.getHpr(self.render))
            
            # Use the mount node's scale; if it's (1,1,1) you can choose a default scale
            mount_scale = node.getScale(self.render)
            default_scale = Vec3(1)  # Default scale
            if mount_scale == default_scale:
                # Optionally randomize scale within a range
                mount_scale = Vec3(random.uniform(0.8, 1.2))  # Random scale range (adjust as needed)
            furniture_model.setScale(mount_scale)
            
            print(f"Placed furniture '{random_furniture}' at {node.getPos(self.render)} with scale {furniture_model.getScale()}")
            
            # Store the placed furniture model in the list
            self.furniture_objects.append(furniture_model)

    def get_furniture_objects(self):
        """
        Returns the list of placed furniture objects.
        """
        return self.furniture_objects
