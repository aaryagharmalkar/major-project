import React, { useRef, useEffect } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, Grid, Environment } from "@react-three/drei";
import * as THREE from "three";

import VehicleModel from "./VehicleModel";
import PersonModel from "./PersonModel";
import Road from "./Road";
import RoomEnvironment from "./RoomEnvironment";
import EvidenceMarker from "./EvidenceMarker";
import TrajectoryPath from "./TrajectoryPath";
import ImpactWave from "./ImpactWave";

function CameraController({ cameraPreset, isIndoor }) {
  const { camera } = useThree();
  const controlsRef = useRef();

  useEffect(() => {
    if (cameraPreset === "overhead") {
      camera.position.set(0, isIndoor ? 14 : 22, 0.1);
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
        controlsRef.current.update();
      }
    } else if (cameraPreset === "impact") {
      camera.position.set(isIndoor ? 2.5 : 4, isIndoor ? 1.8 : 3, isIndoor ? 3 : 5);
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
        controlsRef.current.update();
      }
    } else {
      // Tactical 45-degree isometric default
      camera.position.set(isIndoor ? 8 : 12, isIndoor ? 6 : 10, isIndoor ? 10 : 15);
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
        controlsRef.current.update();
      }
    }
  }, [cameraPreset, camera, isIndoor]);

  return (
    <OrbitControls
      ref={controlsRef}
      enableDamping
      dampingFactor={0.08}
      enableZoom={true}
      enablePan={true}
      enableRotate={true}
      minDistance={1.5}
      maxDistance={60}
      maxPolarAngle={Math.PI / 2 - 0.02}
    />
  );
}

export default function SceneCanvas({
  scene,
  currentTime = 0,
  selectedTargetId,
  setSelectedTargetId,
  cameraPreset = "tactical",
}) {
  const isIndoor = scene.metadata?.scene_type === "indoor_crime_scene" || !!scene.room;
  const roads = scene.roads || [];
  const vehicles = scene.vehicles || [];
  const people = scene.people || [];
  const evidence = scene.evidence || [];
  const timeline = scene.timeline || [];
  const ballistics = scene.ballistics || [];

  return (
    <Canvas
      camera={{
        position: [isIndoor ? 8 : 12, isIndoor ? 6 : 10, isIndoor ? 10 : 15],
        fov: 45,
      }}
      style={{
        width: "100%",
        height: "100%",
        background: "#05080f",
        touchAction: "none",
      }}
    >
      {/* Fog for Tactical Depth */}
      <fog attach="fog" args={["#05080f", isIndoor ? 15 : 20, isIndoor ? 45 : 65]} />

      {/* Cyber-Forensic Ambient & Directional Lighting */}
      <ambientLight intensity={0.9} />
      <directionalLight
        position={[15, 20, 10]}
        intensity={2.2}
        color="#e0f7ff"
      />
      <directionalLight
        position={[-10, 10, -10]}
        intensity={1.0}
        color="#00f0ff"
      />

      <Environment preset="night" />

      {/* Forensic Blueprint Grid */}
      <Grid
        position={[0, -0.01, 0]}
        args={[80, 80]}
        cellSize={1}
        cellColor="#102538"
        sectionSize={5}
        sectionColor="#00f0ff"
        fadeDistance={isIndoor ? 35 : 50}
        fadeStrength={1.5}
      />

      {/* 1. Render Indoor Room Environment if Indoor Case */}
      {isIndoor && scene.room && (
        <RoomEnvironment
          room={scene.room}
          ballistics={ballistics}
          currentTime={currentTime}
        />
      )}

      {/* 2. Render Outdoor Roads if Road Collision Case */}
      {!isIndoor && roads.map((road) => (
        <Road key={road.id} road={road} />
      ))}

      {/* 3. Render Holographic Trajectory Ribbons for Vehicles */}
      {vehicles.map((vehicle, idx) => (
        <TrajectoryPath
          key={`traj_${vehicle.id}`}
          entity={vehicle}
          timeline={timeline}
          color={idx === 0 ? "#00f0ff" : idx === 1 ? "#ffb700" : "#00ff88"}
          currentTime={currentTime}
        />
      ))}

      {/* 4. Render Holographic Trajectory Ribbons for Moving People */}
      {people.map((person, idx) => (
        <TrajectoryPath
          key={`traj_person_${person.id}`}
          entity={person}
          timeline={timeline}
          color="#ff0055"
          currentTime={currentTime}
        />
      ))}

      {/* 5. Render Collision Epicenter & Shockwave Beacon (Outdoor only) */}
      {!isIndoor && <ImpactWave position={[0, 0.04, 0]} currentTime={currentTime} />}

      {/* 6. Render Vehicles Dynamically */}
      {vehicles.map((vehicle) => (
        <VehicleModel
          key={vehicle.id}
          vehicle={vehicle}
          timeline={timeline}
          currentTime={currentTime}
          isSelected={selectedTargetId === vehicle.id}
          onSelect={(id) => setSelectedTargetId(id)}
        />
      ))}

      {/* 7. Render Standalone People / Pedestrians / Suspects / Victims */}
      {people.map((person) => (
        <PersonModel
          key={person.id}
          person={person}
          timeline={timeline}
          currentTime={currentTime}
          isSelected={selectedTargetId === person.id}
          onSelect={(id) => setSelectedTargetId(id)}
        />
      ))}

      {/* 8. Render Forensic Evidence Markers */}
      {evidence.map((ev) => (
        <EvidenceMarker
          key={ev.id}
          evidence={ev}
          isSelected={selectedTargetId === ev.id}
          onSelect={(id) => setSelectedTargetId(id)}
        />
      ))}

      {/* Camera Preset Manager & Controls */}
      <CameraController cameraPreset={cameraPreset} isIndoor={isIndoor} />
    </Canvas>
  );
}