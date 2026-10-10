import React, { useRef, useEffect } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, Grid, Environment } from "@react-three/drei";
import * as THREE from "three";

import VehicleModel from "./VehicleModel";
import PersonModel from "./PersonModel";
import Road from "./Road";
import EvidenceMarker from "./EvidenceMarker";
import TrajectoryPath from "./TrajectoryPath";
import ImpactWave from "./ImpactWave";

function CameraController({ cameraPreset }) {
  const { camera } = useThree();
  const controlsRef = useRef();

  useEffect(() => {
    if (cameraPreset === "overhead") {
      camera.position.set(0, 22, 0.1);
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
        controlsRef.current.update();
      }
    } else if (cameraPreset === "impact") {
      camera.position.set(4, 3, 5);
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
        controlsRef.current.update();
      }
    } else {
      // Tactical 45-degree isometric default
      camera.position.set(12, 10, 15);
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
        controlsRef.current.update();
      }
    }
  }, [cameraPreset, camera]);

  return (
    <OrbitControls
      ref={controlsRef}
      enableDamping
      dampingFactor={0.08}
      enableZoom={true}
      enablePan={true}
      enableRotate={true}
      minDistance={2}
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
  const roads = scene.roads || [];
  const vehicles = scene.vehicles || [];
  const people = scene.people || [];
  const evidence = scene.evidence || [];
  const timeline = scene.timeline || [];

  return (
    <Canvas
      camera={{
        position: [12, 10, 15],
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
      <fog attach="fog" args={["#05080f", 20, 65]} />

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
        fadeDistance={50}
        fadeStrength={1.5}
      />

      {/* Render Roads Dynamically */}
      {roads.map((road) => (
        <Road key={road.id} road={road} />
      ))}

      {/* Render Holographic Trajectory Ribbons for Vehicles */}
      {vehicles.map((vehicle, idx) => (
        <TrajectoryPath
          key={`traj_${vehicle.id}`}
          entity={vehicle}
          timeline={timeline}
          color={idx === 0 ? "#00f0ff" : idx === 1 ? "#ffb700" : "#00ff88"}
          currentTime={currentTime}
        />
      ))}

      {/* Render Holographic Trajectory Ribbons for Moving People */}
      {people.map((person, idx) => (
        <TrajectoryPath
          key={`traj_person_${person.id}`}
          entity={person}
          timeline={timeline}
          color="#ff0055"
          currentTime={currentTime}
        />
      ))}

      {/* Render Collision Epicenter & Shockwave Beacon */}
      <ImpactWave position={[0, 0.04, 0]} currentTime={currentTime} />

      {/* Render Vehicles Dynamically */}
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

      {/* Render Standalone People / Pedestrians / Witnesses */}
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

      {/* Render Forensic Evidence Markers */}
      {evidence.map((ev) => (
        <EvidenceMarker
          key={ev.id}
          evidence={ev}
          isSelected={selectedTargetId === ev.id}
          onSelect={(id) => setSelectedTargetId(id)}
        />
      ))}

      {/* Camera Preset Manager & Controls */}
      <CameraController cameraPreset={cameraPreset} />
    </Canvas>
  );
}