from panda3d.core import BitMask32, Vec3
from panda3d.bullet import BulletCapsuleShape, BulletRigidBodyNode

class PlayerPhysics:
    def __init__(self, player_model, bullet_world):
        self.player_model = player_model
        self.bullet_world = bullet_world
        self.is_on_ground = False
        self.velocity = Vec3(0, 0, 0)

        # Setup player collision and physics
        self.setup_player_collision()

    def setup_player_collision(self):
        """Creates a capsule collision shape for the player."""
        # Define capsule shape parameters
        collision_radius = 0.5  # Adjust based on model size
        collision_height = 1.5  # Adjust based on model height
        capsule_shape = BulletCapsuleShape(collision_radius, collision_height)

        # Create Bullet rigid body node
        self.bullet_rigid_body = BulletRigidBodyNode("player_rigid_body")
        self.bullet_rigid_body.addShape(capsule_shape)
        self.bullet_rigid_body.setMass(70)  # Set mass to prevent infinite falling
        self.bullet_rigid_body.setGravity(Vec3(0, 0, -9.8))  # Apply gravity
        self.bullet_rigid_body.setLinearFactor(Vec3(1, 1, 0))  # Restrict movement in Z (vertical)
        
        # Attach Bullet node to the player model
        self.bullet_node_path = self.player_model.attachNewNode(self.bullet_rigid_body)
        self.bullet_node_path.setPos(self.player_model.getPos())  # Align with player model
        self.bullet_node_path.setCollideMask(BitMask32.bit(1))  # Set collision mask

        # Attach the rigid body to the physics world
        self.bullet_world.attachRigidBody(self.bullet_rigid_body)

    def check_if_on_ground(self):
        """Uses a ray test to check if the player is standing on the ground."""
        player_bottom = self.bullet_node_path.getPos(render) - Vec3(0, 0, 1.0)  # Bottom of capsule
        ground_check = self.bullet_world.rayTestClosest(
            player_bottom, player_bottom + Vec3(0, 0, -0.2)  # Short ray to detect ground
        )

        self.is_on_ground = ground_check.hasHit()

    def apply_gravity(self, gravity_strength=-9.8):
        """Applies gravity when the player is in the air."""
        if not self.is_on_ground:
            velocity = self.bullet_rigid_body.getLinearVelocity()
            velocity.z = max(velocity.z + gravity_strength * globalClock.getDt(), -50)  # Limit fall speed
            self.bullet_rigid_body.setLinearVelocity(velocity)

    def move(self, direction, speed=10):
        """Moves the player by applying velocity in the given direction."""
        velocity = Vec3(direction.x * speed, direction.y * speed, self.bullet_rigid_body.getLinearVelocity().z)
        self.bullet_rigid_body.setLinearVelocity(velocity)

    def update(self):
        """Updates the player's physics state each frame."""
        self.check_if_on_ground()
        self.apply_gravity()
        
        # Debugging output
        if self.is_on_ground:
            print("Player is on the ground!")
        else:
            print("Player is in the air!")
