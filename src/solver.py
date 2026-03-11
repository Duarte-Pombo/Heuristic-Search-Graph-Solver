"""
Implements various heuristics for the optimization problem.
"""

from src.simulator import simulate_assignment, manhattan_distance


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
        # Find vehicle that can complete this ride on time
        best_vehicle = None
        best_cost = (float('inf'), float('inf'))

        for vehicle_id in range(problem.fleet_size):
            # Simulate adding this ride to vehicle
            test_assignment = {k: list(v) for k, v in assignment.items()}
            test_assignment[vehicle_id].append(ride.id)

            score, vehicles = simulate_assignment(problem, test_assignment)
            current_vehicle = vehicles[vehicle_id]

            # Cost: prefer vehicle that finishes on time and is closer
            if current_vehicle.current_time <= problem.time_steps:
                cost = (
                    manhattan_distance(current_vehicle.position, ride.start),
                    current_vehicle.current_time
                )
                if cost < best_cost:
                    best_vehicle = vehicle_id
                    best_cost = cost

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
