#!/usr/bin/env python3
"""
Hash Code 2018 Self-driving Rides - Main entry point.
Usage: python main.py <input_file> <output_file> [solver]
"""

import sys
from src.parser import parse_input
from src.solver import greedy_solver, nearest_vehicle_solver
from src.simulator import simulate_assignment, validate_assignment
from src.writer import write_solution


def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_file> <output_file> [greedy|nearest]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    solver_name = sys.argv[3] if len(sys.argv) > 3 else "greedy"

    # Parse input
    problem = parse_input(input_file)
    print(f"Parsed: {problem.num_rides} rides, {problem.fleet_size} vehicles")
    print(f"Grid: {problem.rows}x{problem.cols}, Time: {problem.time_steps} steps, Bonus: {problem.bonus}")

    # Solve
    if solver_name == "nearest":
        assignment = nearest_vehicle_solver(problem)
    else:
        assignment = greedy_solver(problem)

    # Validate
    if not validate_assignment(assignment, problem.num_rides):
        print("ERROR: Invalid assignment generated")
        sys.exit(1)

    # Simulate and score
    score, vehicles = simulate_assignment(problem, assignment)
    print(f"\nAssignment: {solver_name} solver")
    print(f"Total score: {score}")

    for vehicle_id, vehicle in vehicles.items():
        print(f"  Vehicle {vehicle_id}: {len(vehicle.rides)} rides, score: {vehicle.score}")

    # Write solution
    write_solution(output_file, assignment, problem.fleet_size)
    print(f"\nSolution written to {output_file}")


if __name__ == "__main__":
    main()
