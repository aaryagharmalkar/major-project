import * as THREE from "three";

/**
 * Resolves a normalized list of waypoints for any entity across time.
 * Supports explicit waypoints, 3-point start/impact/final setups, or dynamic timeline events.
 */
export function resolveEntityWaypoints(entity, timeline = []) {
  if (entity.waypoints && entity.waypoints.length > 0) {
    return [...entity.waypoints].sort((a, b) => a.time - b.time);
  }

  // Construct from 3-point schema if provided
  const startPos = entity.start_position || entity.position || { x: 0, y: 0, z: 0 };
  const impactPos = entity.impact_position || startPos;
  const finalPos = entity.final_position?.position || entity.final_position || impactPos;

  const defaultRot = entity.rotation || { x: 0, y: 0, z: 0 };

  // Check if timeline defines specific impact timestamp
  const impactEvent = timeline.find(
    (ev) =>
      ev.event_type?.includes("collision") ||
      ev.event_type?.includes("impact") ||
      ev.event_type?.includes("gunshot")
  );

  const impactTime = impactEvent ? 5.0 : 5.0;

  return [
    {
      time: 0.0,
      position: startPos,
      rotation: defaultRot,
    },
    {
      time: impactTime,
      position: impactPos,
      rotation: defaultRot,
    },
    {
      time: 10.0,
      position: finalPos,
      rotation: defaultRot,
    },
  ];
}

/**
 * Interpolates entity position, rotation, and instantaneous velocity for any arbitrary timestamp.
 */
export function sampleEntityState(waypoints, currentTime) {
  if (!waypoints || waypoints.length === 0) {
    return {
      position: { x: 0, y: 0, z: 0 },
      rotation: { x: 0, y: 0, z: 0 },
      speedKmph: 0,
      activeSegmentIndex: 0,
    };
  }

  if (waypoints.length === 1) {
    return {
      position: waypoints[0].position,
      rotation: waypoints[0].rotation || { x: 0, y: 0, z: 0 },
      speedKmph: 0,
      activeSegmentIndex: 0,
    };
  }

  // Before first waypoint
  if (currentTime <= waypoints[0].time) {
    const p1 = waypoints[0].position;
    const p2 = waypoints[1].position;
    const dt = Math.max(0.01, waypoints[1].time - waypoints[0].time);
    const dist = Math.hypot(p2.x - p1.x, p2.z - p1.z);
    const speedKmph = (dist / dt) * 3.6;

    return {
      position: waypoints[0].position,
      rotation: waypoints[0].rotation || { x: 0, y: 0, z: 0 },
      speedKmph,
      activeSegmentIndex: 0,
    };
  }

  // After last waypoint
  const lastIndex = waypoints.length - 1;
  if (currentTime >= waypoints[lastIndex].time) {
    return {
      position: waypoints[lastIndex].position,
      rotation: waypoints[lastIndex].rotation || { x: 0, y: 0, z: 0 },
      speedKmph: 0,
      activeSegmentIndex: lastIndex,
    };
  }

  // Find active segment between waypoints[i] and waypoints[i+1]
  let i = 0;
  while (i < waypoints.length - 1 && currentTime > waypoints[i + 1].time) {
    i++;
  }

  const w1 = waypoints[i];
  const w2 = waypoints[i + 1];

  const segDuration = Math.max(0.001, w2.time - w1.time);
  const rawProgress = (currentTime - w1.time) / segDuration;
  const progress = Math.max(0, Math.min(1, rawProgress));

  // Position interpolation
  const pos = {
    x: w1.position.x + (w2.position.x - w1.position.x) * progress,
    y: (w1.position.y || 0) + ((w2.position.y || 0) - (w1.position.y || 0)) * progress,
    z: w1.position.z + (w2.position.z - w1.position.z) * progress,
  };

  // Rotation interpolation
  const r1 = w1.rotation || { x: 0, y: 0, z: 0 };
  const r2 = w2.rotation || r1;
  const rot = {
    x: ((r1.x + (r2.x - r1.x) * progress) * Math.PI) / 180,
    y: ((r1.y + (r2.y - r1.y) * progress) * Math.PI) / 180,
    z: ((r1.z + (r2.z - r1.z) * progress) * Math.PI) / 180,
  };

  // Calculate instantaneous velocity in km/h
  const deltaDistance = Math.hypot(w2.position.x - w1.position.x, w2.position.z - w1.position.z);
  const baseSpeedKmph = (deltaDistance / segDuration) * 3.6;

  return {
    position: pos,
    rotation: rot,
    speedKmph: baseSpeedKmph,
    activeSegmentIndex: i,
    segmentProgress: progress,
  };
}
