import React, { useMemo } from "react";
import * as THREE from "three";

export default function RiderAvatar({
  color = "#00f0ff",
  isScooter = false,
  vehicleRotation = { x: 0, y: 0, z: 0 },
  riderRotationY = 0,
  seatOffset = [0, 0.65, 0],
  fallProgress = 0, // 0 = riding on seat, 1 = fallen on ground at rest
  isVictim = false,
}) {
  const suitMaterial = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: "#1c2331",
        roughness: 0.6,
        metalness: 0.2,
      }),
    []
  );

  const accentMaterial = useMemo(
    () =>
      new THREE.MeshBasicMaterial({
        color: color,
      }),
    [color]
  );

  // Compute kinematic fall displacement and body rotation strictly clamped to ground plane
  const { currentPos, currentRot } = useMemo(() => {
    if (fallProgress <= 0) {
      // Actively riding on the vehicle seat
      return {
        currentPos: seatOffset,
        currentRot: [
          vehicleRotation.x,
          vehicleRotation.y + riderRotationY,
          vehicleRotation.z,
        ],
      };
    }

    // Easing curve for rapid impact ejection followed by slide to rest on asphalt
    const t = Math.min(1, Math.pow(fallProgress, 0.7));

    if (isVictim) {
      // Victim rider knocked laterally to the right side of the scooter onto asphalt
      return {
        currentPos: [
          seatOffset[0] + t * 0.95, // Displaced right onto road
          Math.max(0.12, seatOffset[1] * (1 - t) + 0.12 * t), // Strictly on top of road plane (Y >= 0.12)
          seatOffset[2] - t * 0.35,
        ],
        currentRot: [
          Math.PI / 2 * t, // Lies flat on side on the asphalt
          vehicleRotation.y + t * 0.4,
          0.3 * t,
        ],
      };
    } else {
      // Accused rider ejected forward over handlebars onto ground
      return {
        currentPos: [
          seatOffset[0] - t * 1.1, // Thrown forward along momentum vector
          Math.max(0.12, seatOffset[1] * (1 - t) + 0.12 * t), // Strictly on top of road plane (Y >= 0.12)
          seatOffset[2] + t * 0.4,
        ],
        currentRot: [
          0.2 * t,
          vehicleRotation.y + riderRotationY,
          -Math.PI / 2 * t, // Lies flat on road
        ],
      };
    }
  }, [fallProgress, seatOffset, vehicleRotation, riderRotationY, isVictim]);

  const torsoLeanAngle = isScooter ? -0.05 : 0.25;

  return (
    <group position={currentPos} rotation={currentRot}>
      {/* 1. Hips / Pelvis */}
      <mesh position={[0, 0, 0]} material={suitMaterial}>
        <boxGeometry args={[0.26, 0.15, 0.22]} />
      </mesh>

      {/* 2. Upper Torso / Jacket */}
      <group position={[0, 0.16, 0]} rotation={[torsoLeanAngle, 0, 0]}>
        <mesh position={[0, 0.16, 0]} material={suitMaterial}>
          <boxGeometry args={[0.3, 0.32, 0.2]} />
        </mesh>

        {/* Chest Tactical Identification Strip */}
        <mesh position={[0, 0.18, 0.105]} material={accentMaterial}>
          <planeGeometry args={[0.12, 0.04]} />
        </mesh>

        {/* 3. Neck & Helmet */}
        <group position={[0, 0.4, 0.04]}>
          <mesh material={suitMaterial}>
            <sphereGeometry args={[0.13, 16, 16]} />
          </mesh>
          {/* Luminous Visor */}
          <mesh position={[0, 0.02, 0.09]} rotation={[0.1, 0, 0]} material={accentMaterial}>
            <boxGeometry args={[0.15, 0.07, 0.06]} />
          </mesh>
        </group>

        {/* 4. Left Arm */}
        <group position={[-0.18, 0.26, 0.02]} rotation={[-0.5, 0.2, -0.2]}>
          <mesh position={[0, -0.14, 0]} material={suitMaterial}>
            <cylinderGeometry args={[0.04, 0.035, 0.28, 8]} />
          </mesh>
          <group position={[0, -0.26, 0]} rotation={[0.7, -0.2, 0]}>
            <mesh position={[0, -0.11, 0]} material={suitMaterial}>
              <cylinderGeometry args={[0.035, 0.03, 0.22, 8]} />
            </mesh>
          </group>
        </group>

        {/* 5. Right Arm */}
        <group position={[0.18, 0.26, 0.02]} rotation={[-0.5, -0.2, 0.2]}>
          <mesh position={[0, -0.14, 0]} material={suitMaterial}>
            <cylinderGeometry args={[0.04, 0.035, 0.28, 8]} />
          </mesh>
          <group position={[0, -0.26, 0]} rotation={[0.7, 0.2, 0]}>
            <mesh position={[0, -0.11, 0]} material={suitMaterial}>
              <cylinderGeometry args={[0.035, 0.03, 0.22, 8]} />
            </mesh>
          </group>
        </group>
      </group>

      {/* 6. Left Leg */}
      <group position={[-0.14, -0.04, 0.04]} rotation={[isScooter ? 1.2 : 0.8, 0.2, -0.1]}>
        <mesh position={[0, -0.15, 0]} material={suitMaterial}>
          <cylinderGeometry args={[0.05, 0.045, 0.3, 8]} />
        </mesh>
        <group position={[0, -0.28, 0]} rotation={[isScooter ? -1.2 : -1.0, 0, 0]}>
          <mesh position={[0, -0.14, 0]} material={suitMaterial}>
            <cylinderGeometry args={[0.045, 0.04, 0.28, 8]} />
          </mesh>
          <mesh position={[0, -0.28, 0.06]} material={suitMaterial}>
            <boxGeometry args={[0.08, 0.06, 0.15]} />
          </mesh>
        </group>
      </group>

      {/* 7. Right Leg */}
      <group position={[0.14, -0.04, 0.04]} rotation={[isScooter ? 1.2 : 0.8, -0.2, 0.1]}>
        <mesh position={[0, -0.15, 0]} material={suitMaterial}>
          <cylinderGeometry args={[0.05, 0.045, 0.3, 8]} />
        </mesh>
        <group position={[0, -0.28, 0]} rotation={[isScooter ? -1.2 : -1.0, 0, 0]}>
          <mesh position={[0, -0.14, 0]} material={suitMaterial}>
            <cylinderGeometry args={[0.045, 0.04, 0.28, 8]} />
          </mesh>
          <mesh position={[0, -0.28, 0.06]} material={suitMaterial}>
            <boxGeometry args={[0.08, 0.06, 0.15]} />
          </mesh>
        </group>
      </group>
    </group>
  );
}
