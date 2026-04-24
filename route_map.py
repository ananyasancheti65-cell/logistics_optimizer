import folium
import pandas as pd
import numpy as np

# ── Same locations ────────────────────────────────────────────────────────────
locations = {
    "names": [
        "Depot (Warehouse)",
        "Koramangala",
        "Indiranagar",
        "Whitefield",
        "Electronic City",
        "Jayanagar",
        "Hebbal",
        "Marathahalli",
        "BTM Layout",
        "Yeshwanthpur"
    ],
    "lat": [
        12.9716, 12.9352, 12.9784, 12.9698, 12.8458,
        12.9308, 13.0350, 12.9591, 12.9166, 13.0240
    ],
    "lon": [
        77.5946, 77.6245, 77.6408, 77.7499, 77.6603,
        77.5838, 77.5970, 77.7009, 77.6101, 77.5383
    ]
}

df = pd.DataFrame(locations)

# ── Optimized routes from our AI ──────────────────────────────────────────────
routes = {
    "Vehicle 1": {
        "stops": ["Depot (Warehouse)", "Hebbal", "Yeshwanthpur", "Depot (Warehouse)"],
        "color": "red",
        "distance": 21.96,
        "packages": 6
    },
    "Vehicle 2": {
        "stops": ["Depot (Warehouse)", "Koramangala", "Electronic City",
                  "BTM Layout", "Jayanagar", "Depot (Warehouse)"],
        "color": "blue",
        "distance": 33.37,
        "packages": 10
    },
    "Vehicle 3": {
        "stops": ["Depot (Warehouse)", "Indiranagar", "Whitefield",
                  "Marathahalli", "Depot (Warehouse)"],
        "color": "green",
        "distance": 33.97,
        "packages": 10
    }
}

# ── Build the map ─────────────────────────────────────────────────────────────
city_map = folium.Map(location=[12.9716, 77.5946], zoom_start=12)

# Helper: get lat/lon for a location name
def get_coords(name):
    row = df[df["names"] == name].iloc[0]
    return [row["lat"], row["lon"]]

# Draw each vehicle's route
for vehicle, info in routes.items():
    stops     = info["stops"]
    color     = info["color"]
    distance  = info["distance"]
    packages  = info["packages"]

    # Draw lines connecting the stops
    coords = [get_coords(stop) for stop in stops]
    folium.PolyLine(
        coords,
        color=color,
        weight=4,
        opacity=0.8,
        tooltip=f"{vehicle} | {distance} km | {packages} packages"
    ).add_to(city_map)

    # Add markers for each stop
    for i, stop in enumerate(stops):
        coords_point = get_coords(stop)

        if stop == "Depot (Warehouse)":
            # Depot marker
            folium.Marker(
                location=coords_point,
                popup="🏭 Depot (Warehouse)",
                tooltip="Depot",
                icon=folium.Icon(color="black", icon="home")
            ).add_to(city_map)
        else:
            # Delivery stop marker
            folium.Marker(
                location=coords_point,
                popup=f"{stop}<br>{vehicle}",
                tooltip=f"{stop} ({vehicle})",
                icon=folium.Icon(color=color, icon="shopping-cart")
            ).add_to(city_map)

# ── Add a legend ──────────────────────────────────────────────────────────────
legend_html = """
<div style="position: fixed; bottom: 40px; left: 40px; z-index: 1000;
     background: white; padding: 15px; border-radius: 10px;
     border: 2px solid grey; font-size: 14px;">
  <b>🚛 Fleet Routes</b><br><br>
  <span style="color:red">●</span> Vehicle 1 — 21.96 km — 6 packages<br>
  <span style="color:blue">●</span> Vehicle 2 — 33.37 km — 10 packages<br>
  <span style="color:green">●</span> Vehicle 3 — 33.97 km — 10 packages<br>
  <br><b>Total: 89.30 km</b>
</div>
"""
city_map.get_root().html.add_child(folium.Element(legend_html))

# ── Save ──────────────────────────────────────────────────────────────────────
city_map.save("optimized_routes.html")
print("✅ Map saved! Open optimized_routes.html in your browser.")