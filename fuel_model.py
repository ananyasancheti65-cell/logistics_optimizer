import numpy as np
import pandas as pd
import random

# ── Locations ─────────────────────────────────────────────────────────────────
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

# ── Distance calculator ───────────────────────────────────────────────────────
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# Build distance matrix
num_locations = len(df)
dist_matrix = np.zeros((num_locations, num_locations))
for i in range(num_locations):
    for j in range(num_locations):
        if i != j:
            dist_matrix[i][j] = calculate_distance(
                df["lat"][i], df["lon"][i],
                df["lat"][j], df["lon"][j]
            )

# ── Traffic Model ─────────────────────────────────────────────────────────────
# Traffic multipliers by hour of day
# 1.0 = normal, 1.5 = slow, 2.0 = very slow (rush hour)
def get_traffic_multiplier(hour):
    if 8 <= hour <= 10:    # Morning rush
        return 2.0
    elif 17 <= hour <= 19: # Evening rush
        return 1.8
    elif 12 <= hour <= 14: # Lunch hour
        return 1.3
    elif 22 <= hour or hour <= 6:  # Night
        return 0.8
    else:
        return 1.0         # Normal

# ── Fuel Cost Model ───────────────────────────────────────────────────────────
FUEL_PRICE_PER_LITRE = 102.0  # INR (Bengaluru diesel price)
FUEL_CONSUMPTION     = 10.0   # km per litre (delivery van)

def calculate_fuel_cost(distance_km, traffic_multiplier):
    """
    More traffic = more fuel burned
    At multiplier 2.0 (rush hour), fuel consumption goes up 40%
    """
    adjusted_consumption = FUEL_CONSUMPTION / traffic_multiplier
    litres_used = distance_km / adjusted_consumption
    cost = litres_used * FUEL_PRICE_PER_LITRE
    return round(cost, 2), round(litres_used, 2)

# ── Time Window Model ─────────────────────────────────────────────────────────
# Each delivery stop has a time window — must arrive between these hours
time_windows = {
    "Koramangala":    (9, 12),   # Morning delivery
    "Indiranagar":    (10, 13),
    "Whitefield":     (9, 11),   # Early morning only
    "Electronic City":(14, 17),  # Afternoon delivery
    "Jayanagar":      (10, 14),
    "Hebbal":         (9, 12),
    "Marathahalli":   (13, 16),  # Afternoon
    "BTM Layout":     (11, 15),
    "Yeshwanthpur":   (9, 11),   # Early morning only
}

# ── Our best route from Genetic Algorithm ────────────────────────────────────
best_route = [
    "Depot (Warehouse)",
    "Yeshwanthpur",
    "Hebbal",
    "Indiranagar",
    "Marathahalli",
    "Whitefield",
    "Electronic City",
    "Koramangala",
    "BTM Layout",
    "Jayanagar",
    "Depot (Warehouse)"
]

# ── Simulate the delivery run ─────────────────────────────────────────────────
print("=" * 60)
print("  FUEL COST & TRAFFIC ANALYSIS")
print("=" * 60)
print(f"\n  Fuel price : ₹{FUEL_PRICE_PER_LITRE}/litre")
print(f"  Vehicle    : {FUEL_CONSUMPTION} km/litre\n")
print("=" * 60)

START_HOUR     = 9.0   # Depart depot at 9 AM
AVG_SPEED_KMH  = 30.0  # Average city speed in normal traffic

current_hour   = START_HOUR
total_cost     = 0
total_litres   = 0
total_distance = 0
on_time        = 0
late           = 0

print(f"\n🕘 Departure from Depot at {int(START_HOUR)}:00 AM\n")

for i in range(len(best_route) - 1):
    origin      = best_route[i]
    destination = best_route[i + 1]

    # Get location indices
    orig_idx = df[df["names"] == origin].index[0]
    dest_idx = df[df["names"] == destination].index[0]

    # Distance
    distance = dist_matrix[orig_idx][dest_idx]

    # Traffic at current hour
    traffic = get_traffic_multiplier(int(current_hour))

    # Actual travel time (slower in traffic)
    travel_time_hrs = (distance / AVG_SPEED_KMH) * traffic

    # Arrival time
    arrival_hour = current_hour + travel_time_hrs
    arrival_hhmm = f"{int(arrival_hour):02d}:{int((arrival_hour % 1) * 60):02d}"

    # Fuel cost
    cost, litres = calculate_fuel_cost(distance, traffic)
    total_cost     += cost
    total_litres   += litres
    total_distance += distance

    # Check time window
    if destination != "Depot (Warehouse)":
        window = time_windows.get(destination, (8, 18))
        in_window = window[0] <= arrival_hour <= window[1]
        status = "✅ On time" if in_window else "⚠️  Late"
        if in_window:
            on_time += 1
        else:
            late += 1
        window_str = f"  Window: {window[0]}:00–{window[1]}:00  {status}"
    else:
        window_str = "  Returning to depot"

    traffic_label = {2.0: "🔴 Rush hour", 1.8: "🟠 Heavy", 
                     1.3: "🟡 Moderate", 0.8: "🟢 Clear", 
                     1.0: "🟢 Normal"}[traffic]

    print(f"📍 {origin} → {destination}")
    print(f"   Distance : {distance:.2f} km")
    print(f"   Traffic  : {traffic_label} (×{traffic})")
    print(f"   Arrival  : {arrival_hhmm}")
    print(f"   Fuel cost: ₹{cost} ({litres}L)")
    print(f"{window_str}")
    print()

    # Add 15 min stop at each delivery
    current_hour = arrival_hour + 0.25

# ── Summary ───────────────────────────────────────────────────────────────────
print("=" * 60)
print("  SUMMARY")
print("=" * 60)
print(f"  Total distance : {total_distance:.2f} km")
print(f"  Total fuel     : {total_litres:.2f} litres")
print(f"  Total cost     : ₹{total_cost:.2f}")
print(f"  On-time stops  : {on_time}/{on_time + late}")
print(f"  Late stops     : {late}/{on_time + late}")

# Cost comparison — optimized vs unoptimized
unoptimized_cost = (110.95 / FUEL_CONSUMPTION) * FUEL_PRICE_PER_LITRE
savings = unoptimized_cost - total_cost
print(f"\n💰 Cost without AI : ₹{unoptimized_cost:.2f}")
print(f"💰 Cost with AI    : ₹{total_cost:.2f}")
print(f"💸 Money saved     : ₹{savings:.2f} per delivery run!")
print(f"\n   Per month (25 working days): ₹{savings * 25:.2f} saved")
print(f"   Per year                   : ₹{savings * 300:.2f} saved")