from panda3d.core import Vec3, NodePath, BitMask32, Point3
from panda3d.bullet import BulletRigidBodyNode, BulletSphereShape, BulletWorld

class Gun:
    def __init__(self, game, bullet_physics, bottle_manager, physics):
        self.physics = physics
        self.game = game
        self.bullet_physics = bullet_physics  # Bullet physics system reference
        self.bottle_manager = bottle_manager  # Reference to BottleManager
        self.fire_dir = game.model_loader.fire_dir  # Get fire_dir from ModelLoader
        self.load_sounds()
        self.setup_shooting()
        self.last_shot_time = 0
        self.cooldown_time = 0.2  # 200ms cooldown between shots

    def load_sounds(self):
        """Load shooting and shell sounds."""
        self.shoot_sound = self.game.loader.loadSfx("shoot.wav")
        self.shoot_sound.setVolume(1)
        self.pellet_sound = self.game.loader.loadSfx("shell.wav")
        self.pellet_sound.setVolume(1)
        self.break_sound = self.game.loader.loadSfx("break.wav")
        self.break_sound.setVolume(1)

    def setup_shooting(self):
        """Bind shooting action to the left mouse button."""
        self.game.accept("mouse1", self.shoot)

    def create_pellet(self):
        """Creates a physics-enabled pellet and returns its NodePath and BulletRigidBodyNode."""
        if not self.fire_dir or self.fire_dir.isEmpty():
            print("[DEBUG] Error: fire_dir not found in gun model!")
            return None, None

        # Create a Bullet physics body for the pellet
        pellet_rb = BulletRigidBodyNode("pellet")
        pellet_rb.setMass(3.0)
        pellet_rb.setKinematic(False)  # Enable physics-based movement
        pellet_shape = BulletSphereShape(2)
        pellet_rb.addShape(pellet_shape)
        pellet_rb.setIntoCollideMask(BitMask32.bit(1))  # Pellet collision group

        # Attach pellet to the scene
        pellet_rb_np = self.game.render.attachNewNode(pellet_rb)
        self.game.bullet_world.attachRigidBody(pellet_rb)

        # Load pellet model
        pellet_model = self.game.loader.loadModel("models/bullet.bam")
        pellet_model.setScale(1.4)
        pellet_model.reparentTo(pellet_rb_np)

        # Position pellet at the gun's fire point
        pellet_rb_np.setTransform(self.fire_dir.getTransform(self.game.render))

        # Shoot in the forward direction from the fire_dir quaternion
        shoot_direction = self.fire_dir.getQuat(self.game.render).getUp()
        pellet_speed = 512  # Adjust speed as needed
        pellet_rb.setLinearVelocity(shoot_direction * pellet_speed)

        print(f"[DEBUG] Pellet spawned at {pellet_rb_np.getPos(self.game.render)} with velocity {pellet_rb.getLinearVelocity()}")

        self.pellet_sound.play()
        return pellet_rb_np, pellet_rb

    def shoot(self):
        """Handles the shooting mechanism with cooldown."""
        current_time = self.game.task_mgr.globalClock.getFrameTime()
        if current_time - self.last_shot_time < self.cooldown_time:
            return  # Enforce cooldown

        pellet_np, pellet_rb = self.create_pellet()
        if pellet_rb:
            self.shoot_sound.play()
            self.last_shot_time = current_time
            self.setup_pellet_collision(pellet_np, pellet_rb)

    def setup_pellet_collision(self, pellet_np, pellet_rb):
        """Sets up collision detection for the pellet."""
        def collision_callback(result):
            if result.hasHit():
                hit_phys = result.getNode()
                hit_transform = hit_phys.getTransform()
                hit_position = hit_transform.getPos()

                print(f"[DEBUG] Collision detected with {hit_phys.getName()} at {hit_position}")

                if hit_phys and hit_phys.getName() == "Bottle":
                    print(f"[DEBUG] Bottle should break now.")
                    self.physics.break_bottle(hit_phys)
                    self.break_sound.play()

        if pellet_np and not pellet_np.isEmpty():
            pellet_np.node().setPythonTag("collision_callback", collision_callback)

        # Add task to check for collisions
        self.game.task_mgr.add(self.check_collision, "check_pellet_collision", extraArgs=[pellet_rb, pellet_np], appendTask=True)

    def check_collision(self, pellet_rb, pellet_np, task):
        """Checks for collisions between the pellet and all bottles in the world."""
        if not pellet_np or pellet_np.isEmpty():
            return task.done  # Stop task if the pellet has been removed

        start = pellet_np.getPos(self.game.render)  # Get pellet's world position
        forward_dir = pellet_np.getQuat(self.game.render).getUp()
        end = start + forward_dir * 4  # Move a small distance forward

        # Perform ray test for collision detection
        result = self.game.bullet_world.rayTestClosest(start, end)

        if result.hasHit():
            hit_node = result.getNode()  # Get the node that was hit
            hit_name = hit_node.getName() if hit_node else "Unknown"

            print(f"[DEBUG] Pellet collision test: Hit detected with {hit_name}")

            # Check if the hit node is a bottle and process accordingly
            if hit_name == "Bottle":
                # Get the collision point (Manifold Point)
                hit_point = result.getHitPoint()  # This gives the world position of the collision
                print(f"[DEBUG] Bottle detected at {hit_point}")
                self.physics.break_bottle(hit_node, hit_point)  # Pass the collision point to break_bottle
                self.break_sound.play()

        # Iterate through all bottles and check for collisions
        for bottle in self.bottle_manager.get_all_bottles():
            # You can adjust this to check for a direct collision with each bottle
            bottle_pos = bottle.node.getPos(self.game.render)  # Assuming 'node' is the NodePath of the bottle
            distance = (start - bottle_pos).length()
            
            # Define a threshold for collision detection (can be adjusted)
            if distance < 5:  # If the pellet is close enough to the bottle
                print(f"[DEBUG] Pellet detected collision with bottle at {bottle_pos}")
                hit_point = bottle_pos  # If we're directly checking, use the bottle's position
                self.physics.break_bottle(bottle, hit_point)  # Pass the hit point to break_bottle
                self.game.sfx.load_sound("bottle_break", "break.wav")
                self.game.sfx.play_sound("bottle_break", position=Point3(bottle_pos), volume=1.0)


        # Cleanup: Remove pellets if they travel too far
        if start.length() > 200:  # Arbitrary distance limit
            self.game.bullet_world.removeRigidBody(pellet_rb)
            pellet_np.removeNode()
            print("[DEBUG] Pellet removed after exceeding distance limit.")
            return task.done

        return task.cont  # Continue checking for collisions
