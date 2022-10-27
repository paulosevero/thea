# Importing EdgeSimPy components
from edge_sim_py import *

# Importing customized EdgeSimPy components
from .custom_component_methods import *

# Importing placement strategies
from .strategies import *

# Importing Python libraries
from random import seed
import argparse


def main(seed_value: int, algorithm: str, dataset: str, parameters: dict = {}):
    # Setting a seed value to enable reproducibility
    seed(seed_value)

    # Parsing NSGA-II parameters string
    parameters_string = ""
    if algorithm == "nsgaii":
        for key, value in parameters.items():
            parameters_string += f"{key}={value};"

    # Creating a Simulator object
    simulator = Simulator(
        tick_duration=1,
        tick_unit="seconds",
        stopping_criterion=lambda model: model.schedule.steps == 1,
        resource_management_algorithm=eval(algorithm),
        resource_management_algorithm_parameters=parameters,
        dump_interval=1,
        logs_directory=f"logs/algorithm={algorithm};{parameters_string}",
    )

    # Loading custom EdgeSimPy components and methods
    User.set_communication_path = user_set_communication_path
    Topology.collect = topology_collect

    # Loading a sample dataset from GitHub
    simulator.initialize(input_file=dataset)

    # Executing the simulation
    simulator.run_model()

    metrics = Topology.first().collect()
    print(f"==== {algorithm} ====")
    for metric, value in metrics.items():
        print(f"{metric}: {value}")


if __name__ == "__main__":
    # Parsing named arguments from the command line
    parser = argparse.ArgumentParser()

    # Generic arguments
    parser.add_argument("--seed", "-s", help="Seed value for EdgeSimPy", default="1")
    parser.add_argument("--dataset", "-d", help="Dataset file")
    parser.add_argument("--algorithm", "-a", help="Algorithm that will be executed")

    # NSGA-II arguments
    parser.add_argument("--pop_size", "-p", help="Population size", default="0")
    parser.add_argument("--n_gen", "-g", help="Number of generations", default="0")
    parser.add_argument("--cross_prob", "-c", help="Crossover probability (0.0 to 1.0)", default="1")
    parser.add_argument("--mut_prob", "-m", help="Mutation probability (0.0 to 1.0)", default="0")

    args = parser.parse_args()

    parameters = {
        "pop_size": int(args.pop_size),
        "n_gen": int(args.n_gen),
        "cross_prob": float(args.cross_prob),
        "mut_prob": float(args.mut_prob),
    }

    main(seed_value=int(args.seed), algorithm=args.algorithm, dataset=args.dataset, parameters=parameters)
