import json

from scene.scene_projector import SceneProjector


with open("src/case_summary.json", "r") as f:
    case_data = json.load(f)


projector = SceneProjector()

scene = projector.project(case_data)


print("\n========== SCENE IR ==========\n")

print(
    scene.model_dump_json(
        indent=2
    )
)

print("\n========== SUMMARY ==========\n")

print("Roads:", len(scene.roads))
print("Vehicles:", len(scene.vehicles))
print("Evidence:", len(scene.evidence))
print("Timeline:", len(scene.timeline))
print("Conflicts:", len(scene.conflicts))

for vehicle in scene.vehicles:

    print(
        vehicle.id,
        "→",
        vehicle.make,
        vehicle.model,
        "→",
        vehicle.asset_path,
    )