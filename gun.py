from panda3d.core import Vec3, NodePath, BitMask32
from panda3d.bullet import BulletRigidBodyNode, BulletSphereShape, BulletWorld

class Gun:
    def __init__(self, game, bullet_physics, bottle_manager):
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
        pellet_rb.setMass(1.0)
        pellet_rb.setKinematic(False)  # Enable physics-based movement
        pellet_shape = BulletSphereShape(0.1)
        pellet_rb.addShape(pellet_shape)
        # In create_pellet method, set the collision mask for the pellet
        pellet_rb.setIntoCollideMask(BitMask32.bit(1))  # This will make the pellet collide with everything

        # In BottleManager or wherever you create the bottle physics object
        

        # Attach pellet to the scene
        pellet_rb_np = self.game.render.attachNewNode(pellet_rb)
        self.game.bullet_world.attachRigidBody(pellet_rb)

        # Load pellet model
        pellet_model = self.game.loader.loadModel("models/bullet.bam")
        pellet_model.setScale(0.8)
        pellet_model.reparentTo(pellet_rb_np)

        # Position pellet at the gun's fire point
        pellet_rb_np.setTransform(self.fire_dir.getTransform(self.game.render))

        # Shoot in the forward direction from the fire_dir quaternion
        shoot_direction = self.fire_dir.getQuat(self.game.render).getUp()
        pellet_speed = 50  # Adjust speed as needed
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
                print(f"[DEBUG] Collision detected with {hit_phys.getName()}")
                if hit_phys and hit_phys.getName() == "bottle":
                    # Break the bottle on hit, using BottleManager
                    hit_transform = hit_phys.getTransform()
                    hit_position = hit_transform.getPos()
                    print(f"[DEBUG] Bottle hit at position {hit_position}")
                    self.bottle_manager.break_bottle(hit_phys, hit_position)  # Call break_bottle in bottle_manager.py
                    self.break_sound.play()

        if pellet_np and not pellet_np.isEmpty():
            pellet_np.node().setPythonTag("collision_callback", collision_callback)

        # Add task to check for collisions
        self.game.task_mgr.add(self.check_collision, "check_pellet_collision", extraArgs=[pellet_rb, pellet_np], appendTask=True)

    def check_collision(self, pellet_rb, pellet_np, task):
        """Checks for collisions between the pellet and objects in the world."""
        if not pellet_np or pellet_np.isEmpty():
            return task.done  # Stop task if the pellet has been removed

        start = pellet_np.getPos(self.game.render)  # Get pellet's world position
        forward_dir = pellet_np.getQuat(self.game.render).getUp()
        end = start + forward_dir * 0.1  # Move a small distance forward

        # Perform ray test for collision detection
        result = self.game.bullet_world.rayTestClosest(start, end)

        if result.hasHit():
            hit_node = result.getNode()  # Get the node that was hit
            hit_name = hit_node.getName() if hit_node else "Unknown"

            print(f"[DEBUG] Pellet collision test: Hit detected with {hit_name}")
            
            if hit_name == "pellet":
                print("[DEBUG] Pellet collided with itself! Ignoring.")
                return task.cont  # Ignore self-collision, continue checking

            # Trigger collision callback if a valid collision occurs
            collision_callback = pellet_np.node().getPythonTag("collision_callback")
            if collision_callback:
                collision_callback(result)

                # Remove pellet after collision
                self.game.bullet_world.removeRigidBody(pellet_rb)
                pellet_np.removeNode()
                print(f"[DEBUG] Pellet removed after hitting {hit_name}")
                return task.done  # End task for this pellet

        # Cleanup: Remove pellets if they travel too far
        if start.length() > 200:  # Arbitrary distance limit
            self.game.bullet_world.removeRigidBody(pellet_rb)
            pellet_np.removeNode()
            print("[DEBUG] Pellet removed after exceeding distance limit.")
            return task.done

        return task.cont  # Continue checking for collisions
