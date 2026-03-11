def write_solution(filename, assignment, fleet_size):
    """
    Write solution to output file.

    Args:
        filename: Output file path
        assignment: dict mapping vehicle_id -> list of ride ids
        fleet_size: Number of vehicles in fleet
    """
    with open(filename, 'w') as f:
        for vehicle_id in range(fleet_size):
            ride_ids = assignment.get(vehicle_id, [])
            line = str(len(ride_ids))
            if ride_ids:
                line += ' ' + ' '.join(map(str, ride_ids))
            f.write(line + '\n')


def read_solution(filename):
    """
    Read solution from output file.

    Args:
        filename: Solution file path

    Returns:
        dict mapping vehicle_id -> list of ride ids
    """
    assignment = {}
    with open(filename, 'r') as f:
        for vehicle_id, line in enumerate(f):
            parts = list(map(int, line.split()))
            num_rides = parts[0]
            ride_ids = parts[1:num_rides + 1] if num_rides > 0 else []
            assignment[vehicle_id] = ride_ids
    return assignment
