# Importing Python libraries
import itertools
import time
import os

SYNC_EXECUTION = True


def run_simulation(dataset: str, algorithm: str, n_gen: int, pop_size: int, cross_prob: float, mut_prob: float):
    """Executes the simulation with the specified parameters.

    Args:
        dataset (str): Dataset being read.
        algorithm (str): Algorithm being executed.
        n_gen (int): Number of generations of the NSGA-II algorithm.
        pop_size (int): Number of chromosomes in the NSGA-II's population.
        cross_prob (float): NSGA-II's crossover probability.
        mut_prob (float): NSGA-II's mutation probability.
    """
    # Running the simulation based on the parameters and gathering its execution time
    cmd = f"nohup python3 -B -m simulation -d {dataset} -a {algorithm} -p {pop_size} -g {n_gen} -c {cross_prob} -m {mut_prob} &"
    print(f"    cmd = {cmd}")

    stream = os.popen(cmd)
    if SYNC_EXECUTION:
        stream.read()


# Parameters
datasets = ["datasets/dataset1.json"]
algorithms = ["nsgaii"]

population_sizes = [300]
number_of_generations = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
crossover_probabilities = [1]
mutation_probabilities = [0, 0.2, 0.4, 0.6, 0.8, 1]

# Generating list of combinations with the parameters specified
combinations = list(
    itertools.product(
        datasets,
        algorithms,
        population_sizes,
        number_of_generations,
        crossover_probabilities,
        mutation_probabilities,
    )
)

# Executing simulations and collecting results
print(f"EXECUTING {len(combinations)} COMBINATIONS")
for i, parameters in enumerate(combinations, 1):
    # Parsing parameters
    dataset = parameters[0]
    algorithm = parameters[1]
    pop_size = parameters[2]
    n_gen = parameters[3]
    cross_prob = parameters[4]
    mut_prob = parameters[5]

    print(f"\t[Execution {i}]")
    print(f"\t\t[{algorithm}] dataset={dataset}. pop_size={pop_size}. n_gen={n_gen}. cross_prob={cross_prob}. mut_prob={mut_prob}")

    # Executing algorithm
    run_simulation(
        dataset=dataset,
        algorithm=algorithm,
        pop_size=pop_size,
        n_gen=n_gen,
        cross_prob=cross_prob,
        mut_prob=mut_prob,
    )
