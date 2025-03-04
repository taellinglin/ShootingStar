from panda3d.core import BitMask32, Vec3
from panda3d.bullet import BulletCapsuleShape, BulletRigidBodyNode, ZUp

class PlayerPhysics:
    def __init__(self, player_model, bullet_world):
        self.player_model = player_model
        self.bullet_world = bullet_world
        self.is_on_ground = False
        self.velocity = Vec3(0, 0, 0)
        self.gravity_strength = -9.8  # Gravity strength (adjustable)
        self.move_speed = 10  # Move speed for the player
        self.jump_speed = 15  # Jump speed (for future jumping mechanic)

        # Setup player collision and physics
        self.setup_player_physics()

        # Set initial position (5 feet above the ground)
        self.bullet_node_path.setPos(0, 0, 1.524 * 2)

    def check_if_on_ground(self):
        """Uses a ray test to check if the player is standing on the ground."""
        player_bottom = self.bullet_node_path.getPos(render) - Vec3(0, 0, 1.0)  # Bottom of capsule
        ground_check = self.bullet_world.rayTestClosest(
            player_bottom, player_bottom + Vec3(0, 0, -0.2)  # Short ray to detect ground
        )

        self.is_on_ground = ground_check.hasHit()

    def apply_gravity(self):
        """Applies gravity when the player is in the air."""
        if not self.is_on_ground:
            velocity = self.bullet_rigid_body.getLinearVelocity()
            velocity.z = max(velocity.z + self.gravity_strength * globalClock.getDt(), -50)  # Limit fall speed
            self.bullet_rigid_body.setLinearVelocity(velocity)

    def move(self, direction):
        """Moves the player by applying velocity in the given direction."""
        velocity = Vec3(direction.x * self.move_speed, direction.y * self.move_speed, self.bullet_rigid_body.getLinearVelocity().z)
        self.bullet_rigid_body.setLinearVelocity(velocity)

    def jump(self):
        """Makes the player jump if they are on the ground."""
        if self.is_on_ground:
            velocity = self.bullet_rigid_body.getLinearVelocity()
            velocity.z = self.jump_speed  # Apply upward force for jumping
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

    def reset(self, position=Vec3(0, 0, 1.524)):
        """Resets the player's position and velocity."""
        self.bullet_rigid_body.setLinearVelocity(Vec3(0, 0, 0))  # Stop movement
        self.bullet_rigid_body.setAngularVelocity(Vec3(0, 0, 0))  # Reset rotation velocity
        self.bullet_node_path.setPos(position)  # Reset position
        self.bullet_rigid_body.clearForces()  # Remove any applied forces
        
        # Restore physics properties
        self.restore_physics()

    def restore_physics(self):
        """Restores the player's physics properties after a reset."""
        if self.bullet_rigid_body not in self.bullet_world.getRigidBodies():
            self.bullet_world.attachRigidBody(self.bullet_rigid_body)

        # Reapply physics settings
        self.bullet_rigid_body.setAngularFactor(Vec3(1, 1, 1))  # Ensure full rotation is enabled
        self.bullet_rigid_body.setLinearVelocity(Vec3(0, 0, 0))
        self.bullet_rigid_body.setAngularVelocity(Vec3(0, 0, 0))
        #self.bullet_rigid_body.setDamping(0.05, 0.05)  # Reset damping for realistic movement

        print("Player physics restored!")

    def setup_player_physics(self):
        """Setup player physics with a capsule collision shape representing a 5-foot-tall player."""
        total_height_meters = 1.524  # 5 feet in meters
        radius = 0.3  # Adjust the radius as needed
        cylinder_height = total_height_meters - 2 * radius

        player_shape = BulletCapsuleShape(radius, cylinder_height, ZUp)
        self.bullet_rigid_body = BulletRigidBodyNode('player')  # Store in self
        self.bullet_rigid_body.addShape(player_shape)

        self.bullet_node_path = base.render.attachNewNode(self.bullet_rigid_body)  # Store in self
        self.bullet_world.attachRigidBody(self.bullet_rigid_body)

        # Reparent the player model to the physics node
        self.player_model.reparentTo(self.bullet_node_path)
