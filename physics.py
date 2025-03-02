import random
import numpy as np
from panda3d.core import *
from panda3d.bullet import *
from scipy.spatial import Voronoi


class BulletPhysics:
    def __init__(self, bullet_world, render):
        self.bullet_world = bullet_world
        self.render = render
        self.break_sound = base.loader.loadSfx("break.wav")
        
        self.debug_node = BulletDebugNode('Debug')
        self.debug_node.showWireframe(True)
        self.debug_np = self.render.attachNewNode(self.debug_node)
        self.bullet_world.setDebugNode(self.debug_node)

    def setup_ground_collision(self, ground_model):
        mesh = BulletTriangleMesh()
        for geom in ground_model.findAllMatches('**/groundcol').getGeoms():
            mesh.addGeom(geom)
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        ground_phys = BulletRigidBodyNode('ground')
        ground_phys.addShape(shape)
        ground_model.attachNewNode(ground_phys)
        self.bullet_world.attachRigidBody(ground_phys)

    def setup_bottle_physics(self, bottle_model):
        shards = bottle_model.findAllMatches("**/bottle_shard*")
        if shards.isEmpty():
            shape = BulletSphereShape(0.5)
            bottle_phys = BulletRigidBodyNode('bottle')
            bottle_phys.addShape(shape)
            bottle_model.attachNewNode(bottle_phys)
            self.bullet_world.attachRigidBody(bottle_phys)
            return
        
        for shard in shards:
            shape = BulletConvexHullShape()
            for geom in shard.node().getGeoms():
                shape.addGeom(geom)
            shard_phys = BulletRigidBodyNode(f"shard_{shard.getName()}")
            shard_phys.addShape(shape)
            shard_phys.setMass(0.1)
            shard_phys.setInertia(DMatrix3(0, 0, 0, 0, 0, 0))  # Zero inertia to prevent immediate movement
            shard_phys.setDeactivationEnabled(False)  # Prevent auto-deactivation
            shard_phys.setActivationState(4)  # Set to active state
            shard_phys.setLinearDamping(0)  # Disable linear damping
            shard_phys.setAngularDamping(0)  # Disable angular damping
            shard_phys.setGravityEnable(False)  # Disable gravity effect
            shard_phys.setFriction(0.5)  # Set appropriate friction
            shard_phys.setRestitution(0.5)  # Set appropriate restitution
            shard_phys.setRollingFriction(0.1)  # Set rolling friction
            shard_phys.setSpinningFriction(0.1)  # Set spinning friction
            shard_phys.setCcdMotionThreshold(0.1)  # Set CCD motion threshold
            shard_phys.setCcdSweptSphereRadius(0.2)  # Set CCD swept sphere radius
            shard_phys.setContactProcessingThreshold(0.01)  # Set contact processing threshold
            shard_phys.setLinearSleepingThreshold(0.8)  # Set linear sleeping threshold
            shard_phys.setAngularSleepingThreshold(1.0)  # Set angular sleeping threshold
            shard_phys.setLinearFactor(Vec3(1, 1, 1))  # Enable linear movement
            shard_phys.setAngularFactor(Vec3(1, 1, 1))  # Enable angular movement
            shard_phys.setDamping(0.1, 0.1)  # Set damping factors
            phys_node = base.render.attachNewNode(shard_phys)
            self.bullet_world.attachRigidBody(shard_phys)
            phys_node.setPos(shard.getPos())
            phys_node.setHpr(shard.getHpr())

    def on_mouse_click(self, camera, render):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            near, far = Point3(), Point3()
            if base.cam.node().getLens().extrude(mpos, near, far):
                start, end = base.cam.getPos(render), base.cam.getPos(render) + (far - near).normalized() * 1000
                result = self.bullet_world.rayTestClosest(start, end)
                if result.hasHit() and result.getNode().getName() == "bottle":
                    self.break_bottle(result.getNode(), result.getHitPos())

    def break_bottle(self, hit_phys, position):
        points = np.vstack(([0, 0, 0], np.random.uniform(-0.5, 0.5, (12, 3))))
        vor = Voronoi(points)

        for i, region in enumerate(vor.regions):
            if not region or -1 in region:
                continue
            
            shape = BulletConvexHullShape()
            for idx in region:
                shape.addGeom(GeomVertexData("shard", GeomVertexFormat.getV3(), Geom.UHStatic))
            
            piece_phys = BulletRigidBodyNode(f"piece_{i}")
            piece_phys.addShape(shape)
            piece_phys.setMass(0.1)
            piece_phys.setInertia(DMatrix3(0, 0, 0, 0, 0, 0))  # Zero inertia to prevent immediate movement
            piece_phys.setDeactivationEnabled(False)  # Prevent auto-deactivation
            piece_phys.setActivationState(4)  # Set to active state
            piece_phys.setLinearDamping(0)  # Disable linear damping
            piece_phys.setAngularDamping(0)  # Disable angular damping
            piece_phys.setGravityEnable(False)  # Disable gravity effect
            piece_phys.setFriction(0.5)  # Set appropriate friction
            piece_phys.setRestitution(0.5)  # Set appropriate restitution
            piece_phys.setLinearFactor(Vec3(1, 1, 1))  # Enable linear movement
            piece_phys.setAngularFactor(Vec3(1, 1, 1))  # Enable angular movement
            piece_phys.setDamping(0.1, 0.1)  # Set damping factors
            piece_phys.setPos(position + Vec3(*np.random.uniform(-0.3, 0.3, 3)))
            piece_phys.applyCentralImpulse(Vec3(*np.random.uniform(-10, 10, 3)))
            phys_node = base.render.attachNewNode(piece_phys)
            self.bullet_world.attachRigidBody(piece_phys)

 
