# Importing Python libraries
from subprocess import Popen, DEVNULL
import itertools
import time
import os

SYNC_EXECUTION = False
NUMBER_OF_PARALLEL_PROCESSES = os.cpu_count()
# NUMBER_OF_PARALLEL_PROCESSES = 10

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
    cmd = f"python3 -B -m simulation -d {dataset} -a {algorithm} -p {pop_size} -g {n_gen} -c {cross_prob} -m {mut_prob}"
    # print(f"    cmd = {cmd}")

    return Popen(cmd.split(" "), stdout=DEVNULL, stderr=DEVNULL)


# Parameters
datasets = ["datasets/dataset1.json"]
algorithms = ["nsgaii"]

population_sizes = [100, 200, 300]
number_of_generations = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1500, 2000, 2500, 3000]
crossover_probabilities = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
mutation_probabilities = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

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

processes = []

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
    proc = run_simulation(
        dataset=dataset,
        algorithm=algorithm,
        pop_size=pop_size,
        n_gen=n_gen,
        cross_prob=cross_prob,
        mut_prob=mut_prob,
    )

    processes.append(proc)

    while len(processes) > NUMBER_OF_PARALLEL_PROCESSES:
        proc = processes[0]
        proc.wait()
        processes.pop(0)
        print(f"PID {proc.pid} finished")

    print(f"{len(processes)} processes running in parallel")
