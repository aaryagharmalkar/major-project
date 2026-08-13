import React from "react";
import SceneCanvas from "./SceneCanvas";

const DEMO_SCENE = {
  metadata: {
    scene_id: "case_scene",
    location_name:
      "Shankar Road T-Point, New Delhi",
    scene_type: "road_accident",
  },

  roads: [
    {
      id: "road_1",
      name: "Shankar Road",
      width_m: 12.5,
      heading_deg: 0,
      position: {
        x: 0,
        y: 0,
        z: 0,
      },
    },

    {
      id: "road_2",
      name: "Rajinder Nagar Main Road",
      width_m: 10,
      heading_deg: 90,
      position: {
        x: 0,
        y: 0.01,
        z: 0,
      },
    },
  ],

  vehicles: [
  {
    id: "vehicle_1",
    registration: "DL2SBP1234",
    make: "Bajaj Auto Ltd.",
    model: "Pulsar 150",

    asset_path: "/assets/vehicles/bajaj_pulsar_150.glb",

    // WEST → EAST
    start_position: {
      x: -12,
      y: 0,
      z: 0,
    },

    impact_position: {
      x: 0,
      y: 0,
      z: 0,
    },

    final_position: {
      x: 2.5,
      y: 0,
      z: 0,
    },

    rotation: {
      x: 0,
      y: 180,
      z: 0,
    },

    speed_hypotheses: [
      {
        value_kmph: 60,
        confidence: 0.9,
        source: "CCTV",
      },
      {
        value_kmph: 52.4,
        confidence: 0.9,
        source: "CCTV",
      },
    ],
  },

  {
    id: "vehicle_2",
    registration: "DL5SCT5678",
    make: "Honda Motorcycle & Scooter India",
    model: "Pulsar 150 (temporary asset)",

    asset_path: "/assets/vehicles/sports_bike.glb",

    // SOUTH → NORTH
    start_position: {
      x: 0,
      y: 0,
      z: -10,
    },

    impact_position: {
      x: 0,
      y: 0,
      z: 0,
    },

    final_position: {
      x: 0,
      y: 0,
      z: -1.5,
    },

    rotation: {
      x: 0,
      y: 360,
      z: 0,
    },

    speed_hypotheses: [
      {
        value_kmph: 10,
        confidence: 0.9,
        source: "CCTV",
      },
    ],
  },
],

  evidence: [
    {
      id: "evidence_skid_1",

      type: "skid_mark",

      description: "4.2 meter skid mark",

      length_m: 4.2,

      position: {
        x: -2,
        y: 0.03,
        z: 0,
      },

      related_vehicle_ids: [
        "vehicle_1",
      ],
    },
  ],

  timeline: [
    {
      id: "approach_1",
      event_type: "vehicle_approach",
      timestamp: "18:20:02",
      participant_ids: [
        "vehicle_1",
      ],
      confidence: 0.9,
    },

    {
      id: "approach_2",
      event_type: "vehicle_approach",
      timestamp: "18:20:06",
      participant_ids: [
        "vehicle_2",
      ],
      confidence: 0.9,
    },

    {
      id: "impact_1",
      event_type: "collision",
      timestamp: "18:20:07.800",
      participant_ids: [
        "vehicle_1",
        "vehicle_2",
      ],
      confidence: 0.9,
      status: "conflict",
    },

    {
      id: "final_position",
      event_type: "post_collision",
      timestamp: "18:20:10",
      participant_ids: [
        "vehicle_1",
        "vehicle_2",
      ],
      confidence: 0.8,
    },
  ],
};

export default function SceneViewer() {
  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        background: "#08090d",
        position: "relative",
      }}
    >
      <SceneCanvas scene={DEMO_SCENE} />

      <div
        style={{
          position: "absolute",
          top: 20,
          left: 20,
          zIndex: 10,
          color: "#fff",
          background: "rgba(0,0,0,0.75)",
          padding: "16px 20px",
          borderRadius: 8,
          fontFamily: "monospace",
        }}
      >
        <div style={{ fontSize: 18 }}>
          SENTINEL — 3D RECONSTRUCTION
        </div>

        <div
          style={{
            marginTop: 6,
            fontSize: 12,
            opacity: 0.7,
          }}
        >
          {DEMO_SCENE.metadata.location_name}
        </div>
      </div>
    </div>
  );
}