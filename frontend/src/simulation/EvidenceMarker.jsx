import React from "react";
import * as THREE from "three";

export default function EvidenceMarker({ evidence, isSelected, onSelect }) {
  const type = (evidence.type || "evidence").toLowerCase();
  const pos = evidence.position || { x: 0, y: 0.03, z: 0 };

  // 1. Skid Mark
  if (type.includes("skid")) {
    const length = evidence.length_m || 4.2;
    return (
      <group
        position={[pos.x, pos.y || 0.03, pos.z]}
        onClick={(e) => {
          e.stopPropagation();
          if (onSelect) onSelect(evidence.id);
        }}
      >
        <mesh position={[0, 0, 0.2]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[length, 0.12]} />
          <meshBasicMaterial color="#0a0a0a" transparent opacity={0.85} />
        </mesh>
        <mesh position={[0, 0, -0.2]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[length, 0.12]} />
          <meshBasicMaterial color="#0a0a0a" transparent opacity={0.85} />
        </mesh>
        <mesh position={[0, 0.5, 0]}>
          <cylinderGeometry args={[0.015, 0.015, 1.0, 8]} />
          <meshBasicMaterial color="#ffb700" />
        </mesh>
        <mesh position={[0, 1.0, 0]}>
          <boxGeometry args={[0.35, 0.2, 0.02]} />
          <meshBasicMaterial color="#ffb700" />
        </mesh>
      </group>
    );
  }

  // 2. Shell Casing / Cartridge
  if (type.includes("casing") || type.includes("cartridge") || type.includes("bullet")) {
    return (
      <group
        position={[pos.x, pos.y || 0.02, pos.z]}
        onClick={(e) => {
          e.stopPropagation();
          if (onSelect) onSelect(evidence.id);
        }}
      >
        {/* Brass Shell Casing */}
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.03, 0.03, 0.08, 8]} />
          <meshStandardMaterial color="#d4af37" metalness={0.9} roughness={0.2} />
        </mesh>
        {/* Forensic Pin */}
        <mesh position={[0, 0.35, 0]}>
          <cylinderGeometry args={[0.01, 0.01, 0.7, 8]} />
          <meshBasicMaterial color="#ffcc00" />
        </mesh>
        <mesh position={[0, 0.7, 0]}>
          <boxGeometry args={[0.2, 0.15, 0.02]} />
          <meshBasicMaterial color="#ffcc00" />
        </mesh>
      </group>
    );
  }

  // 3. Blood Spatter / Fluid
  if (type.includes("blood") || type.includes("fluid")) {
    return (
      <group
        position={[pos.x, pos.y || 0.02, pos.z]}
        onClick={(e) => {
          e.stopPropagation();
          if (onSelect) onSelect(evidence.id);
        }}
      >
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <circleGeometry args={[0.45, 16]} />
          <meshBasicMaterial color="#8b0000" transparent opacity={0.85} />
        </mesh>
        <mesh position={[0, 0.35, 0]}>
          <cylinderGeometry args={[0.01, 0.01, 0.7, 8]} />
          <meshBasicMaterial color="#ff0055" />
        </mesh>
      </group>
    );
  }

  // 4. Firearm / Weapon Evidence (Supports TRELLIS 3D GLB Model or detailed procedural weapon)
  if (type.includes("weapon") || type.includes("firearm") || type.includes("pistol") || type.includes("gun")) {
    return (
      <group
        position={[pos.x, pos.y || 0.03, pos.z]}
        onClick={(e) => {
          e.stopPropagation();
          if (onSelect) onSelect(evidence.id);
        }}
      >
        {/* Firearm 3D Model: Slide, Barrel & Grip */}
        <group position={[0, 0.04, 0]} rotation={[-Math.PI / 2, 0, Math.PI / 4]}>
          {/* Slide & Barrel */}
          <mesh position={[0, 0.08, 0]}>
            <boxGeometry args={[0.06, 0.22, 0.05]} />
            <meshStandardMaterial color="#1a1d24" metalness={0.9} roughness={0.3} />
          </mesh>
          {/* Pistol Grip */}
          <mesh position={[0, -0.02, -0.07]} rotation={[0.3, 0, 0]}>
            <boxGeometry args={[0.055, 0.12, 0.05]} />
            <meshStandardMaterial color="#2d2218" metalness={0.3} roughness={0.8} />
          </mesh>
          {/* Trigger Guard */}
          <mesh position={[0, 0.02, -0.04]}>
            <torusGeometry args={[0.025, 0.005, 8, 12]} />
            <meshStandardMaterial color="#1a1d24" metalness={0.9} roughness={0.3} />
          </mesh>
        </group>

        {/* Forensic Evidence Stand & Number Flag */}
        <mesh position={[0, 0.35, 0]}>
          <cylinderGeometry args={[0.01, 0.01, 0.7, 8]} />
          <meshBasicMaterial color="#ffb700" />
        </mesh>
        <mesh position={[0, 0.7, 0]}>
          <boxGeometry args={[0.22, 0.16, 0.02]} />
          <meshBasicMaterial color="#ffb700" />
        </mesh>
      </group>
    );
  }

  // 5. Default / Generic Forensic Marker
  return (
    <group
      position={[pos.x, pos.y || 0.03, pos.z]}
      onClick={(e) => {
        e.stopPropagation();
        if (onSelect) onSelect(evidence.id);
      }}
    >
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.2, 0.28, 16]} />
        <meshBasicMaterial color="#00f0ff" transparent opacity={0.8} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0, 0.4, 0]}>
        <cylinderGeometry args={[0.015, 0.015, 0.8, 8]} />
        <meshBasicMaterial color="#00f0ff" />
      </mesh>
      <mesh position={[0, 0.8, 0]}>
        <boxGeometry args={[0.25, 0.18, 0.02]} />
        <meshBasicMaterial color="#00f0ff" />
      </mesh>
    </group>
  );
}