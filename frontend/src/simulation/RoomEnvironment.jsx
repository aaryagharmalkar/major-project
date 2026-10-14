import React, { useMemo } from "react";
import * as THREE from "three";

export default function RoomEnvironment({ room, ballistics = [], currentTime = 0 }) {
  const length = room.length_m || 8.0; // X
  const width = room.width_m || 6.0;   // Z
  const height = room.height_m || 2.8; // Y

  const halfL = length / 2;
  const halfW = width / 2;

  const floorMaterial = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: room.floor_color || "#151922",
        roughness: 0.85,
        metalness: 0.1,
      }),
    [room.floor_color]
  );

  const wallMaterial = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: room.wall_color || "#1b2333",
        roughness: 0.7,
        metalness: 0.15,
        transparent: true,
        opacity: 0.65, // Cutaway transparency for detective camera inspection
        side: THREE.DoubleSide,
      }),
    [room.wall_color]
  );

  // Ballistics laser is actively discharging between T = 4.8s and T = 5.8s, with a lasting bullet trajectory beam after T >= 5.0s
  const isGunshotActive = currentTime >= 4.8;
  const isMuzzleFlashing = currentTime >= 4.8 && currentTime <= 5.6;

  return (
    <group>
      {/* 1. Room Floor */}
      <mesh position={[0, 0, 0]} receiveShadow material={floorMaterial}>
        <boxGeometry args={[length, 0.04, width]} />
      </mesh>

      {/* Floor Tactical Boundary Grid */}
      <gridHelper
        position={[0, 0.025, 0]}
        args={[Math.max(length, width), Math.round(Math.max(length, width)), "#00f0ff", "#0d2b38"]}
      />

      {/* 2. North Wall (Z = -halfW) */}
      <mesh position={[0, height / 2, -halfW]} material={wallMaterial}>
        <boxGeometry args={[length, height, 0.1]} />
      </mesh>

      {/* 3. South Wall (Z = halfW) */}
      <mesh position={[0, height / 2, halfW]} material={wallMaterial}>
        <boxGeometry args={[length, height, 0.1]} />
      </mesh>

      {/* 4. East Wall (X = halfL) */}
      <mesh position={[halfL, height / 2, 0]} material={wallMaterial}>
        <boxGeometry args={[0.1, height, width]} />
      </mesh>

      {/* 5. West Wall with Entrance Doorway Cutout (X = -halfL) */}
      <group position={[-halfL, height / 2, 0]}>
        {/* Upper wall above doorway */}
        <mesh position={[0, 0.5, 0]} material={wallMaterial}>
          <boxGeometry args={[0.1, height - 1.8, width]} />
        </mesh>
        {/* Left wall segment */}
        <mesh position={[0, -0.6, halfW / 2 + 0.6]} material={wallMaterial}>
          <boxGeometry args={[0.1, 1.8, halfW - 0.6]} />
        </mesh>
        {/* Right wall segment */}
        <mesh position={[0, -0.6, -(halfW / 2 + 0.6)]} material={wallMaterial}>
          <boxGeometry args={[0.1, 1.8, halfW - 0.6]} />
        </mesh>
      </group>

      {/* 6. Tactical Architectural Wall Outline Trim */}
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(length, height, width)]} />
        <lineBasicMaterial color="#00f0ff" transparent opacity={0.4} />
      </lineSegments>

      {/* 7. Dynamic Ballistics Laser Trajectories */}
      {isGunshotActive &&
        ballistics.map((traj) => {
          const p1 = new THREE.Vector3(traj.origin.x, traj.origin.y, traj.origin.z);
          const p2 = new THREE.Vector3(traj.target.x, traj.target.y, traj.target.z);
          const geom = new THREE.BufferGeometry().setFromPoints([p1, p2]);

          return (
            <group key={traj.id}>
              {/* Trajectory Laser Line */}
              <line geometry={geom}>
                <lineBasicMaterial
                  color={traj.color || "#ff0055"}
                  linewidth={2}
                  transparent
                  opacity={isMuzzleFlashing ? 1.0 : 0.65}
                />
              </line>

              {/* Muzzle Origin Flash Beacon (Flashes at moment of shooting) */}
              {isMuzzleFlashing && (
                <mesh position={[p1.x, p1.y, p1.z]}>
                  <sphereGeometry args={[0.09, 16, 16]} />
                  <meshBasicMaterial color="#ffcc00" />
                </mesh>
              )}

              {/* Impact Penetration Decal on Wall */}
              <mesh position={[p2.x, p2.y, p2.z]}>
                <sphereGeometry args={[0.05, 12, 12]} />
                <meshBasicMaterial color="#ff0055" />
              </mesh>
              <mesh position={[p2.x - 0.02, p2.y, p2.z]} rotation={[0, Math.PI / 2, 0]}>
                <ringGeometry args={[0.04, 0.12, 16]} />
                <meshBasicMaterial color="#ff0055" side={THREE.DoubleSide} />
              </mesh>
            </group>
          );
        })}
    </group>
  );
}
