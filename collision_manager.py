from panda3d.core import CollisionNode, CollisionBox, CollisionSphere
from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape, BulletSphereShape
from panda3d.core import Point3

class CollisionManager:
    def __init__(self, bullet_world, render):
        self.bullet_world = bullet_world
        self.render = render

    def add_collision(self, node_path, shape_type, dimensions, mass=0, position=Point3(0, 0, 0)):
        """
        General method to add collision to any object.
        :param node_path: The model node to attach the collision to.
        :param shape_type: The type of shape (box or sphere).
        :param dimensions: The dimensions of the shape (e.g., (width, height, depth) for box or radius for sphere).
        :param mass: The mass of the object (default is 0 for immovable objects).
        :param position: The position where the collision should be placed (default is (0, 0, 0)).
        """
        # Create Bullet collision shape based on shape_type
        if shape_type == "box":
            shape = BulletBoxShape(dimensions)
        elif shape_type == "sphere":
            shape = BulletSphereShape(dimensions)
        else:
            raise ValueError("Unsupported shape type")

        # Create a rigid body node for the object
        rigid_node = BulletRigidBodyNode("rigid_node")
        rigid_node.addShape(shape)
        rigid_node.setMass(mass)

        # Attach the rigid body to the render node
        node_path = self.render.attachNewNode(rigid_node)
        node_path.setPos(position)
        self.bullet_world.attachRigidBody(rigid_node)
        
        return node_path  # Return the node_path with collision

    def setup_town_collision(self, town_model):
        # Example: Add collision to the town model
        return self.add_collision(town_model, "box", (10, 10, 1))

    def setup_furniture_collision(self, furniture_model, mass=0):
        # Example: Add collision to furniture
        return self.add_collision(furniture_model, "box", (2, 2, 1), mass=mass)

    def setup_player_collision(self, player_model, mass=1):
        # Example: Add collision to player
        return self.add_collision(player_model, "sphere", 1, mass=mass)
