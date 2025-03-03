from panda3d.core import Vec3, WindowProperties


class Controls:
    def __init__(self, game):
        self.game = game
        self.keys = {"forward": False, "backward": False, "left": False, "right": False}

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
        self.game.accept("mouse1", self.center_mouse)
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
        self.game.camera.setPos(0, 0, 1.7)

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
