import os
import random
import numpy as np
from panda3d.core import *
from panda3d.bullet import *
from scipy.spatial import Voronoi

class BulletPhysics:
    def __init__(self, bullet_world, render):
        self.bullet_world = bullet_world
        self.render = render
        self.break_sound = None

        # Enable Bullet Debugging
        self.debug_node = BulletDebugNode('Debug')
        self.debug_node.showWireframe(True)
        self.debug_node.showConstraints(True)
        self.debug_node.showBoundingBoxes(True)
        self.debug_node.showNormals(True)
        self.debug_np = self.render.attachNewNode(self.debug_node)
        self.bullet_world.setDebugNode(self.debug_node)

    def setup_ground_collision(self, ground_model):
        """Setup collision for the ground using a BulletTriangleMeshShape."""
        mesh = BulletTriangleMesh()
        for geom_node in ground_model.findAllMatches('**/groundcol'):
            for geom in geom_node.node().getGeoms():
                mesh.addGeom(geom)
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        ground_phys = BulletRigidBodyNode('ground')
        ground_phys.addShape(shape)
        ground_phys.setMass(0)  
        ground_phys.setCollideMask(BitMask32.bit(1))
        ground_node = ground_model.attachNewNode(ground_phys)
        self.bullet_world.attachRigidBody(ground_phys)

    def setup_bottle_physics(self, bottle_model):
        """Setup proper collision shape for prefractured bottles."""
        # Create a list to store the bottle shards
        bottle_shards = []
        
        # Find all the prefractured bottle parts by their names
        shard_nodes = bottle_model.findAllMatches("**/bottle_shard*")
        if shard_nodes.isEmpty():
            print("No prefractured shards found for bottle, defaulting to sphere collision.")
            shape = BulletSphereShape(0.5)  # Fallback if no collision shape is found
            bottle_phys = BulletRigidBodyNode('bottle')
            bottle_phys.addShape(shape)
            bottle_phys.setMass(1.0)
            bottle_phys.setCollideMask(BitMask32.bit(1))
            phys_node = bottle_model.attachNewNode(bottle_phys)
            self.bullet_world.attachRigidBody(bottle_phys)
            return phys_node
        else:
            for shard in shard_nodes:
                # For each shard, we need to check if it has a prefractured geometry
                shard_geom = shard.node()
                if shard_geom:
                    # Create a convex hull shape for each shard
                    shape = BulletConvexHullShape()

                    # Loop through the geometries of the shard
                    for geom_node in shard_geom.getGeoms():
                        shape.addGeom(geom_node)

                    # Set up the physics body for this shard
                    shard_phys = BulletRigidBodyNode(f"shard_{shard.getName()}")
                    shard_phys.addShape(shape)
                    shard_phys.setMass(0.1)
                    shard_phys.setCollideMask(BitMask32.bit(1))
                    shard_phys.setFriction(0.5)
                    shard_phys.setRestitution(0.3)  # Adjust restitution for bounce

                    # Attach the shard to the world
                    shard_node_path = bottle_model.attachNewNode(shard_phys)
                    self.bullet_world.attachRigidBody(shard_phys)

                    # Store the shard node
                    bottle_shards.append(shard_node_path)

            print(f"Setup {len(bottle_shards)} prefractured bottle shards with collision.")
            return bottle_shards

    def on_mouse_click(self, camera, render):
        """Handle raycasting when clicking the mouse."""
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            near_point, far_point = Point3(), Point3()
            if base.cam.node().getLens().extrude(mpos, near_point, far_point):
                near_point_world = base.cam.getMat(render).xformPoint(near_point)
                far_point_world = base.cam.getMat(render).xformPoint(far_point)
                direction = (far_point_world - near_point_world).normalized()
                start = base.cam.getPos(render)
                end = start + direction * 1000
                result = self.bullet_world.rayTestClosest(start, end)

                if result.hasHit():
                    hit_phys = result.getNode()
                    print(f"Ray hit: {hit_phys.getName()} at {result.getHitPos()}")
                    if hit_phys.getName() == "bottle":
                        self.break_bottle(hit_phys, result.getHitPos())

    def break_bottle(self, hit_phys, position):
        """Break the bottle into Voronoi-generated shards and apply random forces."""
        num_pieces = 12
        points = np.random.uniform(-0.5, 0.5, (num_pieces, 3))  # Generate fracture points
        points = np.vstack(([0, 0, 0], points))  # Ensure central fracture point
        vor = Voronoi(points)

        print(f"Bottle breaking at {position} into {num_pieces} shards.")

        for i, region in enumerate(vor.regions):
            if not region or -1 in region:
                continue  

            vdata = GeomVertexData("shard", GeomVertexFormat.getV3(), Geom.UHStatic)
            vertex_writer = GeomVertexWriter(vdata, "vertex")
            tris = GeomTriangles(Geom.UHStatic)

            for j, idx in enumerate(region):
                point = vor.vertices[idx]
                vertex_writer.addData3f(*point)

                if j >= 2:
                    tris.addVertices(0, j - 1, j)
                    tris.closePrimitive()

            geom = Geom(vdata)
            geom.addPrimitive(tris)
            geom_node = GeomNode(f"shard_{i}")
            geom_node.addGeom(geom)

            # Bullet Collision Shape
            shape = BulletConvexHullShape()
            shape.addGeom(geom)

            piece_phys = BulletRigidBodyNode(f"piece_{i}")
            piece_phys.addShape(shape)
            piece_phys.setMass(0.1)
            piece_phys.setCollideMask(BitMask32.bit(1))
            phys_node = base.render.attachNewNode(piece_phys)
            self.bullet_world.attachRigidBody(piece_phys)

            phys_node.setPos(position + Vec3(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)))

            shard_model = base.render.attachNewNode(geom_node)
            shard_model.reparentTo(phys_node)

            impulse = Vec3(random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(5, 15))
            piece_phys.applyCentralImpulse(impulse)
            print(f"Shard {i} impulse: {impulse}")

        if not self.break_sound:
            self.break_sound = base.loader.loadSfx("break.wav")
        self.break_sound.set3dAttributes(position.x, position.y, position.z, 0, 0, 0)
        self.break_sound.play()
        print(f"Bottle shattered into {num_pieces} Voronoi shards!")

    def debug_collision(self):
        """Toggle debug rendering of collision shapes."""
        if self.debug_np.isHidden():
            self.debug_np.show()
        else:
            self.debug_np.hide()
