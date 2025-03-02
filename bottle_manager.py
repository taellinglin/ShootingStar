import os
import random
from panda3d.core import Vec4, BitMask32, LVecBase4f, LVector3, PointLight, Material
from panda3d.bullet import BulletRigidBodyNode, BulletConvexHullShape
from panda3d.bullet import BulletRigidBodyNode, BulletConvexHullShape, BulletBoxShape

class BottleManager:
    def __init__(self, loader, render, bullet_world, scene_scale=1.0):
        self.loader = loader
        self.render = render
        self.bullet_world = bullet_world  # Bullet world to add the collision
        self.scene_scale = scene_scale    # Factor to scale offsets, intensity, and radius
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
        Adds a collision shape to the bottle model and applies Bullet physics to make it fall.
        """
        # Get all geometries from the bottle model node
        geometries = self.get_geometries_from_nodepath(bottle)
        
        # If no geometries are found, return
        if not geometries:
            print("No geometries found in bottle!")
            return

        # Create a BulletConvexHullShape for the bottle to handle the collision
        bottle_shape = BulletConvexHullShape()
        
        # Loop through all geometries and add them to the Bullet shape
        for geom in geometries:
            bottle_shape.addGeom(geom)

        # Create a BulletRigidBodyNode for the bottle, enabling physics
        bottle_rigid_body = BulletRigidBodyNode("Bottle")
        bottle_rigid_body.addShape(bottle_shape)
        
        # Set the bottle as a dynamic object (it can move with physics)
        bottle_rigid_body.setMass(1.0)  # You can adjust mass for realism
        bottle_rigid_body.setIntoCollideMask(BitMask32.bit(1))  # Set collision mask for the bottle

        # Attach the BulletRigidBodyNode to the bottle model
        bottle_collision_node = bottle.attachNewNode(bottle_rigid_body)
        
        # Set position and orientation of the collision node to match the bottle's
        bottle_collision_node.setPos(bottle.getPos())
        bottle_collision_node.setHpr(bottle.getHpr())
        
        # Attach the collision node to the render node
        bottle_collision_node.reparentTo(self.render)
        
        # Add the rigid body node to the Bullet world for physics simulation
        self.bullet_world.attachRigidBody(bottle_rigid_body)
        
        print(f"Added collision shape to bottle {bottle.getName()} and enabled physics.")

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
        Each bottle gets a unique ROYGBIV tint, and is illuminated with a PointLight in the same color.
        """
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
            
            # Extract and reparent the existing point lights from the bottle (destructible)
            destructible_node = bottle.find("**/destructible")
            point_lights = destructible_node.findAllMatches("**/Point*")
            for light in point_lights:
                # Reparent existing point lights to bottle
                light.reparentTo(bottle)
                # Adjust position of light based on bottle position
                light.setPos(node.getPos(self.render))
                print(f"Reparented point light from {light.getName()} to bottle.")

            # Set position and orientation relative to the mount node using world coordinates
            bottle.setPos(node.getPos(self.render))
            bottle.setHpr(node.getHpr(self.render))
            
            # Choose a random ROYGBIV color for this specific bottle instance
            color = random.choice(self.colors)
            bottle.setColorScale(*color)
            
            print(f"Placed bottle '{random_bottle_file}' tinted {color} at {node.getPos(self.render)}")
            
            # Add collision for the bottle and enable physics
            self.add_collision_to_bottle(bottle, node)
            
            # Illuminate the bottle with a PointLight using the same color
            self.illuminate_bottle(bottle, color)

    def illuminate_bottle(self, bottle, color):
        """
        Creates a PointLight with the given ROYGBIV color and attaches it to the bottle.
        The light is positioned above and in front of the bottle with offsets scaled for a large scene.
        The attenuation is adjusted to increase the effective radius.
        """
        bottle_light = PointLight("bottle_light")
        bottle_light.setColor(LVecBase4f(color[0], color[1], color[2], color[3]))
        
        # Adjust attenuation values for a large scene.
        attenuation_constant = 1.0
        attenuation_linear = 0.05 / self.scene_scale
        attenuation_quadratic = 0.05 / (self.scene_scale * self.scene_scale)
        bottle_light.setAttenuation((attenuation_constant, attenuation_linear, attenuation_quadratic))
        
        bottle_light_np = bottle.attachNewNode(bottle_light)
        
        # Scale the offset based on scene scale.
        offset = LVector3(0, -3 * self.scene_scale, 3 * self.scene_scale)
        bottle_light_np.setPos(offset)
        
        # Enable the light in the render scene
        self.render.setLight(bottle_light_np)
        print(f"Illuminated bottle {bottle.getName()} with light color {color} at offset {offset} and attenuation {(attenuation_constant, attenuation_linear, attenuation_quadratic)}")

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
