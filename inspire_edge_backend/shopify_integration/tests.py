import json

# Load original JSON
with open("input.json", "r") as f:
    data = json.load(f)

# Dictionary to track user info and spaces
user_space_map = {}

for space_key, space in data.items():
    for user in space.get("users_with_access", []):
        user_id = user["id"]
        if user_id not in user_space_map:
            user_space_map[user_id] = {
                "id": user_id,
                "name": user["name"],
                "spaces": [space_key]
            }
        else:
            user_space_map[user_id]["spaces"].append(space_key)

# Add space count to each user
for user in user_space_map.values():
    user["space_count"] = len(user["spaces"])

# Convert to list
output = list(user_space_map.values())

# Save to JSON
with open("user_space_counts.json", "w") as f:
    json.dump(output, f, indent=2)
