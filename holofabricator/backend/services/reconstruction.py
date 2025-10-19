"""Utility functions for generating meshes from captured imagery."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import open3d as o3d
from PIL import Image

logger = logging.getLogger(__name__)


def generate_mesh_from_image(image_path: Path, output_dir: Path, scan_id: str) -> Optional[str]:
    """Generate a rudimentary mesh from a single RGB frame."""
    try:
        image = Image.open(image_path)
    except Exception as exc:  # pragma: no cover - defensive branch
        logger.error("Failed to open image %s: %s", image_path, exc)
        return None

    try:
        img_array = np.array(image)
        height, width = img_array.shape[:2]

        gray = np.mean(img_array, axis=2) / 255.0
        depth = 0.1 * (1 - gray)

        points = []
        colours = []
        scale = 0.01

        for y in range(0, height, 4):
            for x in range(0, width, 4):
                z = depth[y, x]
                points.append([x * scale, y * scale, float(z)])
                colours.append(img_array[y, x] / 255.0)

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.asarray(points))
        pcd.colors = o3d.utility.Vector3dVector(np.asarray(colours))
        pcd.estimate_normals()

        mesh, _densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd, depth=8
        )

        output_dir.mkdir(exist_ok=True)
        mesh_filename = f"{scan_id}_mesh.ply"
        mesh_path = output_dir / mesh_filename
        o3d.io.write_triangle_mesh(str(mesh_path), mesh)

        logger.info("Mesh generated for %s at %s", scan_id, mesh_path)
        return mesh_filename

    except Exception as exc:  # pragma: no cover - defensive branch
        logger.exception("Mesh generation failed for %s: %s", scan_id, exc)
        return None
