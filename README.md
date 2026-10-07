# Autonomous Fleet Dispatcher & Route Optimizer

### Algorithmic Solutions for the Google Hash Code 2018 Vehicle Routing Problem

An algorithmic framework for solving the **Vehicle Routing Problem with Time Windows (VRPTW)** based on the Google Hash Code 2018 challenge. The project benchmarks exact, greedy, decentralized, and metaheuristic optimization algorithms across diverse grid-city dispatch scenarios to maximize completed trip distances and on-time bonus rewards.

---

## Overview

Given a fleet of $F$ autonomous vehicles operating across a 2D grid over $T$ discrete timesteps, the engine assigns and sequences $N$ pre-booked rides. Each ride specifies:

* Pick-up and drop-off coordinates (Manhattan distance $d = \vert{}x_1 - x_2\vert{} + \vert{}y_1 - y_2\vert{}$)
* Earliest start timestep ($s$) and hard latest-finish deadline ($f$)

A ride yields points equal to its travel distance only if completed by $f$. If a vehicle arrives at or before $s$ and commences the ride precisely at $s$, an additional fixed bonus $B$ is awarded.

The solution space is $O(F^N)$, characterized by tight temporal bottlenecks, spatial dispersion, and competing bonus trade-offs.

---

## Key Architecture & Design

The repository uses a modular architecture following the **Strategy Pattern** for interchangeable optimization engines:

```
.
├── input/                  # Benchmark datasets (Hash Code sets A–E + custom bottlenecks)
├── logs/                   # Execution metrics, convergence rates, and run traces
├── output/                 # Hash Code-compliant submission files
├── src/
│   ├── parser.py           # Ingests grid specs, fleet dimensions, and trip constraints
│   ├── simulator.py        # Independent validation engine for schedule feasibility and scoring
│   ├── writer.py           # Validates and writes official submission formats
│   └── solvers/            # Pluggable solver implementations
│       ├── backtracking_solver.py        # Exact DFS search (small instances/benchmarking)
│       ├── greedy_solver.py              # Score/cost heuristic selection
│       ├── nearest_solver.py             # Distance-minimizing constructive heuristic
│       ├── simulated_annealing_solver.py # Probabilistic local search metaheuristic
│       ├── genetic_solver.py             # Evolutionary population optimization
│       └── multiagent_solver.py          # Decentralized bidding/agent allocation
└── main.py                 # CLI orchestration and evaluation harness

```

### Core Components

* **Independent Simulation Engine (`simulator.py`)**: Fully verifies submission schedules, tracking Manhattan traversal steps, idle waiting cycles, punctuality bonuses, and deadhead vehicle repositioning.
* **Pluggable Solvers (`src/solvers/`)**: Shared solver interface enabling zero-overhead benchmarking and cross-algorithm seeding (e.g., initializing Simulated Annealing using Nearest Neighbor solutions).
* **Automated Audit Logging (`logs/`)**: Records epoch-by-epoch convergence and score gains across iterative runs.

---

## Implemented Solvers

| Solver | Classification | Complexity | Strategy & Mechanics |
| --- | --- | --- | --- |
| **Backtracking** | Exact / Exhaustive | Exponential $O(F^N)$ | Pruned DFS searching for global optima; used as a baseline verification on small subproblems. |
| **Nearest Neighbor** | Constructive Heuristic | Low $O(N^2)$ | Greedily assigns the physically closest ride to idle vehicles to minimize repositioning deadhead. |
| **Greedy Evaluator** | Constructive Heuristic | Low $O(F \cdot N)$ | Evaluates candidate assignments based on immediate total payoff (ride distance + feasibility bonus). |
| **Simulated Annealing** | Metaheuristic | Configurable | Applies swap, insert, and 2-opt trajectory neighborhood perturbations with an exponential cooling schedule to escape local optima. |
| **Genetic Algorithm** | Metaheuristic | Configurable | Maintains a population of vehicle-ride schedules, utilizing tournament selection, order-preserving crossover (OX), and mutation operators. |
| **Multi-Agent** | Decentralized / Distributed | Moderate | Models vehicles as autonomous agents negotiating rides via localized auction/utility evaluation. |

---

## Benchmark Datasets

The algorithms are tested against official Google Hash Code sets and custom challenge inputs:

* `g_a_example.in`: Minimal reference case for algorithmic verification.
* `g_b_should_be_easy.in`: High vehicle-to-ride ratio; tests basic assignment density.
* `g_c_no_hurry.in`: Long time horizons with loose deadlines; prioritizes sequencing over punctuality.
* `g_d_metropolis.in`: Dense, congested metropolitan environment requiring strict deadhead minimization.
* `g_e_high_bonus.in`: High bonus value ($B \gg \text{distance}$); heavily shifts priority toward exact start timesteps.
* `bottleneck.txt` / `medium.txt`: Custom stress tests evaluating algorithmic scalability under constrained fleet capacity.

---

## Getting Started

### Prerequisites

* Python 3.10+
* Standard Python libraries (no external dependencies required)

### Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>

```

### Usage

Run the primary execution script from the root directory:

```bash
# Run a specific solver on a dataset
python main.py --input input/g_b_should_be_easy.in --solver greedy

# Run Simulated Annealing seeded with Nearest Neighbor
python main.py --input input/g_d_metropolis.in --solver simulated_annealing --seed nearest

# Run the Genetic Algorithm with custom epoch logs
python main.py --input input/medium.txt --solver genetic --generations 200 --pop-size 50

```

Submission-ready solutions are written to `output/`, and convergence metrics are logged to `logs/`.

---

## Engineering Takeaways

* **Hybrid Metaheuristic Initialization**: Initializing Simulated Annealing and Genetic Algorithms from constructive heuristic baselines (Nearest Neighbor/Greedy) significantly accelerated convergence compared to random restarts.
* **Trade-off Analysis**: Constructive heuristics compute in sub-second runtimes with strong baseline scores, while metaheuristics yield measurable percentage-point improvements in dense, deadline-sensitive scenarios (`g_d_metropolis` and `g_e_high_bonus`).
* **Decoupled Architecture**: Strict separation between the simulation rules (`simulator.py`) and scheduling heuristics (`solvers/`) eliminated validation bias across all benchmark runs.
