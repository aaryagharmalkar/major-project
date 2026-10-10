import React, { useMemo } from "react";
import * as THREE from "three";
import { resolveEntityWaypoints, sampleEntityState } from "./kinematics";

export default function PersonModel({
  person,
  timeline = [],
  currentTime = 0,
  isSelected = false,
  onSelect,
}) {
  const waypoints = useMemo(() => resolveEntityWaypoints(person, timeline), [person, timeline]);
  const { position, rotation } = useMemo(
    () => sampleEntityState(waypoints, currentTime),
    [waypoints, currentTime]
  );

  const role = (person.role || "person").toLowerCase();
  const roleColor =
    role.includes("victim")
      ? "#ff0055"
      : role.includes("suspect") || role.includes("accused") || role.includes("shooter")
      ? "#ffb700"
      : "#00f0ff"; // witness / police / bystander

  const suitMaterial = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: "#18202c",
        roughness: 0.6,
        metalness: 0.2,
      }),
    []
  );

  const accentMaterial = useMemo(
    () =>
      new THREE.MeshBasicMaterial({
        color: roleColor,
      }),
    [roleColor]
  );

  return (
    <group
      position={[position.x, Math.max(0.04, position.y), position.z]}
      rotation={[rotation.x, rotation.y, rotation.z]}
      onClick={(e) => {
        e.stopPropagation();
        if (onSelect) onSelect(person.id);
      }}
    >
      {/* 1. Standing / Walking Mannequin Mesh */}
      <group position={[0, 0.85, 0]}>
        {/* Head & Visor */}
        <mesh position={[0, 0.65, 0]} material={suitMaterial}>
          <sphereGeometry args={[0.13, 16, 16]} />
        </mesh>
        <mesh position={[0, 0.67, 0.09]} material={accentMaterial}>
          <boxGeometry args={[0.14, 0.06, 0.04]} />
        </mesh>

        {/* Torso & Identification Tag */}
        <mesh position={[0, 0.25, 0]} material={suitMaterial}>
          <boxGeometry args={[0.3, 0.42, 0.18]} />
        </mesh>
        <mesh position={[0, 0.32, 0.095]} material={accentMaterial}>
          <planeGeometry args={[0.14, 0.05]} />
        </mesh>

        {/* Arms */}
        <mesh position={[-0.2, 0.22, 0]} material={suitMaterial}>
          <cylinderGeometry args={[0.04, 0.035, 0.4, 8]} />
        </mesh>
        <mesh position={[0.2, 0.22, 0]} material={suitMaterial}>
          <cylinderGeometry args={[0.04, 0.035, 0.4, 8]} />
        </mesh>

        {/* Legs */}
        <mesh position={[-0.09, -0.42, 0]} material={suitMaterial}>
          <cylinderGeometry args={[0.048, 0.04, 0.45, 8]} />
        </mesh>
        <mesh position={[0.09, -0.42, 0]} material={suitMaterial}>
          <cylinderGeometry args={[0.048, 0.04, 0.45, 8]} />
        </mesh>
      </group>

      {/* Target Reticle Halo */}
      <mesh position={[0, 0.03, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.4, 0.48, 24]} />
        <meshBasicMaterial
          color={isSelected ? "#00f0ff" : roleColor}
          transparent
          opacity={isSelected ? 0.9 : 0.5}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Floating Role Marker Pin */}
      <mesh position={[0, 1.85, 0]}>
        <sphereGeometry args={[0.05, 12, 12]} />
        <meshBasicMaterial color={roleColor} />
      </mesh>
    </group>
  );
}
