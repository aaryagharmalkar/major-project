import React from "react";
import * as THREE from "three";

export default function Road({ road }) {
  const width = road.width_m || 10;
  const length = 50;

  return (
    <group
      position={[road.position.x, road.position.y, road.position.z]}
      rotation={[0, (road.heading_deg * Math.PI) / 180, 0]}
    >
      {/* Asphalt Surface */}
      <mesh position={[0, 0, 0]} receiveShadow>
        <boxGeometry args={[length, 0.04, width]} />
        <meshStandardMaterial
          color="#181a1f"
          roughness={0.88}
          metalness={0.1}
        />
      </mesh>

      {/* Road Curbs (Left & Right borders) */}
      <mesh position={[0, 0.04, width / 2]} receiveShadow>
        <boxGeometry args={[length, 0.08, 0.3]} />
        <meshStandardMaterial color="#333740" roughness={0.9} />
      </mesh>
      <mesh position={[0, 0.04, -width / 2]} receiveShadow>
        <boxGeometry args={[length, 0.08, 0.3]} />
        <meshStandardMaterial color="#333740" roughness={0.9} />
      </mesh>

      {/* Center Dashed Line (White/Yellow forensic markings) */}
      {Array.from({ length: 12 }).map((_, i) => {
        const posX = -length / 2 + 2 + i * 4;
        return (
          <mesh
            key={i}
            position={[posX, 0.025, 0]}
            rotation={[-Math.PI / 2, 0, 0]}
          >
            <planeGeometry args={[2.0, 0.18]} />
            <meshBasicMaterial
              color="#ffcc00"
              transparent
              opacity={0.75}
            />
          </mesh>
        );
      })}

      {/* Stop Line at intersection entrance */}
      <mesh
        position={[-6, 0.026, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <planeGeometry args={[0.4, width - 0.8]} />
        <meshBasicMaterial
          color="#ffffff"
          transparent
          opacity={0.8}
        />
      </mesh>
    </group>
  );
}