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

solver_names = {1:"nearest", 2:"greedy", 3:"annealing", 4:"multi", 5:"genetic", 6:"backtracking"}

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

    '''
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_file> <output_file> [greedy|nearest|annealing|multiagent|genetic|backtracking]")
        sys.exit(1)

    # Grab the arguments
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    solver_name = sys.argv[3] if len(sys.argv) > 3 else "greedy"
    '''

    print("Please select the input file.\nFilenames starting with \"g_\" come from the official problem repository")
    for file in os.listdir("input"):
        print(f" - {file}")

    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    out_dir = "output"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    input_file = input("Please indicate the complete name of the input file:\n")
    input_basename = os.path.splitext(os.path.basename(input_file))[0]
    full_input_path = os.path.join("input", input_file)

    print("Please indicate the method to solve the problem:\n1. Nearest vehicle\n2. Greedy solver\n3. Simulated Annealing\n4. Multi-agent solver\n5. Genetic solver")
    solver_number = int(input("Please indicate just the number:\n"))
    solver_name = solver_names[solver_number]
    if not (1 <= solver_number <= 5):
        print("Wrong input")
        sys.exit(1)

    log_filename = os.path.join(log_dir, f"{solver_name}_{input_basename}_logs.txt")
    sys.stdout = DualLogger(log_filename)

    output_file = os.path.join(out_dir, f"{solver_name}_{input_basename}_output.txt")

    # Print a detailed header
    print(f"{'=' * 40}")
    print(f"NEW RUN: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"DATASET: {input_file}")
    print(f"{'=' * 40}")

    # Parse input
    problem = parse_input(full_input_path)
    print(f"Parsed: {problem.num_rides} rides, {problem.fleet_size} vehicles")
    print(f"Grid: {problem.rows}x{problem.cols}, Time: {problem.time_steps} steps, Bonus: {problem.bonus}")

    # Solve
    if solver_number == 1:
        assignment = nearest_vehicle_solver(problem)
    elif solver_number == 2:
        assignment = greedy_solver(problem)
    elif solver_number == 3:
        print("What solver would you like to use for the baseline:\n1. Nearest\n2. Greedy\n3. Multi-agent\n4. Best baseline available")
        solver_number_annealing = int(input("Please indicate just the number:\n"))
        assignment = simulated_annealing_solver(problem,solver_number_annealing)
    elif solver_number == 4:
        assignment = multiagent_solver(problem)
    elif solver_number == 5:
        assignment = genetic_solver(problem)
    elif solver_number == 6 :
        assignment = backtracking_solver() # experimental algorithm, might not work


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
