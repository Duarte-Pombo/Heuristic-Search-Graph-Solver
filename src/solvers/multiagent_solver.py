"""
Multi-Agent Solver using the Contract Net Protocol.

Each vehicle is an autonomous VehicleAgent with local state.
In each round, the coordinator announces the most urgent available ride.
Each agent makes a bid or abstains if the ride is impossible.
The highest bid wins, and the agent updates its state. This repeats until there are no more rides.
"""

from src.simulator import manhattan_distance

class VehicleAgent:
    """
    Autonomous vehicle with local state: current position and time.
    It has no visibility into the state of other agents.
    """
    def __init__(self, agent_id: int):
        self.agent_id       = agent_id
        self.position       = (0, 0)
        self.current_time   = 0

    def bid(self, ride, problem):
        """
        Returns the expected net score for this race, or “None” if impossible.

        1. Calculate the arrival time at the start of the race
        2. Determine whether the race can be completed within the time limit
        3. If so: score = distance + bonus - downtime penalty
        """

        dist_to_start = manhattan_distance(self.position, ride.start)
        arrival_time = self.current_time + dist_to_start
        start_time = max(arrival_time, ride.earliest_start)
        finish_time = start_time + ride.distance

        # Impossible Ride -> resign
        if finish_time > ride.latest_finish or finish_time > problem.time_steps:
            return None
        
        gain = ride.distance
        bonus = problem.bonus if arrival_time <= ride.earliest_start else 0
        dead_time = dist_to_start + max(0, ride.earliest_start - arrival_time)

        # Keep dead_time weight low so that gains and bonuses take precedence
        return gain + bonus - dead_time * 0.1

    def accept_ride(self, ride):
        """
        Agent won the auction: advances position and internal clock/step. (analogous to simulate_assignment)
        """
        dist_to_start = manhattan_distance(self.position, ride.start)
        self.current_time += dist_to_start
        self.current_time = max(self.current_time, ride.earliest_start)
        self.current_time += ride.distance
        self.position = ride.finish

def _run_auction(agents, ride, problem):
    """
    Announces a race and collects bids from all agents.
    Returns the agent_id of the winner, or None if no agent can complete the race
    """
    best_agent_id = None
    best_bid = float('-inf')

    for agent in agents:
        bid = agent.bid(ride, problem)
        if bid is not None and bid > best_bid:
            best_bid = bid
            best_agent_id = agent.agent_id

    return best_agent_id

def multiagent_solver(problem):
    """
    Orchestrates the multi-agent system.
    Returns an assignment: {vehicle_id: [ride_id, ride_id, ...]}
    """
    agents = [VehicleAgent(i) for i in range(problem.fleet_size)]
    assignment = {i: [] for i in range(problem.fleet_size)}

    # Priority: the tightest deadline first; tie → the shortest race
    sorted_rides = sorted(
        problem.rides,
        key=lambda r: (r.latest_finish, r.distance)
    )

    assigned_count = 0

    for ride in sorted_rides:
        winner_id = _run_auction(agents, ride, problem)

        if winner_id is None:
            continue # any agent can take this ride

        assignment[winner_id].append(ride.id)
        agents[winner_id].accept_ride(ride)
        assigned_count += 1

    print(f"Multi-agent: {assigned_count}/{problem.num_rides} rides assigned.")
    return assignment