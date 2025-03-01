import os
import random
from panda3d.core import Vec4, BitMask32
from panda3d.bullet import BulletRigidBodyNode, BulletConvexHullShape

class BottleManager:
    def __init__(self, loader, render, bullet_world):
        self.loader = loader
        self.render = render
        self.bullet_world = bullet_world  # Bullet world to add the collision
        self.bottle_path = "models/bottles/"
        
        # Load all available bottle model filenames from the directory
        if os.path.exists(self.bottle_path):
            self.bottle_files = [f for f in os.listdir(self.bottle_path) if f.endswith(".bam")]
        else:
            self.bottle_files = []
            print("Bottle path does not exist!")
        
        # Define ROYGBIV colors as RGBA tuples
        self.colors = [
            (1, 0, 0, 1),       # Red
            (1, 0.5, 0, 1),     # Orange
            (1, 1, 0, 1),       # Yellow
            (0, 1, 0, 1),       # Green
            (0, 0, 1, 1),       # Blue
            (0.29, 0, 0.51, 1), # Indigo
            (0.58, 0, 0.83, 1)  # Violet
        ]

    def add_collision_to_bottle(self, bottle, node):
        """
        Adds a collision shape to the bottle model.
        """
        # Get all geometries from the bottle model node
        geometries = self.get_geometries_from_nodepath(bottle)
        
        # If no geometries are found, return
        if not geometries:
            print("No geometries found in bottle!")
            return

        # Create a BulletConvexHullShape for the bottle
        bottle_shape = BulletConvexHullShape()
        
        # Loop through all geometries and add them to the Bullet shape
        for geom in geometries:
            bottle_shape.addGeom(geom)

        # Create a BulletRigidBodyNode for the bottle
        bottle_rigid_body = BulletRigidBodyNode("Bottle")
        bottle_rigid_body.addShape(bottle_shape)
        bottle_rigid_body.setIntoCollideMask(BitMask32.bit(1))  # Similarly for the bottle

        # Attach the BulletRigidBodyNode to the bottle
        bottle_collision_node = bottle.attachNewNode(bottle_rigid_body)
        
        # Set position and orientation of the collision node to match the bottle's position and orientation
        bottle_collision_node.setPos(bottle.getPos())
        bottle_collision_node.setHpr(bottle.getHpr())
        
        # Attach the collision node to the render node (this does not need an additional call to attachNewNode)
        bottle_collision_node.reparentTo(self.render)
        print(f"Added collision shape to bottle {bottle.getName()}")



    def get_geometries_from_nodepath(self, node_path):
        """
        Extracts all geometries from a NodePath if available.
        """
        geometries = []

        # Check if the node has a GeomNode
        geom_node = node_path.findAllMatches('**/+GeomNode')
        if geom_node.isEmpty():
            print("No GeomNode found in the NodePath.")
            return geometries
        
        # Extract Geoms from the GeomNode
        for geom_node_instance in geom_node:
            geom_node_obj = geom_node_instance.node()  # Get the actual GeomNode object
            for i in range(geom_node_obj.getNumGeoms()):
                geom = geom_node_obj.getGeom(i)  # Get the i-th geometry
                geometries.append(geom)
                # Print basic information about the geometry
                print(f"Found Geom with {geom.getPrimitive(0).getNumVertices()} vertices.")

        return geometries
    def place_bottles_in_model(self, model):
        """
        Find all bottle mount nodes in the given model and place a randomly tinted bottle at each mount.
        """
        # Find nodes whose names start with "bottle" (or "bottle.xx")
        bottle_nodes = model.findAllMatches("**/bottle*")
        if bottle_nodes.isEmpty():
            print(f"No bottle mount nodes found in {model.getName()}!")
            return

        for node in bottle_nodes:
            if not self.bottle_files:
                print("No bottle models available!")
                return
            
            # Choose a random bottle model file
            random_bottle_file = random.choice(self.bottle_files)
            model_path = os.path.join(self.bottle_path, random_bottle_file)
            bottle = self.loader.loadModel(model_path)
            bottle.reparentTo(self.render)
            
            # Set position and orientation relative to the mount node using world coordinates
            bottle.setPos(node.getPos(self.render))
            bottle.setHpr(node.getHpr(self.render))
            
            # Tint with a random ROYGBIV color
            color = random.choice(self.colors)
            bottle.setColor(*color)
            
            print(f"Placed bottle '{random_bottle_file}' tinted {color} at {node.getPos(self.render)}")
            
            # Add collision for the bottle
            self.add_collision_to_bottle(bottle, node)

    def place_bottles(self, town_model, furniture_models=None):
        """
        Place bottles on bottle mount nodes found in the town model and in each furniture model.
        """
        # Place bottles in the town model first.
        self.place_bottles_in_model(town_model)

        # Then, if a list of furniture models is provided, place bottles on each of them.
        if furniture_models:
            for furniture in furniture_models:
                self.place_bottles_in_model(furniture)
