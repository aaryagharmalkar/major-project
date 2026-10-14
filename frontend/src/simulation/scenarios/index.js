import { delhiAccidentScene } from "./delhiAccidentScene";
import { indoorShootingScene } from "./indoorShootingScene";

export const SCENARIO_REGISTRY = {
  case_001: {
    id: "case_001",
    name: "Case 001: Delhi T-Point Collision",
    category: "Traffic Collision",
    data: delhiAccidentScene,
  },
  case_002: {
    id: "case_002",
    name: "Case 002: Rohini Flat 302 Shootout",
    category: "Indoor Ballistics / Crime Scene",
    data: indoorShootingScene,
  },
};
