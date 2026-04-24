import folium
import pandas as pd

# ── Delivery locations around Bengaluru ───────────────────────────────────────
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
        12.9716,  # Depot
        12.9352,  # Koramangala
        12.9784,  # Indiranagar
        12.9698,  # Whitefield
        12.8458,  # Electronic City
        12.9308,  # Jayanagar
        13.0350,  # Hebbal
        12.9591,  # Marathahalli
        12.9166,  # BTM Layout
        13.0240   # Yeshwanthpur
    ],
    "lon": [
        77.5946,  # Depot
        77.6245,  # Koramangala
        77.6408,  # Indiranagar
        77.7499,  # Whitefield
        77.6603,  # Electronic City
        77.5838,  # Jayanagar
        77.5970,  # Hebbal
        77.7009,  # Marathahalli
        77.6101,  # BTM Layout
        77.5383   # Yeshwanthpur
    ]
}

# ── Create a DataFrame (like a table) ─────────────────────────────────────────
df = pd.DataFrame(locations)
print("Our delivery locations:")
print(df)

# ── Build the map ─────────────────────────────────────────────────────────────
# Centre the map on Bengaluru
city_map = folium.Map(location=[12.9716, 77.5946], zoom_start=12)

# Add each location as a marker on the map
for i, row in df.iterrows():
    if i == 0:
        # Depot gets a special red marker
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=row["names"],
            tooltip=row["names"],
            icon=folium.Icon(color="red", icon="home")
        ).add_to(city_map)
    else:
        # Delivery stops get blue markers
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=row["names"],
            tooltip=row["names"],
            icon=folium.Icon(color="blue", icon="shopping-cart")
        ).add_to(city_map)

# ── Save the map ──────────────────────────────────────────────────────────────
city_map.save("delivery_map.html")
print("\nMap saved! Open delivery_map.html in your browser to see it.")