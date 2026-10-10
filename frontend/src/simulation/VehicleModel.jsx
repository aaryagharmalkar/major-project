import React, { useMemo, useRef } from "react";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";
import RiderAvatar from "./RiderAvatar";
import { resolveEntityWaypoints, sampleEntityState } from "./kinematics";

export default function VehicleModel({
  vehicle,
  timeline = [],
  currentTime = 0,
  isSelected = false,
  onSelect,
}) {
  const assetPath = vehicle.asset_path || "/assets/vehicles/bajaj_pulsar_150.glb";
  const { scene } = useGLTF(assetPath);
  const modelRef = useRef();

  // Clone and automatically center the 3D GLB mesh so (0, 0, 0) is the true origin
  const { clonedScene, normalizedScale } = useMemo(() => {
    const cloned = scene.clone();
    const box = new THREE.Box3().setFromObject(cloned);
    const center = new THREE.Vector3();
    box.getCenter(center);
    const size = new THREE.Vector3();
    box.getSize(size);

    // Re-center internal mesh offset to exact bounding center on the ground
    cloned.position.x = -center.x;
    cloned.position.y = -box.min.y;
    cloned.position.z = -center.z;

    const currentLength = Math.max(size.x, size.z);
    const expectedLength = vehicle.type === "four_wheeler" ? 4.2 : 2.0;
    const scale =
      !currentLength || currentLength <= 0
        ? 1
        : expectedLength / currentLength;

    return { clonedScene: cloned, normalizedScale: scale };
  }, [scene, vehicle.type]);

  const waypoints = useMemo(() => resolveEntityWaypoints(vehicle, timeline), [vehicle, timeline]);
  const isVehicle1 = vehicle.id === "vehicle_1";

  // Dynamic Waypoint Kinematics
  const { position, rotation, activeSegmentIndex } = useMemo(() => {
    const sampled = sampleEntityState(waypoints, currentTime);
    let rot = { ...sampled.rotation };
    let pos = { ...sampled.position };

    // Post-impact shock & tilt logic (after first impact waypoint)
    if (currentTime > 5.0) {
      const dt = currentTime - 5.0;
      const progress = Math.min(1, dt / 5.0);
      const slideProgress = 1 - Math.pow(1 - progress, 2);

      // 1. High-Frequency Contact Shock & Wobble (0.0s to 1.2s post-impact)
      if (dt <= 1.2) {
        const envelope = Math.exp(-4.5 * dt);
        const freq = 28;
        const wobbleYaw = Math.sin(freq * dt) * 0.12 * envelope;
        const wobbleRoll = Math.cos(freq * dt * 0.8) * 0.15 * envelope;

        rot.y += isVehicle1 ? wobbleYaw : -wobbleYaw;
        rot.z += wobbleRoll;
      }

      // 2. Progressive Chassis Deflection & Resting Tilt
      let tiltAmount = 0;
      if (isVehicle1) {
        tiltAmount = slideProgress * 0.55;
        rot.z += tiltAmount;
        rot.y += slideProgress * 0.2;
      } else {
        tiltAmount = slideProgress * 1.2;
        rot.x += tiltAmount;
        rot.y += slideProgress * 0.35;
      }

      // 3. Ground Plane Clamping
      const bikeHeightOffset = Math.sin(Math.abs(tiltAmount)) * 0.35;
      pos.y = Math.max(0.04, bikeHeightOffset);
    }

    return { position: pos, rotation: rot, activeSegmentIndex: sampled.activeSegmentIndex };
  }, [waypoints, currentTime, isVehicle1]);

  const modelName = (vehicle.model || vehicle.make || "").toLowerCase();
  const isTwoWheeler =
    vehicle.type === "two_wheeler" ||
    !vehicle.type ||
    modelName.includes("pulsar") ||
    modelName.includes("bike") ||
    modelName.includes("activa") ||
    modelName.includes("scooter");

  const isScooter =
    !isVehicle1 &&
    (modelName.includes("activa") ||
      vehicle.asset_path?.includes("vespa") ||
      modelName.includes("scooter"));

  const riderColor = isVehicle1 ? "#00f0ff" : "#ffb700";
  const riderRotationY = isVehicle1 ? -Math.PI / 2 : 0;
  const seatOffset = isVehicle1 ? [0, 0.62, 0] : [0, 0.68, -0.05];
  const fallProgress = currentTime <= 5.0 ? 0 : Math.min(1, (currentTime - 5.0) / 4.0);

  return (
    <group
      onClick={(e) => {
        e.stopPropagation();
        if (onSelect) onSelect(vehicle.id);
      }}
    >
      {/* 3D Vehicle & Mounted Rider Group */}
      <group position={[position.x, position.y, position.z]}>
        {/* Scaled & Centered 3D Model with Ground Clamped Rotation */}
        <group
          rotation={[rotation.x, rotation.y, rotation.z]}
          scale={[normalizedScale, normalizedScale, normalizedScale]}
        >
          <primitive ref={modelRef} object={clonedScene} />
        </group>

        {/* Mount Rider Avatar only on Two-Wheelers */}
        {isTwoWheeler && (
          <RiderAvatar
            color={riderColor}
            isScooter={isScooter}
            vehicleRotation={rotation}
            riderRotationY={riderRotationY}
            seatOffset={seatOffset}
            fallProgress={fallProgress}
            isVictim={!isVehicle1}
          />
        )}
      </group>

      {/* Detective HUD Vehicle Target Reticle / Highlight Halo */}
      <mesh
        position={[position.x, 0.05, position.z]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <ringGeometry args={[0.9, 0.98, 32]} />
        <meshBasicMaterial
          color={isSelected ? "#00f0ff" : "#ffb700"}
          transparent
          opacity={isSelected ? 0.9 : 0.4}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Floating Target ID Tag */}
      <mesh position={[position.x, 1.8, position.z]}>
        <sphereGeometry args={[0.06, 12, 12]} />
        <meshBasicMaterial color={isSelected ? "#00f0ff" : "#ffb700"} />
      </mesh>
    </group>
  );
}