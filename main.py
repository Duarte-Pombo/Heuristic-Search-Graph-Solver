#!/usr/bin/env python3
"""
Hash Code 2018 Self-driving Rides - Main entry point.
Usage: python main.py <input_file> <output_file> [solver]
"""

import sys
import copy
import datetime
import os

from src.parser import parse_input
from src.solvers.greedy_solver import greedy_solver
from src.solvers.nearest_solver import nearest_vehicle_solver
from src.solvers.multiagent_solver import multiagent_solver
from src.solvers.genetic_solver import genetic_solver
from src.solvers.backtracking_solver import backtracking_solver
from src.solvers.simulated_annealing_solver import simulated_annealing_solver
from src.simulator import simulate_assignment, validate_assignment
from src.writer import write_solution

class DualLogger:
    def __init__(self, filepath):
        self.terminal = sys.stdout
        # extend the existing file
        self.log = open(filepath, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush() # Forces Python to write to the file immediately

    def flush(self):
        self.terminal.flush()
        self.log.flush()


def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_file> <output_file> [greedy|nearest|annealing|multiagent|genetic|backtracking]")
        sys.exit(1)

    # Grab the arguments
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    solver_name = sys.argv[3] if len(sys.argv) > 3 else "greedy"

    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    input_basename = os.path.splitext(os.path.basename(input_file))[0]

    log_filename = os.path.join(log_dir, f"{solver_name}_{input_basename}_logs.txt")
    sys.stdout = DualLogger(log_filename)

    # Print a detailed header
    print(f"{'=' * 40}")
    print(f"NEW RUN: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"DATASET: {input_file}")
    print(f"{'=' * 40}")

    # Parse input
    problem = parse_input(input_file)
    print(f"Parsed: {problem.num_rides} rides, {problem.fleet_size} vehicles")
    print(f"Grid: {problem.rows}x{problem.cols}, Time: {problem.time_steps} steps, Bonus: {problem.bonus}")

    # Solve
    if solver_name == "nearest":
        assignment = nearest_vehicle_solver(problem)
    elif solver_name == "annealing":
        assignment = simulated_annealing_solver(problem)
    elif solver_name == "multiagent":
        assignment = multiagent_solver(problem)
    elif solver_name == "genetic" :
        assignment = genetic_solver(problem)
    elif solver_name == "backtracking" :
        assignment = backtracking_solver() # experimental algorithm, might not work
    else:
        assignment = greedy_solver(problem)

    # Validate
    if not validate_assignment(assignment, problem.num_rides):
        print("ERROR: Invalid assignment generated")
        sys.exit(1)

    # Simulate and score
    score, vehicles = simulate_assignment(problem, copy.deepcopy(assignment))
    print(f"\nAssignment: {solver_name} solver")
    print(f"Total score: {score}")

    for vehicle_id, vehicle in vehicles.items():
        assigned_count = len(assignment[vehicle_id])
        print(f"  Vehicle {vehicle_id}: {assigned_count} rides, score: {vehicle.score}")

    # Write solution
    write_solution(output_file, assignment, problem.fleet_size)
    print(f"\nSolution written to {output_file}\n")


if __name__ == "__main__":
    main()
