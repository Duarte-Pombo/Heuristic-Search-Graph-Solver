from src.simulator import simulate_assignment, manhattan_distance
from src.solvers.greedy_solver import greedy_solver
 
import random
import copy

def genetic_solver ( problem ) :
    num_rides = problem.num_rides
    fleet_size = problem.fleet_size

    population_size, max_generations, mutation_rate, elite_fraction, tournament_size = get_parameters (num_rides, fleet_size)

    num_elite_seed = max (1, int(population_size * elite_fraction))

    print(f"\n=== Starting Genetic Algorithm ===")
    print(f"  Rides / Vehicles  : {num_rides} / {fleet_size}")
    print(f"  Elite carry-over  : {num_elite_seed} individuals")
    
    # GENERATION 0 -----------------------------------------------

    # start population build
    population = []
    
    # get initial seed from greedy algorithm
    try: 
        greedy_perm, greedy_cuts = get_greedy_start_seed (problem)
        population.append((greedy_perm, greedy_cuts))
        print (" - greedy seed implanted")
    except Exception as exc: 
        print (f"  [warn] Greedy seed failed ({exc}), using random instead.")

    # fill the rest with random permutaions
    while (len(population) < population_size):
        population.append(get_random_chromosome(num_rides, fleet_size))

    # EVALUATE INITIAL GENERATION ---------------------------------

    print ("evaluating Gen 0")

    fitness_scores = [get_fitness(perm, cuts, fleet_size, problem) for perm, cuts in population]

    best_idx = max (range(population_size), key=lambda i: fitness_scores[i])
    best_score = fitness_scores[best_idx]
    best_chromossome = copy.deepcopy(population[best_idx])
    
    print(f"  Initial best score : {best_score}")
    print(f"  Initial avg  score : {sum(fitness_scores) / len(fitness_scores):.0f}")

    # EVOLUTION PROCESS -------------------------------------------

    print(f"\n  {'Gen':>5}  {'Best':>10}  {'Avg':>10}  {'Δ best':>8}")
    print(f"  {'-'*5}  {'-'*10}  {'-'*10}  {'-'*8}")
    
    for generation in range (max_generations):
        #sort idx by fitness score (best to worst)
        ranked_scores = sorted(range(population_size), key=lambda i: fitness_scores[i], reverse=True)

        new_population = []
        new_fits = []

        # ELITISM 

        # carry over top num_elite_seed unchanged 
        for idx in ranked_scores[:num_elite_seed]:
            new_population.append(copy.deepcopy(population[idx]))
            new_fits.append(fitness_scores[idx])

        # CROSSOVER + MUTATION

        # fill the rest of the population with crossovers of the chromossomes and mutations
        while len(new_population) < population_size:
            pa = tournament_select(population, fitness_scores, tournament_size)
            pb = tournament_select(population, fitness_scores, tournament_size)
 
            perm_a, cuts_a = pa
            perm_b, cuts_b = pb
 
            child_perms = ox1_crossover(perm_a, perm_b)
            child_cuts  = cuts_crossover(cuts_a, cuts_b)
 
            for cperm, ccuts in zip(child_perms, child_cuts):
                if len(new_population) >= population_size:
                    break
                cperm, ccuts = mutate(cperm, ccuts, num_rides, mutation_rate)
                f = get_fitness(cperm, ccuts, fleet_size, problem)
                new_population.append((cperm, ccuts))
                new_fits.append(f)

        population = new_population
        fitness_scores = new_fits


        # TRACK GLOBAL BEST ACROSS GENS

        gen_best_idx = max(range(population_size), key=lambda i: fitness_scores[i])
        gen_best     = fitness_scores[gen_best_idx]
        if gen_best > best_score:
            delta      = gen_best - best_score
            best_score = gen_best
            best_chromossome = copy.deepcopy(population[gen_best_idx])
        else:
            delta = 0
 
        # progress every 10 generations
        if (generation + 1) % 10 == 0 or generation == 0 or generation == max_generations - 1:
            avg = sum(fitness_scores) / len(fitness_scores)
            d_str = f"+{delta}" if delta else "-"
            print(f"  {generation + 1:>5}  {best_score:>10}  {avg:>10.0f}  {d_str:>8}")
    
    
    # Decode best chromossome
    
    best_perm, best_cuts = best_chromossome
    final_assignment = chromosome_to_assignment(best_perm, best_cuts, fleet_size)
 
    # ensure every vehicle key exists (simulate_assignment expects it)
    for v in range(fleet_size):
        final_assignment.setdefault(v, [])
 
    print(f"\n  GA finished. Best score: {best_score}")
    return final_assignment


