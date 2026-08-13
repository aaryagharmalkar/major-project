import React from "react";

export default function Road({ road }) {
  const width = road.width_m || 10;

  return (
    <mesh
      position={[
        road.position.x,
        road.position.y,
        road.position.z,
      ]}
      rotation={[
        0,
        (road.heading_deg * Math.PI) / 180,
        0,
      ]}
    >
      <boxGeometry args={[40, 0.08, width]} />

      <meshStandardMaterial
        color="#292929"
        roughness={0.95}
      />
    </mesh>
  );
}