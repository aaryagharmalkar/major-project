export const delhiAccidentScene = {
  metadata: {
    scene_id: "case_001_delhi_tpoint",
    location_name: "Shankar Road T-Point, New Delhi",
    scene_type: "road_traffic_collision",
    coordinate_system: "local_cartesian",
    units: "meters",
  },

  roads: [
    {
      id: "road_1",
      name: "Shankar Road",
      width_m: 12.5,
      heading_deg: 0,
      position: { x: 0, y: 0, z: 0 },
    },
    {
      id: "road_2",
      name: "Rajinder Nagar Main Road",
      width_m: 10,
      heading_deg: 90,
      position: { x: 0, y: 0.01, z: 0 },
    },
  ],

  vehicles: [
    {
      id: "vehicle_1",
      registration: "DL2SBP1234",
      make: "Bajaj Auto Ltd.",
      model: "Pulsar 220F",
      type: "two_wheeler",
      asset_path: "/assets/vehicles/vespa_scooter.glb",
      start_position: { x: -12, y: 0, z: 0 },
      impact_position: { x: -1.05, y: 0, z: 0 },
      final_position: { x: 2.5, y: 0, z: 0.3 },
      rotation: { x: 0, y: 180, z: 0 },
    },
    {
      id: "vehicle_2",
      registration: "DL5SCT5678",
      make: "Honda Motorcycle & Scooter India",
      model: "Activa 6G (Proxy)",
      type: "two_wheeler",
      asset_path: "/assets/vehicles/sports_bike.glb",
      start_position: { x: 0, y: 0, z: -10 },
      impact_position: { x: 0, y: 0, z: 0 },
      final_position: { x: 0.3, y: 0, z: -1.5 },
      rotation: { x: 0, y: 360, z: 0 },
    },
  ],

  people: [
    {
      id: "witness_1",
      name: "Ramesh (Tea Stall)",
      role: "witness",
      position: { x: -6.0, y: 0, z: 6.5 },
      rotation: { x: 0, y: 135, z: 0 },
    },
  ],

  evidence: [
    {
      id: "evidence_skid_1",
      type: "skid_mark",
      description: "4.2m locked-wheel emergency braking skid mark",
      length_m: 4.2,
      position: { x: -2.0, y: 0.03, z: 0 },
      related_vehicle_ids: ["vehicle_1"],
    },
  ],

  timeline: [
    {
      id: "approach_1",
      event_type: "approach",
      description: "Vehicle approach detected on CCTV-4 heading Eastbound.",
      timestamp: "18:20:02",
      confidence: 0.9,
    },
    {
      id: "brake_1",
      event_type: "braking",
      description: "Pulsar initiates emergency braking; tire skid trace begins.",
      timestamp: "18:20:05",
      confidence: 0.85,
    },
    {
      id: "impact_1",
      event_type: "collision",
      description: "Lateral perpendicular collision at T-Point intersection center.",
      timestamp: "18:20:07.800",
      confidence: 0.95,
      status: "conflict",
    },
    {
      id: "final_position",
      event_type: "final_rest",
      description: "Vehicles & riders come to rest per Spot Panchanama survey.",
      timestamp: "18:20:10",
      confidence: 0.9,
    },
  ],

  conflicts: [
    {
      id: "conflict_speed_v1",
      field: "vehicle_1_speed",
      hypotheses: [
        { id: "hyp_1", value: 60.0, source: "CCTV-4", confidence: 0.9 },
        { id: "hyp_2", value: 52.4, source: "CCTV-2", confidence: 0.9 },
      ],
    },
  ],
};