# ----------------------------------
# GENETIC FUNCTIONS
# ----------------------------------

# CHROMOSSOME CROSSOVER

def ox1_crossover(perm_a, perm_b):

    n = len(perm_a)
    if n < 2:
        return list(perm_a), list(perm_b)
 
    i, j = sorted(random.sample(range(n), 2))
 
    def build(base, donor):
        segment  = base[i:j + 1]
        seg_set  = set(segment)
        # Walk donor starting just after j (wrap-around), skip genes in segment
        donor_order = [x for x in (donor[j + 1:] + donor[:j + 1]) if x not in seg_set]
        child = [None] * n
        child[i:j + 1] = segment
        ptr = 0
        for pos in list(range(j + 1, n)) + list(range(i)):
            child[pos] = donor_order[ptr]
            ptr += 1
        return child
 
    return build(perm_a, perm_b), build(perm_b, perm_a)

def cuts_crossover(cuts_a, cuts_b):
    c1 = [a if random.random() < 0.5 else b for a, b in zip(cuts_a, cuts_b)]
    c2 = [b if random.random() < 0.5 else a for a, b in zip(cuts_a, cuts_b)]
    return c1, c2

# CHROMOSSOME MUTATION

def mutate(rides_permutation, cuts, num_rides, mutation_rate=0.05):
    perm = list(rides_permutation)
    cuts = list(cuts)
 
    if random.random() >= mutation_rate:
        return perm, cuts          # no mutation this time
 
    op = random.choice(['swap', 'inversion', 'cut_shift'])
 
    if op == 'swap' and len(perm) >= 2:
        i, j = random.sample(range(len(perm)), 2)
        perm[i], perm[j] = perm[j], perm[i]
 
    elif op == 'inversion' and len(perm) >= 2:
        i, j = sorted(random.sample(range(len(perm)), 2))
        perm[i:j + 1] = perm[i:j + 1][::-1]
 
    elif op == 'cut_shift' and cuts:
        idx   = random.randrange(len(cuts))
        delta = random.choice([-1, 1])
        lo    = cuts[idx - 1] if idx > 0         else 0
        hi    = cuts[idx + 1] if idx < len(cuts) - 1 else num_rides
        cuts[idx] = max(lo, min(hi, cuts[idx] + delta))
 
    return perm, cuts

# -------------------------------------
# AUX FUNTIONS
# -------------------------------------

def assignment_to_chromosome (assignment, num_rides, fleet_size):
    rides_permutation = []
    cuts = []

    for vehicle in range(fleet_size):
        rides_permutation.extend(assignment.get(vehicle, []))
        cuts.append(len(rides_permutation))

    cuts = cuts[:-1] # drop the last cut

    # append rides left to assign
    assigned_set = set(rides_permutation)
    for ride in range(num_rides):
        if ride not in assigned_set:
            rides_permutation.append(ride)
 
    return rides_permutation, cuts


def chromosome_to_assignment(rides_permutation, cuts, fleet_size):
    assignment = {}
    prev = 0
    for vehicle, cut in enumerate(cuts):
        assignment[vehicle] = list(rides_permutation[prev:cut])
        prev = cut
    assignment[fleet_size - 1] = list(rides_permutation[prev:])   # last vehicle gets the rest of the rides
    return assignment


