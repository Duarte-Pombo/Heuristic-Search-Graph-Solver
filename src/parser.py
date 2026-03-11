"""
Reads input file and validates constraints.
"""

class Ride:
    def __init__(self, ride_id, start_r, start_c, finish_r, finish_c, earliest_start, latest_finish):
        self.id = ride_id
        self.start = (start_r, start_c)
        self.finish = (finish_r, finish_c)
        self.earliest_start = earliest_start
        self.latest_finish = latest_finish
        self.distance = abs(start_r - finish_r) + abs(start_c - finish_c)


class Problem:
    def __init__(self, rows, cols, fleet_size, num_rides, bonus, time_steps):
        self.rows = rows
        self.cols = cols
        self.fleet_size = fleet_size
        self.num_rides = num_rides
        self.bonus = bonus
        self.time_steps = time_steps
        self.rides = []


def parse_input(filename):
    """Parse input file and return Problem object."""
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Parse header
    header = list(map(int, lines[0].split()))
    R, C, F, N, B, T = header

    problem = Problem(R, C, F, N, B, T)

    # Parse rides
    for i in range(1, N + 1):
        parts = list(map(int, lines[i].split()))
        a, b, x, y, s, f = parts
        ride = Ride(i - 1, a, b, x, y, s, f)
        problem.rides.append(ride)

    return problem


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        problem = parse_input(sys.argv[1])
        print(f"Parsed: {problem.num_rides} rides, {problem.fleet_size} vehicles")
        print(f"Grid: {problem.rows}x{problem.cols}, Time: {problem.time_steps} steps")
