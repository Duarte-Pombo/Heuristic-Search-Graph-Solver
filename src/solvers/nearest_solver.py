from src.simulator import simulate_assignment, manhattan_distance

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
