"""
Executes rides and computes scores.
"""

def manhattan_distance(pos1, pos2):
    """Calculate Manhattan distance between two positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def simulate_assignment(problem, assignment):
    """
    Simulate vehicle assignments and compute total score.

    Args:
        problem: Problem object
        assignment: dict mapping vehicle_id -> list of ride ids

    Returns:
        tuple (total_score, vehicles_state)
    """
    vehicles = {i: Vehicle(i) for i in range(problem.fleet_size)}

    for vehicle_id, ride_ids in assignment.items():
        vehicle = vehicles[vehicle_id]

        for ride_id in ride_ids:
            ride = problem.rides[ride_id]

            # Drive to start intersection
            travel_dist = manhattan_distance(vehicle.position, ride.start)
            vehicle.current_time += travel_dist
            vehicle.position = ride.start

            # Wait if needed
            if vehicle.current_time < ride.earliest_start:
                vehicle.current_time = ride.earliest_start

            start_time = vehicle.current_time

            # Drive to finish
            travel_dist = ride.distance
            vehicle.current_time += travel_dist
            finish_time = vehicle.current_time
            vehicle.position = ride.finish

            # Calculate score
            if finish_time <= ride.latest_finish:
                ride_score = ride.distance
                if start_time == ride.earliest_start:
                    ride_score += problem.bonus
                vehicle.score += ride_score

    total_score = sum(v.score for v in vehicles.values())
    return total_score, vehicles


def validate_assignment(assignment, num_rides):
    """Validate that assignment is valid (each ride assigned at most once)."""
    assigned = set()
    for vehicle_id, ride_ids in assignment.items():
        for ride_id in ride_ids:
            if ride_id in assigned:
                return False
            if ride_id >= num_rides or ride_id < 0:
                return False
            assigned.add(ride_id)
    return True
