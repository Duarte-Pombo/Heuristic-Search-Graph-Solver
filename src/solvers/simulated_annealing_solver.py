from src.simulator import simulate_assignment, manhattan_distance
from src.solvers.greedy_solver import greedy_solver
from src.solvers.nearest_solver import nearest_vehicle_solver
from src.solvers.multiagent_solver import multiagent_solver

import random
import math
import copy


def mutate_assignment(assignment, problem):
    """
    problem: The Problem object containing the list of Ride objects
    assignment: The current dict of {vehicle_id: [ride_ids]}
    """

    # Helper to sort by the ride's earliest start time
    def sort_rides(ride_list):
        # We look up the ride data using the ride_id from problem.rides
        ride_list.sort(key=lambda r_id: problem.rides[r_id].earliest_start)

    v_ids = list(assignment.keys())
    active_vehicles = [v for v in v_ids if assignment[v]]
    inactive_vehicles = [v for v in v_ids if not assignment[v]]
    n_in = len(inactive_vehicles)

    # Shallow copy for speed
    new_assignment = assignment.copy()
    mutation_type = random.choice(['shift', 'swap', 'tail_shift'])

    if mutation_type == 'shift' and active_vehicles:
        v_from = random.choice(active_vehicles)
        v_to = random.choice(inactive_vehicles) if (inactive_vehicles and random.random() < 0.5) else random.choice(
            v_ids)

        if v_from == v_to: return new_assignment, n_in

        list_from, list_to = list(new_assignment[v_from]), list(new_assignment[v_to])
        ride = list_from.pop(random.randrange(len(list_from)))

        list_to.append(ride)
        sort_rides(list_to)  # Puts the ride in the best chronological spot

        new_assignment[v_from], new_assignment[v_to] = list_from, list_to

    elif mutation_type == 'tail_shift' and active_vehicles:
        v_from = random.choice(active_vehicles)
        v_to = random.choice(inactive_vehicles) if inactive_vehicles else random.choice(v_ids)
        if v_from == v_to: return new_assignment, n_in

        list_from, list_to = list(new_assignment[v_from]), list(new_assignment[v_to])
        idx = random.randrange(len(list_from))

        list_to.extend(list_from[idx:])
        new_list_from = list_from[:idx]

        sort_rides(list_to)  # Re-order the entire chain for the new car
        new_assignment[v_from], new_assignment[v_to] = new_list_from, list_to

    elif mutation_type == 'swap' and active_vehicles:
        v1 = random.choice(active_vehicles)
        v2 = random.choice(v_ids)
        if v1 == v2: return new_assignment, n_in

        list1, list2 = list(new_assignment[v1]), list(new_assignment[v2])

        # Take a ride from V1
        ride1 = list1.pop(random.randrange(len(list1)))

        if list2:
            # Swap with a ride from V2
            ride2 = list2.pop(random.randrange(len(list2)))
            list1.append(ride2)
            sort_rides(list1)

        list2.append(ride1)
        sort_rides(list2)

        new_assignment[v1], new_assignment[v2] = list1, list2

    return new_assignment, n_in

def simulated_annealing_solver(problem):
    """
    Simulated Annealing optimization.
    Starts with the greedy solution and iteratively tries to improve it.
    """
    print("Generating initial greedy assignment...")
    current_assignment_greedy = greedy_solver(problem)
    current_score_greedy, _ = simulate_assignment(problem, current_assignment_greedy)
    print(f"Greedy provides an initial score of {current_score_greedy}\n")
    #current_score_greedy = 0

    print("Generating initial nearest assignment...")
    current_assignment_nearest = nearest_vehicle_solver(problem)
    current_score_nearest, _ = simulate_assignment(problem, current_assignment_nearest)
    print(f"Nearest provides an initial score of {current_score_nearest}\n")

    print("Generating initial multi agent assignment...")
    current_assignment_multi = multiagent_solver(problem)
    current_score_multi, _ = simulate_assignment(problem, current_assignment_multi)
    print(f"Multi agents provides an initial score of {current_score_multi}\n")

    # Track the absolute best score we've ever seen
    if current_score_greedy > current_score_nearest and current_score_greedy > current_score_multi:
        print("Greedy provided the best initial score.")
        best_assignment = copy.deepcopy(current_assignment_greedy)
        best_score = current_score_greedy
    elif current_score_nearest > current_score_greedy and current_score_nearest > current_score_multi:
        print("Nearest provides the best initial score.")
        best_assignment = copy.deepcopy(current_assignment_nearest)
        best_score = current_score_nearest
    else:
        print("Multi agent provides the best initial score")
        best_assignment = copy.deepcopy(current_assignment_multi)
        best_score = current_score_multi

    current_assignment = copy.deepcopy(best_assignment)
    current_score = best_score
    starting_score = best_score

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

    last_upgrade = 0
    inactive_vehicles = [v for v, rides in current_assignment.items() if len(rides) == 0]
    n_in = len(inactive_vehicles)
    n_in_start = n_in

    for i in range(max_iter):
        if temp <= min_temp:
            break

        # Get a mutated neighbor
        neighbor_assignment, n_in = mutate_assignment(current_assignment, problem)

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
                last_upgrade = -1
                # Can be uncommented to properly display algorithm behavior, generates unnecessary prints
                #print(f"Iteration {i}: New Best Score -> {best_score}")

        else:
            # Worse solution. Calculate probability of accepting it anyway.
            probability = math.exp(delta_s / temp)

            if random.random() < probability:
                # Accept a worse move to escape local maximums
                current_assignment = neighbor_assignment
                current_score = neighbor_score

                # This generates too many prints, can be uncommented to display that the algorithm actually considers the worse solutions
                #print(f"Iteration {i}: Accepted WORSE score -> {current_score} (Temp: {temp:.2f})")

        # Decrease the temperature
        temp *= cooling_rate

        last_upgrade += 1

    print(f"\nFinished Simulated Annealing. Final Best Score: {best_score}")

    improvement = best_score - starting_score
    improv_percent = (improvement/starting_score) * 100
    print(f"Score grew by {improv_percent:.2f}% from {starting_score} to {best_score}")
    print(f"Scored last improved {last_upgrade} iterations ago")
    print(f"Inactive vehicles left: {n_in} from {n_in_start}")
    return best_assignment
