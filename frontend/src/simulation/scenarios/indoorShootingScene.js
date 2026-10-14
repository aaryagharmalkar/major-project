export const indoorShootingScene = {
  metadata: {
    scene_id: "case_002_rohini_shooting",
    location_name: "Living Room, Flat 302, Sector 14, Rohini, New Delhi",
    scene_type: "indoor_crime_scene",
    coordinate_system: "local_cartesian",
    units: "meters",
  },

  room: {
    length_m: 8.0, // X dimension
    width_m: 6.0,  // Z dimension
    height_m: 2.8, // Y dimension
    floor_color: "#161b26",
    wall_color: "#1e2638",
  },

  roads: [], // Zero roads in enclosed room
  vehicles: [], // Zero vehicles in indoor homicide

  people: [
    {
      id: "suspect_1",
      name: "Assailant / Shooter",
      role: "suspect",
      position: { x: -2.8, y: 0, z: 1.2 },
      rotation: { x: 0, y: 75, z: 0 },
      waypoints: [
        { time: 0.0, position: { x: -3.8, y: 0, z: 0.1 }, rotation: { x: 0, y: 70, z: 0 } },  // Enters doorway
        { time: 2.5, position: { x: -3.2, y: 0, z: 0.7 }, rotation: { x: 0, y: 70, z: 0 } },  // Advances into room
        { time: 4.8, position: { x: -2.6, y: 0, z: 1.15 }, rotation: { x: 0, y: 75, z: 0 } }, // Confronts & aims firearm
        { time: 5.5, position: { x: -2.6, y: 0, z: 1.15 }, rotation: { x: 0, y: 75, z: 0 } }, // Fires 2 rounds
        { time: 6.8, position: { x: -3.1, y: 0, z: 0.6 }, rotation: { x: 0, y: 250, z: 0 } }, // Turns back
        { time: 10.0, position: { x: -3.85, y: 0, z: 0.0 }, rotation: { x: 0, y: 250, z: 0 } }, // Flees out doorway
      ],
    },
    {
      id: "victim_1",
      name: "Suresh Gupta (Victim)",
      role: "victim",
      position: { x: 1.6, y: 0, z: -0.4 },
      rotation: { x: 0, y: 255, z: 0 },
      waypoints: [
        { time: 0.0, position: { x: 1.2, y: 0, z: -0.2 }, rotation: { x: 0, y: 255, z: 0 } },  // Standing near table
        { time: 2.5, position: { x: 1.4, y: 0, z: -0.3 }, rotation: { x: 0, y: 255, z: 0 } },  // Steps back in surprise
        { time: 4.8, position: { x: 1.6, y: 0, z: -0.4 }, rotation: { x: 0, y: 255, z: 0 } },  // Standing confrontation
        { time: 5.2, position: { x: 1.62, y: 0, z: -0.4 }, rotation: { x: 0, y: 255, z: 0 } }, // Struck by gunshot
        { time: 6.0, position: { x: 1.65, y: 0, z: -0.4 }, rotation: { x: 0, y: 255, z: 0 } }, // Collapses to floor
        { time: 10.0, position: { x: 1.65, y: 0, z: -0.4 }, rotation: { x: 0, y: 255, z: 0 } }, // Incapacitated on ground
      ],
    },
  ],

  evidence: [
    {
      id: "ev_casing_1",
      type: "shell_casing_9mm",
      description: "9mm KF fired brass cartridge case #1 (Near shooter foot)",
      position: { x: -2.4, y: 0.02, z: 1.0 },
    },
    {
      id: "ev_casing_2",
      type: "shell_casing_9mm",
      description: "9mm KF fired brass cartridge case #2",
      position: { x: -2.2, y: 0.02, z: 1.35 },
    },
    {
      id: "ev_bullet_hole",
      type: "wall_bullet_hole",
      description: "Bullet penetration mark in East wall plaster (Y = 1.45m)",
      position: { x: 3.98, y: 1.45, z: -0.8 },
    },
    {
      id: "ev_blood_pool",
      type: "blood_pool",
      description: "Primary blood pooling pattern around victim chest/floor",
      position: { x: 1.6, y: 0.02, z: -0.4 },
    },
    {
      id: "ev_weapon",
      type: "firearm_pistol",
      description: "Country-made 7.65mm/9mm pistol discarded near doorway",
      position: { x: -3.6, y: 0.03, z: 0.2 },
    },
  ],

  ballistics: [
    {
      id: "traj_line_1",
      origin: { x: -2.6, y: 1.35, z: 1.15 }, // Gun muzzle height
      target: { x: 3.98, y: 1.45, z: -0.8 },  // Wall impact penetration
      color: "#ff0055",
      label: "Ballistic Trajectory #1",
    },
  ],

  timeline: [
    {
      id: "entry_1",
      event_type: "forced_entry",
      description: "Main wooden door lock forced open from corridor.",
      timestamp: "22:14:00",
      confidence: 0.9,
    },
    {
      id: "confrontation",
      event_type: "verbal_altercation",
      description: "Heated confrontation inside living room reported by neighbors.",
      timestamp: "22:14:10",
      confidence: 0.85,
    },
    {
      id: "discharge",
      event_type: "gunshot_discharge",
      description: "2 rounds discharged from 9mm semi-automatic firearm.",
      timestamp: "22:14:18",
      confidence: 0.98,
      status: "conflict",
    },
    {
      id: "fled",
      event_type: "suspect_escape",
      description: "Suspect seen running down staircase toward ground floor exit.",
      timestamp: "22:14:35",
      confidence: 0.92,
    },
  ],

  conflicts: [
    {
      id: "conflict_distance",
      field: "shooter_distance_meters",
      hypotheses: [
        { id: "hyp_fsl", value: "3.2m (GSR Stippling)", source: "FSL Ballistics", confidence: 0.95 },
        { id: "hyp_wit", value: "4.5m (Room Center)", source: "Eyewitness", confidence: 0.65 },
      ],
    },
  ],
};
