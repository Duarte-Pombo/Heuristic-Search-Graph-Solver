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
