"""
Implements various heuristics for the optimization problem.
"""

from src.simulator import simulate_assignment, manhattan_distance

import random
import math
import copy

def mutate_assignment(assignment, num_vehicles):
    """
    Neighborhood Function: Creates a neighboring solution by mutating the current one.
    It randomly chooses to either 'shift' a ride to another vehicle, or 'swap' two rides.
    """
    new_assignment = copy.deepcopy(assignment)

    active_vehicles = [v for v, rides in new_assignment.items() if len(rides) > 0]
    if not active_vehicles:
        return new_assignment

    mutation_type = random.choice(['shift', 'swap'])

    if mutation_type == 'shift':
        # Take a ride from a random active vehicle and give it to any vehicle
        v_from = random.choice(active_vehicles)
        v_to = random.choice(range(num_vehicles))

        if new_assignment[v_from]:
            # Pop a random ride from the source vehicle
            ride_idx = random.randrange(len(new_assignment[v_from]))
            ride = new_assignment[v_from].pop(ride_idx)

            # Generate all valid insertion indices
            possible_insertions = list(range(len(new_assignment[v_to]) + 1))

            # If it's the same car, the ride can not be placed in the same spot it came from
            if v_from == v_to and len(possible_insertions) > 1:
                possible_insertions.remove(ride_idx)

            # Insert it at a random valid position
            insert_idx = random.choice(possible_insertions)
            new_assignment[v_to].insert(insert_idx, ride)

    elif mutation_type == 'swap':
        # Exchange two rides between two different active vehicles
        if len(active_vehicles) >= 2:
            v1, v2 = random.sample(active_vehicles, 2)
            if new_assignment[v1] and new_assignment[v2]:
                idx1 = random.randrange(len(new_assignment[v1]))
                idx2 = random.randrange(len(new_assignment[v2]))

                # Swap the rides
                new_assignment[v1][idx1], new_assignment[v2][idx2] = new_assignment[v2][idx2], new_assignment[v1][idx1]

    return new_assignment


def simulated_annealing_solver(problem):
    """
    Simulated Annealing optimization.
    Starts with the greedy solution and iteratively tries to improve it.
    """
    print("Generating initial greedy assignment...")
    # 1. Initial State: Start with your fast greedy solver
    current_assignment_greedy = greedy_solver(problem)
    current_score_greedy, _ = simulate_assignment(problem, current_assignment_greedy)

    print("Generating initial nearest assignment...\n")
    # 1. Initial State: Start with your fast greedy solver
    current_assignment_nearest = nearest_vehicle_solver(problem)
    current_score_nearest, _ = simulate_assignment(problem, current_assignment_nearest)

    # Track the absolute best score we've ever seen
    if current_score_greedy > current_score_nearest:
        print("Greedy provided the initial best score.")
        best_assignment = copy.deepcopy(current_assignment_greedy)
        best_score = current_score_greedy
    else:
        print("Nearest provides the initial best score.")
        best_assignment = copy.deepcopy(current_assignment_nearest)
        best_score = current_score_nearest

    current_assignment = copy.deepcopy(best_assignment)
    current_score = best_score


    # ==========================================
    # 4. DYNAMIC HYPERPARAMETERS
    # ==========================================
    # Scale iterations based on dataset size (min 2000, max 100k)
    max_iter = max(2000, min(100000, problem.num_rides * 10))

    # Scale initial temp based on the max possible distance/time of the simulation
    initial_temp = max(1000.0, problem.time_steps / 5.0)
    min_temp = 0.1

    # Mathematically perfect cooling rate
    cooling_rate = math.pow((min_temp / initial_temp), (1.0 / max_iter))

    print(f"\n--- Dynamic SA Parameters ---")
    print(f"Iterations:   {max_iter}")
    print(f"Initial Temp: {initial_temp:.1f}")
    print(f"Cooling Rate: {cooling_rate:.6f}")
    print(f"-----------------------------")
    # ==========================================

    temp = initial_temp
    print(f"\nStarting Simulated Annealing (Initial Score: {best_score})")

    for i in range(max_iter):
        if temp <= min_temp:
            break

        # Get a mutated neighbor
        neighbor_assignment = mutate_assignment(current_assignment, problem.fleet_size)

        # Calculate the new score and the score difference
        neighbor_score, _ = simulate_assignment(problem, neighbor_assignment)
        delta_s = neighbor_score - current_score

        if delta_s > 0:
            # Better solution found
            current_assignment = neighbor_assignment
            current_score = neighbor_score

            # Update the global best if needed
            if current_score > best_score:
                best_score = current_score
                best_assignment = copy.deepcopy(current_assignment)
                # Can be uncommented to properly display algorithm behavior, generates unnecessary prints
                print(f"Iteration {i}: New Best Score -> {best_score}")

        else:
            # Worse solution. Calculate probability of accepting it anyway.
            probability = math.exp(delta_s / temp)

            if random.random() < probability:
                # Accept a worse move to escape local maximums
                current_assignment = neighbor_assignment
                current_score = neighbor_score

                # This generates too many prints, can be uncommented to display that the algorithm actually considers the worse solutions
                # print(f"Iteration {i}: Accepted WORSE score -> {current_score} (Temp: {temp:.2f})")

        # Decrease the temperature
        temp *= cooling_rate

    print(f"Finished Simulated Annealing. Final Best Score: {best_score}")
    return best_assignment


