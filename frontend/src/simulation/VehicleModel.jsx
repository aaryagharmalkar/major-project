import React, { useMemo, useRef } from "react";
import { useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

function interpolatePosition(start, end, progress) {
  return {
    x: start.x + (end.x - start.x) * progress,
    y: start.y + (end.y - start.y) * progress,
    z: start.z + (end.z - start.z) * progress,
  };
}

export default function VehicleModel({ vehicle }) {
  const { scene } = useGLTF(vehicle.asset_path);

  const modelRef = useRef();

  // Clone the GLB so each vehicle gets its own instance
  const clonedScene = useMemo(() => {
    return scene.clone();
  }, [scene]);

  // ==========================================
  // NORMALIZE MODEL SIZE
  // ==========================================

  const normalizedScale = useMemo(() => {
    const box = new THREE.Box3().setFromObject(clonedScene);

    const size = new THREE.Vector3();

    box.getSize(size);

    // We assume the largest horizontal dimension
    // represents the vehicle's length.
    const currentLength = Math.max(size.x, size.z);

    // Approximate real-world motorcycle length
    const expectedLength = 2.0;

    if (!currentLength || currentLength <= 0) {
      return 1;
    }

    return expectedLength / currentLength;
  }, [clonedScene]);

  // ==========================================
  // CASE POSITIONS
  // ==========================================

  const startPosition = vehicle.start_position;

  const impactPosition = vehicle.impact_position;

  const finalPosition = vehicle.final_position;

  // ==========================================
  // ANIMATION
  // ==========================================

  useFrame((state) => {
    if (!modelRef.current) {
      return;
    }

    /*
     * For now the reconstruction automatically
     * plays when the page loads.
     *
     * Total duration = 10 seconds.
     *
     * 0 → 5 sec
     * Start → Impact
     *
     * 5 → 10 sec
     * Impact → Final
     */

    const time = Math.min(
      state.clock.elapsedTime,
      10
    );

    let position;

    if (time < 5) {
      const progress = time / 5;

      position = interpolatePosition(
        startPosition,
        impactPosition,
        progress
      );
    } else {
      const progress = (time - 5) / 5;

      position = interpolatePosition(
        impactPosition,
        finalPosition,
        Math.min(progress, 1)
      );
    }

    modelRef.current.position.set(
      position.x,
      position.y,
      position.z
    );
  });

  // ==========================================
  // RENDER
  // ==========================================

  return (
    <primitive
      ref={modelRef}
      object={clonedScene}
      position={[
        startPosition.x,
        startPosition.y,
        startPosition.z,
      ]}
      rotation={[
        ((vehicle.rotation?.x || 0) * Math.PI) / 180,
        ((vehicle.rotation?.y || 0) * Math.PI) / 180,
        ((vehicle.rotation?.z || 0) * Math.PI) / 180,
      ]}
      scale={[
        normalizedScale,
        normalizedScale,
        normalizedScale,
      ]}
    />
  );
}