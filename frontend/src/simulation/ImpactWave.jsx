import React, { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

export default function ImpactWave({ position = [0, 0.04, 0], currentTime = 0 }) {
  const ringRef = useRef();

  // Pulse effect near impact time (4.8s to 6.5s)
  const isNearImpact = currentTime >= 4.8 && currentTime <= 7.0;
  const impactIntensity = isNearImpact ? Math.max(0, 1 - (currentTime - 5.0) / 2.0) : 0;

  useFrame((state) => {
    if (ringRef.current && isNearImpact) {
      const scale = 1 + (state.clock.elapsedTime * 3) % 2.5;
      ringRef.current.scale.set(scale, scale, 1);
    }
  });

  return (
    <group position={position}>
      {/* Ground Collision Target / Epicenter Ring */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.5, 0.65, 32]} />
        <meshBasicMaterial
          color="#ff0055"
          transparent
          opacity={0.85}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Outer Warning Reticle */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[1.2, 1.25, 32]} />
        <meshBasicMaterial
          color="#ffb700"
          transparent
          opacity={0.6}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Dynamic Shockwave Ring during Impact */}
      {isNearImpact && (
        <mesh ref={ringRef} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.8, 0.95, 32]} />
          <meshBasicMaterial
            color="#ff0055"
            transparent
            opacity={Math.max(0.2, impactIntensity)}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}

      {/* Center Impact Beacon Pin */}
      <mesh position={[0, 0.6, 0]}>
        <cylinderGeometry args={[0.02, 0.02, 1.2, 8]} />
        <meshBasicMaterial color="#ff0055" transparent opacity={0.7} />
      </mesh>
      <mesh position={[0, 1.2, 0]}>
        <sphereGeometry args={[0.08, 16, 16]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>
    </group>
  );
}