def greedy_solver(problem):
    """
    Simple greedy solver: assign rides to nearest available vehicle.
    Prioritizes rides by deadline urgency.
    """

    assignment = {i: [] for i in range(problem.fleet_size)}

    # Sort rides by latest_finish (earlier deadline first)
    sorted_rides = sorted(
        problem.rides,
        key=lambda r: (r.latest_finish, r.distance)
    )

    for ride in sorted_rides:
        best_vehicle = None
        best_cost = (float('inf'), float('inf'))

        # Get the current state of all vehicles BEFORE adding the new ride
        _, vehicles = simulate_assignment(problem, assignment)

        for vehicle_id in range(problem.fleet_size):
            current_vehicle = vehicles[vehicle_id]

            # 1. Calculate distance from vehicle's current position to the ride's start
            dist_to_start = manhattan_distance(current_vehicle.position, ride.start)

            # 2. Calculate when the vehicle arrives at the start intersection
            arrival_time = current_vehicle.current_time + dist_to_start

            # 3. Vehicle might have to wait if it arrives before earliest_start
            start_time = max(arrival_time, ride.earliest_start)

            # 4. Calculate when the ride would be completed
            finish_time = start_time + ride.distance

            # 5. Must finish before the simulation ends AND before the ride's deadline
            if finish_time <= problem.time_steps and finish_time <= ride.latest_finish:

                # Cost: prefer the vehicle that is physically closer, tie-break by earliest finish
                cost = (dist_to_start, finish_time)

                if cost < best_cost:
                    best_vehicle = vehicle_id
                    best_cost = cost

        # Assign to the best vehicle found
        if best_vehicle is not None:
            assignment[best_vehicle].append(ride.id)

    return assignment


def nearest_vehicle_solver(problem):
    """
    Assign each ride to the nearest vehicle.
    Simple and fast approach.
    """
    assignment = {i: [] for i in range(problem.fleet_size)}

    for ride in problem.rides:
        # Find nearest vehicle
        best_vehicle = 0
        best_distance = float('inf')

        score, vehicles = simulate_assignment(problem, assignment)

        for vehicle_id in range(problem.fleet_size):
            vehicle = vehicles[vehicle_id]
            dist = manhattan_distance(vehicle.position, ride.start)
            if dist < best_distance:
                best_distance = dist
                best_vehicle = vehicle_id

        # Try to add ride if it fits in time
        test_assignment = {k: list(v) for k, v in assignment.items()}
        test_assignment[best_vehicle].append(ride.id)

        score, test_vehicles = simulate_assignment(problem, test_assignment)
        test_vehicle = test_vehicles[best_vehicle]

        if test_vehicle.current_time <= problem.time_steps:
            assignment[best_vehicle].append(ride.id)

    return assignment