def get_random_chromosome(num_rides, fleet_size):
    permutation = list(range(num_rides))
    random.shuffle(permutation)
    cuts = sorted(random.randint(0, num_rides) for _ in range(fleet_size - 1))
    return permutation, cuts

def get_fitness(rides_permutation, cuts, fleet_size, problem):
    assignment = chromosome_to_assignment(rides_permutation, cuts, fleet_size)
    score, _ = simulate_assignment(problem, assignment)
    return score

def tournament_select(population, fitnesses, k=3):
    contestants = random.sample(range(len(population)), k)
    winner = max(contestants, key=lambda i: fitnesses[i])
    return copy.deepcopy(population[winner])

def get_greedy_start_seed (problem):
    assignment = greedy_solver(problem)
    return assignment_to_chromosome(assignment, problem.num_rides, problem.fleet_size)

# ---------------------------------------
# CL INTERFACE FUNCTIONS
# ---------------------------------------

def get_parameters (num_rides, fleet_size):
    
    # default values 
    default_population_size   = max(30, min(200, num_rides // 15))
    default_max_generations  = max(60, min(600, num_rides * 3))
    default_mutation_rate   = 0.05
    default_elite_fraction = 0.10
    default_tournament_size   = 3
 
    print("\n" + "=" * 60)
    print(" Genetic Algorithm — Parameter Configuration")
    print(f" > {num_rides} rides, {fleet_size} vehicles\n")
    print("  Enter for default value or type in the value \n")
 
    print("  ┌─ POPULATION SIZE ─────────────────────────────────────┐")
    print("  │ Number of candidate solutions kept each generation.   │")
    print("  │                                                       │")
    print("  │   • 20–50   → fast, good for quick experiments        │")
    print("  │   • 50–150  → balanced (recommended range)            │")
    print("  │   • 150–500 → thorough search, noticeably slower      │")
    print("  │   • 500+    → very slow; use only on small datasets   │")
    print("  └───────────────────────────────────────────────────────┘")

    population_size = prompt_user_for_int(
            "Population size",
            default_population_size, 
            minimum = 10, maximum = 2000, 
            warn_above = 300, 
            warn_msg="Warning: above 300 population size will be slow on large datasets")
    
    print()
 
    print("  ┌─ GENERATIONS ─────────────────────────────────────────┐")
    print("  │ How many evolution cycles to run.                     │")
    print("  │                                                       │")
    print("  │ Total evaluations ≈ pop_size × generations.           │")
    print("  │   • 50–200   → quick run                              │")
    print("  │   • 200–500  → balanced (recommended range)           │")
    print("  │   • 500–2000 → long search; expect minutes            │")
    print("  └───────────────────────────────────────────────────────┘")
    max_generations = prompt_user_for_int(
        "Max generations",
        default_max_generations, 
        minimum = 10, maximum = 10000,
        warn_above = 1000,
        warn_msg="Warning: above 1000 generations w/ a large population will be slow")
    
    print()

    print("  ┌─ MUTATION RATE ───────────────────────────────────────┐")
    print("  │ Probability that each offspring is mutated.           │")
    print("  │ Too low  → algorithm gets stuck, no solution diversity│")
    print("  │ Too high → random walk; good solutions get destroyed. │")
    print("  │   • 0.01–0.03  → conservative, slow exploration       │")
    print("  │   • 0.03–0.10  → recommended range                    │")
    print("  │   • 0.10–0.30  → aggressive; useful if stuck          │")
    print("  └───────────────────────────────────────────────────────┘")
    
    mutation_rate = prompt_user_for_float(
        "Mutation rate (0.0–1.0)", 
        default_mutation_rate, 
        minimum=0.0, maximum=1.0 )

    print()
 
    print("  ┌─ ELITE FRACTION ──────────────────────────────────────┐")
    print("  │ Fraction of top individuals copied unchanged into the │")
    print("  │ next generation (elitism).                            │")
    print("  │   • 0.05–0.15  → standard elitism (recommended)       │")
    print("  │   • 0.20–0.40  → heavy elitism; fast convergence but  │")
    print("  │                  risks premature loss of diversity    │")
    print("  └───────────────────────────────────────────────────────┘")
    
    elite_fraction = prompt_user_for_float(
        "Elite fraction (0.0–0.5)", 
        default_elite_fraction, 
        minimum=0.0, maximum=0.5
    )

    print()
 
    print("  ┌─ TOURNAMENT SIZE ─────────────────────────────────────┐")
    print("  │ Number of individuals that compete to become a parent │")
    print("  │ Higher → stronger selection pressure, but diversity   |")
    print("  | drops faster.                                         │")
    print("  │   • 2   → weak pressure, high diversity               │")
    print("  │   • 3–5 → recommended range                           │")
    print("  │   • 7+  → near-greedy selection; low diversity        │")
    print("  └───────────────────────────────────────────────────────┘")
    
    tournament_size = prompt_user_for_int(
        "Tournament size", 
        default_tournament_size, 
        minimum=2, maximum = min(20, population_size),
        warn_above=7,
        warn_msg="Warning: large tournament sizes reduce population diversity quickly"
    )

    print()
 
    label, desc = estimate_runtime (population_size, max_generations, num_rides)
    icons = {"fast": "🟢", "moderate": "🟡", "slow": "🟠", "very slow": "🔴"}
    icon  = icons.get(label, "⚠")
    print(f"  {icon}  Estimated runtime: {label.upper()} — {desc}.")
    print(f"     (pop={population_size} × gens={max_generations} × rides={num_rides} "
          f"= {population_size * max_generations * num_rides:,} work units)\n")
 
    print("  ─── Confirmed parameters ───────────────────────────────")
    print(f"    Population size   : {population_size}")
    print(f"    Generations       : {max_generations}")
    print(f"    Mutation rate     : {mutation_rate:.0%}")
    print(f"    Elite fraction    : {elite_fraction:.0%}  ({max(1, int(population_size * elite_fraction))} individuals)")
    print(f"    Tournament size   : {tournament_size}")
    print("  ────────────────────────────────────────────────────────")
 
    confirm = input("\n  Proceed with these settings? [Y/n]: ").strip().lower()
    if confirm in ("n", "no"):
        print("  Re-running parameter configuration…")
        return get_parameters(num_rides, fleet_size)
 
    return population_size, max_generations, mutation_rate, elite_fraction, tournament_size
 

def prompt_user_for_int(prompt, default, minimum, maximum, warn_above=None, warn_msg=""):
    while True:
        raw = input(f"  {prompt} [{minimum}–{maximum}, default={default}]: ").strip()
        if raw == "":
            return default
        try:
            val = int(raw)
        except ValueError:
            print(f"  please enter a whole number")
            continue
        if not (minimum <= val <= maximum):
            print(f"  value must be between {minimum} and {maximum}")
            continue
        if warn_above is not None and val > warn_above and warn_msg:
            print(f"  ⚠  {warn_msg}")
        return val
 
 
def prompt_user_for_float (prompt, default, minimum, maximum, decimals=2):
    while True:
        raw = input(f"  {prompt} [{minimum}–{maximum}, default={default}]: ").strip()
        if raw == "":
            return default
        try:
            val = float(raw)
        except ValueError:
            print(f"  please enter a decimal number")
            continue
        if not (minimum <= val <= maximum):
            print(f"  value must be between {minimum} and {maximum}")
            continue
        return round(val, decimals)

RUNTIME_THRESHOLDS = {
    # (pop_size * generations * num_rides) rough "work units"
    5_000_000:   ("fast",    "should finish in seconds"),
    50_000_000:  ("moderate","expect tens of seconds to a few minutes"),
    500_000_000: ("slow",    "may take several minutes"),
}
 
def estimate_runtime(population_size, generations, num_rides):
    work = population_size * generations * num_rides
    for threshold, (label, desc) in RUNTIME_THRESHOLDS.items():
        if work <= threshold:
            return label, desc
    return "very slow", "consider reducing parameters"
