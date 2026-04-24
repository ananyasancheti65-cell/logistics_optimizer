import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Logistics Route Optimizer",
    page_icon="🚛",
    layout="wide"
)

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

# ── Helpers ───────────────────────────────────────────────────────────────────
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def build_distance_matrix():
    n = len(df)
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(0)
            else:
                d = calculate_distance(
                    df["lat"][i], df["lon"][i],
                    df["lat"][j], df["lon"][j]
                )
                row.append(int(d * 1000))
        matrix.append(row)
    return matrix

def get_traffic_multiplier(hour):
    if 8 <= hour <= 10:    return 2.0
    elif 17 <= hour <= 19: return 1.8
    elif 12 <= hour <= 14: return 1.3
    elif 22 <= hour or hour <= 6: return 0.8
    else: return 1.0

def run_optimizer(num_vehicles, capacity, demands):
    distance_matrix = build_distance_matrix()
    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix), num_vehicles, 0
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return distance_matrix[
            manager.IndexToNode(from_index)
        ][manager.IndexToNode(to_index)]

    transit_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    def demand_callback(from_index):
        return demands[manager.IndexToNode(from_index)]

    demand_idx = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_idx, 0, [capacity] * num_vehicles, True, "Capacity"
    )

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.time_limit.seconds = 5

    solution = routing.SolveWithParameters(params)
    routes = []

    if solution:
        for vid in range(num_vehicles):
            index = routing.Start(vid)
            route = []
            dist  = 0
            load  = 0
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                route.append(node)
                load += demands[node]
                prev  = index
                index = solution.Value(routing.NextVar(index))
                dist += routing.GetArcCostForVehicle(prev, index, vid)
            route.append(0)
            routes.append({
                "vehicle":  vid + 1,
                "route":    route,
                "distance": dist / 1000,
                "load":     load
            })
    return routes

# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🚛 Intelligent Logistics & Route Optimizer")
st.markdown("AI-powered fleet management for Bengaluru deliveries")

# Sidebar controls
st.sidebar.header("⚙️ Fleet Settings")
num_vehicles = st.sidebar.slider("Number of vehicles", 1, 5, 3)
capacity     = st.sidebar.slider("Vehicle capacity (packages)", 5, 20, 10)
start_hour   = st.sidebar.slider("Departure time (hour)", 6, 12, 9)
fuel_price   = st.sidebar.slider("Fuel price (₹/litre)", 90, 120, 102)

st.sidebar.header("📦 Delivery Demands")
demands = [0]  # depot = 0
for i in range(1, len(df)):
    d = st.sidebar.number_input(
        df["names"][i], min_value=1, max_value=10, value=3
    )
    demands.append(d)

# Run optimizer
if st.button("🤖 Optimize Routes", type="primary"):
    with st.spinner("AI is calculating optimal routes..."):
        routes = run_optimizer(num_vehicles, capacity, demands)

    if routes:
        # ── Metrics row ───────────────────────────────────────────────────────
        total_dist = sum(r["distance"] for r in routes)
        total_pkgs = sum(r["load"] for r in routes)
        fuel_used  = total_dist / 10
        fuel_cost  = fuel_used * fuel_price

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Distance",  f"{total_dist:.1f} km")
        col2.metric("Total Packages",  f"{total_pkgs}")
        col3.metric("Fuel Used",       f"{fuel_used:.1f} L")
        col4.metric("Fuel Cost",       f"₹{fuel_cost:.0f}")

        st.markdown("---")

        # ── Map + Route details side by side ──────────────────────────────────
        map_col, info_col = st.columns([3, 2])

        colors = ["red", "blue", "green", "purple", "orange"]

        with map_col:
            st.subheader("🗺️ Optimized Routes Map")
            city_map = folium.Map(
                location=[12.9716, 77.5946], zoom_start=12
            )

            for r in routes:
                color = colors[r["vehicle"] - 1]
                coords = [
                    [df["lat"][n], df["lon"][n]]
                    for n in r["route"]
                ]
                folium.PolyLine(
                    coords, color=color, weight=4, opacity=0.8,
                    tooltip=f"Vehicle {r['vehicle']} | {r['distance']:.1f} km"
                ).add_to(city_map)

                for idx, node in enumerate(r["route"]):
                    if node == 0:
                        folium.Marker(
                            [df["lat"][0], df["lon"][0]],
                            popup="🏭 Depot",
                            icon=folium.Icon(color="black", icon="home")
                        ).add_to(city_map)
                    else:
                        folium.Marker(
                            [df["lat"][node], df["lon"][node]],
                            popup=df["names"][node],
                            tooltip=f"{df['names'][node]} (V{r['vehicle']})",
                            icon=folium.Icon(color=color, icon="info-sign")
                        ).add_to(city_map)

            st_folium(city_map, width=700, height=450)

        with info_col:
            st.subheader("📋 Route Details")
            for r in routes:
                color = colors[r["vehicle"] - 1]
                route_names = [df["names"][n] for n in r["route"]]

                traffic = get_traffic_multiplier(start_hour)
                adj_fuel = (r["distance"] / 10) * traffic * fuel_price

                with st.expander(
                    f"🚛 Vehicle {r['vehicle']} — {r['distance']:.1f} km",
                    expanded=True
                ):
                    st.write("**Route:**")
                    st.write(" → ".join(route_names))
                    st.write(f"**Packages:** {r['load']}/{capacity}")
                    st.write(f"**Fuel cost:** ₹{adj_fuel:.0f}")
                    traffic_label = {
                        2.0: "🔴 Rush hour",
                        1.8: "🟠 Heavy",
                        1.3: "🟡 Moderate",
                        0.8: "🟢 Clear",
                        1.0: "🟢 Normal"
                    }[traffic]
                    st.write(f"**Traffic:** {traffic_label}")
    else:
        st.error("No solution found. Try reducing demands or increasing capacity.")

else:
    # Default map before optimizing
    st.subheader("📍 Delivery Locations")
    city_map = folium.Map(location=[12.9716, 77.5946], zoom_start=12)
    for i, row in df.iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=row["names"],
            tooltip=row["names"],
            icon=folium.Icon(
                color="red" if i == 0 else "blue",
                icon="home" if i == 0 else "info-sign"
            )
        ).add_to(city_map)
    st_folium(city_map, width=900, height=450)
    st.info("👆 Adjust settings in the sidebar and click **Optimize Routes** to run the AI!")