import React from "react";
import { Canvas } from "@react-three/fiber";
import {
  OrbitControls,
  Grid,
  Environment,
} from "@react-three/drei";

import VehicleModel from "./VehicleModel";
import Road from "./Road";
import EvidenceMarker from "./EvidenceMarker";

export default function SceneCanvas({ scene }) {
  return (
    <Canvas
      camera={{
        position: [12, 12, 18],
        fov: 45,
      }}
    >
      <ambientLight intensity={1.5} />

      <directionalLight
        position={[10, 15, 10]}
        intensity={3}
      />

      <Environment preset="city" />

      <Grid
        args={[100, 100]}
        cellSize={1}
        sectionSize={5}
        fadeDistance={80}
      />

      {scene.roads.map((road) => (
        <Road
          key={road.id}
          road={road}
        />
      ))}

      {scene.vehicles.map((vehicle) => (
        <VehicleModel
          key={vehicle.id}
          vehicle={vehicle}
        />
      ))}

      {scene.evidence.map((evidence) => (
        <EvidenceMarker
          key={evidence.id}
          evidence={evidence}
        />
      ))}

      <OrbitControls
        enableDamping
        dampingFactor={0.08}
      />
    </Canvas>
  );
}