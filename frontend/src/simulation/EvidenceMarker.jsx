import React from "react";

export default function EvidenceMarker({ evidence }) {
  if (evidence.type === "skid_mark") {
    return (
      <mesh
        position={[
          evidence.position.x,
          evidence.position.y,
          evidence.position.z,
        ]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <planeGeometry
          args={[
            evidence.length_m || 4,
            0.25,
          ]}
        />

        <meshBasicMaterial
          color="#e53935"
          transparent
          opacity={0.8}
        />
      </mesh>
    );
  }

  return null;
}