import numpy as np
import random
import pandas as pd

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

# Delivery stops (everything except depot which is index 0)
stops = list(range(1, num_locations))

# ── Genetic Algorithm ─────────────────────────────────────────────────────────
class GeneticAlgorithm:
    def __init__(self, stops, dist_matrix, population_size=100, generations=500):
        self.stops          = stops
        self.dist_matrix    = dist_matrix
        self.pop_size       = population_size
        self.generations    = generations
        self.best_route     = None
        self.best_distance  = float("inf")
        self.history        = []  # track improvement over generations

    def total_distance(self, route):
        """Calculate total distance of a route starting and ending at depot"""
        dist  = self.dist_matrix[0][route[0]]   # depot → first stop
        for i in range(len(route) - 1):
            dist += self.dist_matrix[route[i]][route[i+1]]
        dist += self.dist_matrix[route[-1]][0]   # last stop → depot
        return dist

    def create_population(self):
        """Create random initial population of routes"""
        population = []
        for _ in range(self.pop_size):
            route = self.stops.copy()
            random.shuffle(route)
            population.append(route)
        return population

    def selection(self, population):
        """
        Tournament selection — pick 2 random routes,
        keep the shorter one (survival of the fittest)
        """
        tournament = random.sample(population, 5)
        return min(tournament, key=self.total_distance)

    def crossover(self, parent1, parent2):
        """
        Ordered crossover — take a slice from parent1,
        fill the rest with parent2's order
        """
        size   = len(parent1)
        start  = random.randint(0, size - 2)
        end    = random.randint(start + 1, size)
        child  = parent1[start:end]
        for gene in parent2:
            if gene not in child:
                child.append(gene)
        return child

    def mutate(self, route, mutation_rate=0.02):
        """
        Mutation — randomly swap 2 stops in the route
        This adds variety so we don't get stuck
        """
        route = route.copy()
        for i in range(len(route)):
            if random.random() < mutation_rate:
                j = random.randint(0, len(route) - 1)
                route[i], route[j] = route[j], route[i]
        return route

    def evolve(self):
        """Main evolution loop"""
        population = self.create_population()
        print(f"🧬 Starting evolution with {self.pop_size} routes...")
        print(f"   Running {self.generations} generations\n")

        for gen in range(self.generations):
            # Sort population by distance (best first)
            population = sorted(population, key=self.total_distance)

            # Track the best route
            current_best = self.total_distance(population[0])
            if current_best < self.best_distance:
                self.best_distance = current_best
                self.best_route    = population[0].copy()

            # Save history every 50 generations
            if gen % 50 == 0:
                self.history.append({
                    "generation": gen,
                    "distance":   round(self.best_distance, 2)
                })
                print(f"   Generation {gen:4d} → Best distance: {self.best_distance:.2f} km")

            # Create next generation
            next_gen = population[:10]  # keep top 10 (elitism)
            while len(next_gen) < self.pop_size:
                parent1 = self.selection(population)
                parent2 = self.selection(population)
                child   = self.crossover(parent1, parent2)
                child   = self.mutate(child)
                next_gen.append(child)

            population = next_gen

        return self.best_route, self.best_distance

# ── Run the Genetic Algorithm ─────────────────────────────────────────────────
print("=" * 50)
print("  GENETIC ALGORITHM ROUTE OPTIMIZER")
print("=" * 50)

ga = GeneticAlgorithm(
    stops           = stops,
    dist_matrix     = dist_matrix,
    population_size = 100,
    generations     = 500
)

best_route, best_distance = ga.evolve()

# ── Print results ─────────────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("  BEST ROUTE FOUND")
print("=" * 50)

route_names = (
    ["Depot (Warehouse)"] +
    [df["names"][i] for i in best_route] +
    ["Depot (Warehouse)"]
)

print(f"\n🏆 Best route:")
print("   " + " → ".join(route_names))
print(f"\n📏 Total distance: {best_distance:.2f} km")

# Compare with simple sequential route
sequential = list(range(1, num_locations))
seq_distance = ga.total_distance(sequential)
improvement = ((seq_distance - best_distance) / seq_distance) * 100

print(f"\n📊 Comparison:")
print(f"   Without AI (sequential): {seq_distance:.2f} km")
print(f"   With Genetic Algorithm:  {best_distance:.2f} km")
print(f"   🎯 Improvement: {improvement:.1f}% shorter route!")

print("\n📈 Evolution history:")
for record in ga.history:
    bar = "█" * int(record["distance"] / 5)
    print(f"   Gen {record['generation']:4d}: {record['distance']:6.2f} km  {bar}")