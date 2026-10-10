import React, { useMemo } from "react";
import * as THREE from "three";
import { resolveEntityWaypoints, sampleEntityState } from "./kinematics";

export default function TrajectoryPath({
  entity,
  timeline = [],
  color = "#00f0ff",
  currentTime = 0,
}) {
  const waypoints = useMemo(() => resolveEntityWaypoints(entity, timeline), [entity, timeline]);

  // Generate smooth sampled curve through all waypoints
  const { points, activePoint } = useMemo(() => {
    if (!waypoints || waypoints.length === 0) {
      return { points: [], activePoint: null };
    }

    const pts = [];
    const subSteps = 20;

    for (let i = 0; i < waypoints.length - 1; i++) {
      const p1 = waypoints[i].position;
      const p2 = waypoints[i + 1].position;

      for (let s = 0; s <= subSteps; s++) {
        const t = s / subSteps;
        pts.push(
          new THREE.Vector3(
            p1.x + (p2.x - p1.x) * t,
            0.02,
            p1.z + (p2.z - p1.z) * t
          )
        );
      }
    }

    const { position } = sampleEntityState(waypoints, currentTime);
    const active = new THREE.Vector3(position.x, 0.05, position.z);

    return { points: pts, activePoint: active };
  }, [waypoints, currentTime]);

  const lineGeometry = useMemo(() => {
    if (points.length === 0) return null;
    return new THREE.BufferGeometry().setFromPoints(points);
  }, [points]);

  if (!lineGeometry) return null;

  return (
    <group>
      {/* 3D Holographic Trajectory Line */}
      <line geometry={lineGeometry}>
        <lineDashedMaterial
          color={color}
          dashSize={0.4}
          gapSize={0.2}
          transparent
          opacity={0.65}
        />
      </line>

      {/* Start Waypoint Marker */}
      {waypoints[0] && (
        <mesh
          position={[waypoints[0].position.x, 0.03, waypoints[0].position.z]}
          rotation={[-Math.PI / 2, 0, 0]}
        >
          <ringGeometry args={[0.3, 0.45, 24]} />
          <meshBasicMaterial color={color} transparent opacity={0.6} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* Final Rest Waypoint Marker */}
      {waypoints.length > 1 && (
        <mesh
          position={[
            waypoints[waypoints.length - 1].position.x,
            0.03,
            waypoints[waypoints.length - 1].position.z,
          ]}
          rotation={[-Math.PI / 2, 0, 0]}
        >
          <ringGeometry args={[0.3, 0.45, 24]} />
          <meshBasicMaterial color="#ff3366" transparent opacity={0.8} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* Active Position Indicator */}
      {activePoint && (
        <mesh position={[activePoint.x, activePoint.y, activePoint.z]}>
          <sphereGeometry args={[0.1, 16, 16]} />
          <meshBasicMaterial color={color} />
        </mesh>
      )}
    </group>
  );
}
