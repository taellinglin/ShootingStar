import random
import numpy as np
from panda3d.core import *
from panda3d.bullet import *
from scipy.spatial import Voronoi
from panda3d.bullet import BulletDebugNode
from panda3d.bullet import BulletCapsuleShape, BulletRigidBodyNode, ZUp, BulletConvexHullShape
from panda3d.core import Geom, GeomNode, GeomVertexData, GeomVertexFormat, GeomTriangles
from panda3d.core import GeomVertexWriter, GeomTristrips, GeomTriangles
from panda3d.core import LMatrix3f  # For single precision
from panda3d.core import LVecBase3f
from shapely.geometry import Polygon, box
import os

class BulletPhysics:
    def __init__(self, bullet_world, render):
        self.bullet_world = bullet_world
        self.render = render
        self.break_sound = base.loader.loadSfx("break.wav")

        # Debug node for visualizing the physics world
        self.debug_node = BulletDebugNode('Debug')
        self.debug_node.showWireframe(True)
        self.debug_np = self.render.attachNewNode(self.debug_node)
        self.bullet_world.setDebugNode(self.debug_node)
        # Start debug rendering task
    def update(self, task):
        # Step the physics simulation
        dt = globalClock.getDt()
        self.bullet_world.do_physics(dt)

        # The debug visualization is automatically updated during do_physics()
        return task.cont

    def setup_temple_collision(self, temple_model):
        """ Set up temple collision using Bullet physics. """
        # Create a BulletTriangleMesh to collect temple collision geometries
        mesh = BulletTriangleMesh()

        # Find all node paths associated with the temple model
        for np in temple_model.findAllMatches('**/temple'):
            # Ensure the node is a GeomNode (contains geometry)
            if isinstance(np.node(), GeomNode):
                for i in range(np.node().getGeomCount()):
                    geom = np.node().getGeom(i)
                    mesh.addGeom(geom)

        # Create a shape from the mesh (static since it's part of the environment)
        shape = BulletTriangleMeshShape(mesh, dynamic=False)

        # Create a BulletRigidBodyNode for the temple's collision body
        temple_phys = BulletRigidBodyNode('temple')
        temple_phys.addShape(shape)

        # Attach the physical representation of the temple to the model
        temple_model.attachNewNode(temple_phys)

        # Add the temple's collision body to the Bullet world
        self.bullet_world.attachRigidBody(temple_phys)


    def setup_player_physics(self, player_model):
        """Setup player physics with a capsule collision shape representing a 5-foot-tall player."""
        total_height_meters = 1.524  # 5 feet in meters
        radius = 0.3  # Adjust the radius as needed
        cylinder_height = total_height_meters - 2 * radius

        player_shape = BulletCapsuleShape(radius, cylinder_height, ZUp)
        player_phys = BulletRigidBodyNode('player')
        player_phys.addShape(player_shape)
        player_np = self.render.attachNewNode(player_phys)
        self.bullet_world.attachRigidBody(player_phys)

        # Reparent the player model to the physics node
        player_model.reparentTo(player_np)

    def setup_bottle_physics(self, bottle_model):
        """ Setup bottle collision physics, possibly for shattering. """
        shards = bottle_model.findAllMatches("**/bottle_shard*")
        if shards.isEmpty():
            shape = BulletSphereShape(1)
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
            shard_phys.setInertia(LVecBase3f(0.0,0.0,0.0))
             # Zero inertia to prevent immediate movement
            shard_phys.setDeactivationEnabled(False)  # Prevent auto-deactivation
            shard_phys.set_active(True)  # Activate the rigid body
  # Set to active state
            shard_phys.setLinearDamping(0)  # Disable linear damping
            shard_phys.setAngularDamping(0)  # Disable angular damping
            shard_phys.setGravity(LVector3(0,0,0))  # Disable gravity effect
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
            #shard_phys.setDamping(0.1, 0.1)  # Set damping factors
            phys_node = base.render.attachNewNode(shard_phys)
            self.bullet_world.attachRigidBody(shard_phys)
            phys_node.setPos(shard.getPos())
            phys_node.setHpr(shard.getHpr())

    def on_mouse_click(self, camera, render):
        """ Handle mouse click to break bottle on hit. """
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            near, far = Point3(), Point3()
            if base.cam.node().getLens().extrude(mpos, near, far):
                start, end = base.cam.getPos(render), base.cam.getPos(render) + (far - near).normalized() * 1000
                result = self.bullet_world.rayTestClosest(start, end)
                if result.hasHit() and result.getNode().getName() == "bottle":
                    self.break_bottle(result.getNode(), result.getHitPos())



    def clip_voronoi_region(self, region_points, bbox):
        """
        Given a list of (x, y) points (which may define an unbounded region),
        clip them to a bounding box (shapely Polygon) and return the resulting polygon's points.
        """
        try:
            poly = Polygon(region_points)
            # Clip the polygon to the bounding box
            clipped = poly.intersection(bbox)
            if clipped.is_empty:
                return None
            # Ensure the result is a polygon (could be a MultiPolygon)
            if clipped.geom_type == 'Polygon':
                return list(clipped.exterior.coords)
            else:
                # If it's a MultiPolygon, choose the largest one
                largest = max(clipped.geoms, key=lambda p: p.area)
                return list(largest.exterior.coords)
        except Exception as e:
            print(f"Error clipping region: {e}")
            return None

    def break_bottle(self, hit_phys, position):
        """Handle bottle breaking into shards using Voronoi tessellation,
        cutting the bottle's mesh and parenting the mesh pieces to the physics shards.
        Shards are placed at the hit position."""
        if not hasattr(hit_phys, 'destroyed') or hit_phys.destroyed == False or not hasattr(hit_phys, 'node'):
            print(f"Breaking bottle at position: {position}")

            # Extract the original mesh and texture from the hit_phys object
            original_mesh_node = hit_phys.node.findAllMatches('**/+GeomNode').getPath(0).node()
            original_texture = hit_phys.node.find('**/destructible').getTexture()  # Returns a Texture object or None
            original_color = hit_phys.node.find('**/destructible').getColor()  # Returns a Vec4 representing the color
            print(f"Original texture: {original_texture}")
            print(f"Original color: {original_color}")

            if original_texture:
                print("Texture found:", original_texture)
            else:
                print("No texture found. Using default color.")

            # Generate a set of random points for Voronoi tessellation.
            num_points = 128
            points = np.vstack(([0, 0, 0], np.random.uniform(-1, 1, (num_points - 1, 3))))

            print(f"Generated Voronoi points: {points}")

            # Define a bounding box in the XY plane (adjust as needed for your bottle's bounds).
            clip_bbox = box(-1, -1, 1, 1)
            vor = Voronoi(points)
            print(f"Voronoi regions: {len(vor.regions)} regions generated.")

            for i, region in enumerate(vor.regions):
                print(f"Processing region {i}: {region}")
                if not region:
                    print(f"Skipping region {i} (empty region).")
                    continue

                # Prepare to collect 2D points (only XY) from the region.
                region_pts_2d = []
                if -1 in region:
                    print(f"Region {i} is unbounded; attempting to clip.")
                    for idx in region:
                        if idx == -1 or idx >= len(points):
                            continue
                        region_pts_2d.append((points[idx][0], points[idx][1]))
                    clipped_coords = self.clip_voronoi_region(region_pts_2d, clip_bbox)
                    if clipped_coords is None:
                        print(f"Skipping region {i} after clipping returned no valid polygon.")
                        continue
                    # Convert the clipped polygon's vertices back to 3D (using Z = 0)
                    final_region = [(x, y, 0.0) for (x, y) in clipped_coords]
                else:
                    final_region = []
                    for idx in region:
                        if 0 <= idx < len(points):
                            final_region.append(tuple(points[idx]))
                    if not final_region:
                        print(f"Skipping region {i} because no valid 3D points could be extracted.")
                        continue

                print(f"Region {i} will use {len(final_region)} vertices after processing.")

                # Create GeomVertexData for the shard's geometry.
                vertex_data = GeomVertexData("shard", GeomVertexFormat.getV3(), Geom.UHStatic)
                vertex_writer = GeomVertexWriter(vertex_data, "vertex")
                for pt in final_region:
                    vertex_writer.addData3f(*pt)
                if vertex_data.getNumRows() == 0:
                    print(f"Skipping region {i} because no vertices were written after clipping.")
                    continue

                # Create GeomTriangles (using sequential indices).
                geom_triangles = GeomTriangles(Geom.UHStatic)
                num_vertices = vertex_data.getNumRows()
                print(f"Region {i} has {num_vertices} vertices.")
                for j in range(0, num_vertices - 2, 3):
                    geom_triangles.addVertices(j, j + 1, j + 2)
                if geom_triangles.getNumVertices() < 3:
                    print(f"Skipping region {i} due to invalid triangle data (less than 3 vertices).")
                    continue

                # Assemble the geometry.
                geom = Geom(vertex_data)
                geom.addPrimitive(geom_triangles)
                if geom.getVertexData() is None or geom.getNumPrimitives() == 0 or geom.isEmpty():
                    print(f"Skipping region {i} due to invalid geometry.")
                    continue

                # Create a visual GeomNode for the shard and set its texture and color.
                geom_node = GeomNode(f"shard_geom_{i}")
                geom_node.addGeom(geom)
                geom_node_path = base.render.attachNewNode(geom_node)
                if original_texture:
                    geom_node_path.setTexture(original_texture)
                if original_color:
                    geom_node_path.setColorScale(original_color)

                # Create a BulletConvexHullShape and add the shard geometry for collision.
                shape = BulletConvexHullShape()
                shape.addGeom(geom)
                piece_phys = BulletRigidBodyNode(f"piece_{i}")
                piece_phys.addShape(shape)
                piece_phys.setMass(0.1)
                piece_phys.setInertia(LVecBase3f(0.0, 0.0, 0.0))
                piece_phys.setDeactivationEnabled(False)
                piece_phys.setLinearDamping(0)
                piece_phys.setAngularDamping(0)
                piece_phys.setGravity(LVector3(0, 0, 0))
                piece_phys.setFriction(0.5)
                piece_phys.setRestitution(0.5)
                piece_phys.setLinearFactor(Vec3(1, 1, 1))
                piece_phys.setAngularFactor(Vec3(1, 1, 1))
                impulse = Vec3(*np.random.uniform(-10, 10, 3))
                print(f"Applying central impulse to piece {i}: {impulse}")
                piece_phys.applyCentralImpulse(impulse)

                # Create the physics node and set its position at the hit point.
                phys_node = base.render.attachNewNode(piece_phys)
                phys_node.setName(f"piece_{i}")
                offset = Vec3(*np.random.uniform(-0.1, 0.1, 3))
                phys_node.setPos(position + offset)

                # Parent the visual shard to the physics node so it moves with it.
                geom_node_path.reparentTo(phys_node)

                print(f"Piece {i} attached to the scene at position: {phys_node.getPos()}")
                self.bullet_world.attachRigidBody(piece_phys)
                print(f"Piece {i} added to the Bullet physics world.")

            # Remove the original bottle's mesh from the scene.
            print("Removing original hit_phys object.")
            hit_phys.cleanup()
