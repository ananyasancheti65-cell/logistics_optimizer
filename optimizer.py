import pandas as pd
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# ── Delivery locations ────────────────────────────────────────────────────────
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
distance_matrix = []
for i in range(num_locations):
    row = []
    for j in range(num_locations):
        if i == j:
            row.append(0)
        else:
            dist = calculate_distance(
                df["lat"][i], df["lon"][i],
                df["lat"][j], df["lon"][j]
            )
            row.append(int(dist * 1000))
    distance_matrix.append(row)

print("✓ Distance matrix created")
print(f"  Example: Depot → Koramangala = {distance_matrix[0][1]/1000:.2f} km")

# ── Data model with capacity constraints ──────────────────────────────────────
def create_data_model():
    data = {}
    data["distance_matrix"] = distance_matrix
    data["num_vehicles"] = 3
    data["depot"] = 0

    # How many packages each stop needs (0 for depot)
    data["demands"] = [0, 3, 2, 4, 3, 2, 3, 4, 2, 3]

    # Each vehicle can carry max 10 packages
    data["vehicle_capacities"] = [10, 10, 10]
    return data

data = create_data_model()

# ── Set up OR-Tools ───────────────────────────────────────────────────────────
manager = pywrapcp.RoutingIndexManager(
    len(data["distance_matrix"]),
    data["num_vehicles"],
    data["depot"]
)
routing = pywrapcp.RoutingModel(manager)

# Distance callback
def distance_callback(from_index, to_index):
    from_node = manager.IndexToNode(from_index)
    to_node   = manager.IndexToNode(to_index)
    return data["distance_matrix"][from_node][to_node]

transit_callback_index = routing.RegisterTransitCallback(distance_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# Capacity callback
def demand_callback(from_index):
    from_node = manager.IndexToNode(from_index)
    return data["demands"][from_node]

demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
routing.AddDimensionWithVehicleCapacity(
    demand_callback_index,
    0,                            # no slack
    data["vehicle_capacities"],   # max capacity per vehicle
    True,                         # start cumul at zero
    "Capacity"
)

# ── Solve ─────────────────────────────────────────────────────────────────────
print("\n🤖 AI is calculating optimal routes...")

search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)
search_parameters.local_search_metaheuristic = (
    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
)
search_parameters.time_limit.seconds = 10

solution = routing.SolveWithParameters(search_parameters)

# ── Print results ─────────────────────────────────────────────────────────────
if solution:
    print("\n✅ Optimal routes found!\n")
    total_distance = 0

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = []
        route_distance = 0
        route_load = 0

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(df["names"][node])
            route_load += data["demands"][node]
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )

        route.append("Depot (Warehouse)")
        route_distance_km = route_distance / 1000

        print(f"🚛 Vehicle {vehicle_id + 1}:")
        print(f"   Route: {' → '.join(route)}")
        print(f"   Packages: {route_load}/10")
        print(f"   Distance: {route_distance_km:.2f} km\n")
        total_distance += route_distance_km

    print(f"📦 Total distance all vehicles: {total_distance:.2f} km")

else:
    print("❌ No solution found.")