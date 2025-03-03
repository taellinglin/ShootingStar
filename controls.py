from panda3d.core import Vec3
from direct.interval.IntervalGlobal import LerpPosInterval


class Controls:
    def __init__(self, game, gun, player_node_path):
        self.game = game
        self.gun = gun
        
        self.player = player_node_path  # Reference to the player's NodePath
        self.keys = {"forward": False, "backward": False, "left": False, "right": False}
        self.gun_aiming = False  # To track if the gun is aimed down the sights
    def shoot_gun(self):
        self.gun.shoot()
        
    def setup_controls(self):
        """Set up player movement and mouse look controls."""
        self.game.accept("w", self.set_key, ["forward", True])
        self.game.accept("w-up", self.set_key, ["forward", False])
        self.game.accept("s", self.set_key, ["backward", True])
        self.game.accept("s-up", self.set_key, ["backward", False])
        self.game.accept("a", self.set_key, ["left", True])
        self.game.accept("a-up", self.set_key, ["left", False])
        self.game.accept("d", self.set_key, ["right", True])
        self.game.accept("d-up", self.set_key, ["right", False])

        # Mouse look
        self.game.disableMouse()
        base.accept("mouse1", self.shoot_gun)  # Now this triggers the shoot() method of Gun
        

        # Right Mouse Button (RMB) aiming down sights
        base.accept("mouse3-down", self.aim_down_sights, [True])
        base.accept("mouse3-up", self.aim_down_sights, [False])
        #self.game.accept("mouse1", self.center_mouse)
        self.game.taskMgr.add(self.mouse_look, "mouse_look")

        # Set up player physics
        self.setup_player()



    def setup_player(self):
        """Create a physics-based player with a kinematic body."""
        from panda3d.bullet import BulletRigidBodyNode, BulletSphereShape

        player_shape = BulletSphereShape(1)
        self.player_node = BulletRigidBodyNode("player")
        self.player_node.addShape(player_shape)
        self.player_node.setMass(70)
        self.player_node.setAngularFactor(0)
        self.player_node.setKinematic(True)

        self.player_np = self.game.render.attachNewNode(self.player_node)
        self.player_np.setPos(0, -30, 5)
        self.game.bullet_world.attachRigidBody(self.player_node)

        # Attach the camera to the player node
        self.game.camera.reparentTo(self.player_np)
        self.game.camera.setPos(0, 0, 2)

        # Assuming gun model is attached to the player
        self.original_gun_pos = self.game.model_loader.gun_mount.getPos()  # Corrected line, use player node instead of rigid body node

    def set_key(self, key, value):
        """Handle key press events."""
        self.keys[key] = value

    def update(self, dt):
        """Update player movement each frame."""
        speed = 50 * dt
        move_vec = Vec3(0, 0, 0)

        if self.keys["forward"]:
            move_vec.y += speed
        if self.keys["backward"]:
            move_vec.y -= speed
        if self.keys["left"]:
            move_vec.x -= speed
        if self.keys["right"]:
            move_vec.x += speed

        move_vec = self.player_np.getQuat().xform(move_vec)
        new_pos = self.player_np.getPos() + move_vec
        self.player_np.setPos(new_pos)

    def mouse_look(self, task):
        """Handle mouse look for aiming."""
        md = self.game.win.getPointer(0)
        x, y = md.getX(), md.getY()
        center_x = self.game.win.getXSize() // 2
        center_y = self.game.win.getYSize() // 2

        if x != center_x or y != center_y:
            dx = (x - center_x) * 0.1
            dy = (y - center_y) * 0.1
            self.player_np.setH(self.player_np.getH() - dx)
            self.game.camera.setP(self.game.camera.getP() - dy)
            self.game.win.movePointer(0, center_x, center_y)
        return task.cont

    def center_mouse(self):
        """Re-center the mouse on click."""
        center_x = self.game.win.getXSize() // 2
        center_y = self.game.win.getYSize() // 2
        self.game.win.movePointer(0, center_x, center_y)

    def aim_down_sights(self, is_aiming):
        print(f"Aiming down sights: {is_aiming}")
        
        if is_aiming and not self.gun_aiming:
            # Gun is now aiming, move it to the camera’s front view
            self.gun_aiming = True
            # Calculate the position directly in front of the camera (adjust values for correct alignment)
            aim_pos = base.camera.getPos() + base.camera.getQuat().getUp()+2# Adjust 2 for distance
            # Optionally adjust the Z-offset if necessary to match the gun's height
            aim_pos.setZ(aim_pos.getZ() - 0.2)  # Adjust this value for the aiming height
            aim_anim = LerpPosInterval(self.game.model_loader.gun, 0.3, aim_pos)
            aim_anim.start()

        elif not is_aiming and self.gun_aiming:
            # Gun is no longer aiming, reset to original position
            self.gun_aiming = False
            reset_anim = LerpPosInterval(self.game.model_loader.gun, 0.3, self.original_gun_pos)
            reset_anim.start()
