# Importing EdgeSimPy components
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.service import Service

# Importing helper methods
from simulation.helper_methods import *

# Importing Pymoo components
from pymoo.util.display import Display
from pymoo.core.problem import Problem
from pymoo.optimize import minimize
from pymoo.factory import get_crossover, get_mutation
from pymoo.algorithms.moo.nsga2 import NSGA2

# Importing Python libraries
import numpy as np
from random import sample, random

# Variable that defines the NSGA-II algorithm's verbosity
VERBOSE = True


def random_fit() -> list:
    """Custom algorithm that generates random placement solutions.

    Returns:
        placement (list): Generated placement solution.
    """
    services = sample(Service.all(), Service.count())
    for service in services:
        app = service.application
        user = app.users[0]
        user_switch = user.base_station.network_switch

        if random() > 0.5:
            edge_servers = sample(EdgeServer.all(), EdgeServer.count())
        else:
            edge_servers = sorted(
                EdgeServer.all(),
                key=lambda server: calculate_path_delay(
                    origin_network_switch=user_switch,
                    target_network_switch=server.network_switch,
                ),
            )

        for edge_server in edge_servers:
            # Checking if the host would have resources to host the service and its (additional) layers
            if edge_server.has_capacity_to_host(service=service):
                provision(user=user, application=app, service=service, edge_server=edge_server)
                break

    placement = [service.server.id for service in Service.all()]

    reset_placement()

    return placement


class TheaDisplay(Display):
    """Creates a visualization on how the genetic algorithm is evolving throughout the generations."""

    def _do(self, problem: object, evaluator: object, algorithm: object):
        """Defines the way information about the genetic algorithm is printed after each generation.

        Args:
            problem (object): Instance of the problem being solved.
            evaluator (object): Object that makes modifications before calling the problem's evaluate function.
            algorithm (object): Algorithm being executed.
        """
        super()._do(problem, evaluator, algorithm)

        objective_1 = int(np.min(algorithm.pop.get("F")[:, 0]))
        objective_2 = int(np.min(algorithm.pop.get("F")[:, 1]))
        objective_3 = int(np.min(algorithm.pop.get("F")[:, 2]))

        overloaded_servers = int(np.min(algorithm.pop.get("CV")[:, 0]))

        self.output.append("Del Viol.", objective_1)
        self.output.append("Pri Viol.", objective_2)
        self.output.append("Pw. Cons.", objective_3)
        self.output.append("Overloaded SVs", overloaded_servers)


class PlacementProblem(Problem):
    """Describes the application placement as an optimization problem."""

    def __init__(self, **kwargs):
        """Initializes the problem instance."""
        super().__init__(n_var=Service.count(), n_obj=3, n_constr=1, xl=1, xu=EdgeServer.count(), type_var=int, **kwargs)

    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluates solutions according to the problem objectives.

        Args:
            x (list): Solution or set of solutions that solve the problem.
            out (dict): Output of the evaluation function.
        """
        output = [self.get_fitness_score_and_constraints(solution=solution) for solution in x]

        out["F"] = np.array([item[0] for item in output])
        out["G"] = np.array([item[1] for item in output])

    def get_fitness_score_and_constraints(self, solution: list) -> tuple:
        """Calculates the fitness score and penalties of a solution based on the problem definition.

        Args:
            solution (list): Placement scheme.

        Returns:
            output (tuple): Output of the evaluation function containing the fitness scores of the solution and its penalties.
        """
        # Applying the placement scheme suggested by the chromosome
        apply_placement(solution=solution)

        # Calculating objectives and penalties
        output = evaluate_placement()

        # Resetting the placement scheme suggested by the chromosome
        reset_placement()

        return output


def nsgaii(parameters: dict = {}):
    # Parsing the NSGA-II parameters
    pop_size = parameters["pop_size"]
    n_gen = parameters["n_gen"]
    cross_prob = parameters["cross_prob"]
    mut_prob = parameters["mut_prob"]

    # Generating initial population for the NSGA-II algorithm
    initial_population = []
    while len(initial_population) < pop_size:
        placement = random_fit()
        if placement not in initial_population:
            initial_population.append(placement)

    # Defining the NSGA-II attributes
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=np.array(initial_population),
        crossover=get_crossover("int_ux", prob=cross_prob),
        mutation=get_mutation("int_pm", prob=mut_prob),
        eliminate_duplicates=True,
    )

    # Running the NSGA-II algorithm
    problem = PlacementProblem()
    res = minimize(problem, algorithm, termination=("n_gen", n_gen), seed=1, verbose=VERBOSE, display=TheaDisplay())

    # Parsing the NSGA-II's output
    solutions = []
    for i in range(len(res.X)):
        solution = {
            "placement": res.X[i].tolist(),
            "Delay Violations": res.F[i][0],
            "Priv. Violations": res.F[i][1],
            "Power Consumption": res.F[i][2],
            "overloaded_servers": res.CV[i][0].tolist(),
        }
        solutions.append(solution)

    # Applying the a placement scheme found by the NSGA-II algorithm
    best_solution = sorted(
        solutions, key=lambda solution: (solution["Delay Violations"], solution["Priv. Violations"], solution["Power Consumption"])
    )[0]["placement"]

    apply_placement(solution=best_solution)
