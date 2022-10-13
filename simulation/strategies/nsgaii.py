# Importing EdgeSimPy components
from edge_sim_py.components.user import User
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.service import Service
from edge_sim_py.components.container_layer import ContainerLayer

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
    if random() > 0.5:
        placement = [sample(EdgeServer.all(), 1)[0].id for _ in range(Service.count())]
    else:
        services = sample(Service.all(), Service.count())
        for service in services:
            app = service.application
            user = app.users[0]

            # Shuffling the list of edge servers
            edge_servers = sample(EdgeServer.all(), EdgeServer.count())

            for edge_server in edge_servers:
                # Checking if the host would have resources to host the service and its (additional) layers
                if edge_server.has_capacity_to_host(service=service):
                    provision(user=user, application=app, service=service, edge_server=edge_server)
                    break

        placement = [service.server.id for service in Service.all()]

        reset_placement()

    return placement


def apply_placement(solution: list):
    """Applies the placement scheme suggested by the chromosome.

    Args:
        solution (list): Placement scheme.
    """
    for service_id, edge_server_id in enumerate(solution, 1):
        service = Service.find_by_id(service_id)
        edge_server = EdgeServer.find_by_id(edge_server_id)
        app = service.application
        user = app.users[0]

        provision(user=user, application=app, service=service, edge_server=edge_server)


def reset_placement():
    """Resets the placement scheme suggested by the chromosome."""
    for edge_server in EdgeServer.all():
        # Resetting the demand
        edge_server.cpu_demand = 0
        edge_server.memory_demand = 0
        edge_server.disk_demand = 0

        # Deprovisioning services
        for service in edge_server.services:
            service.server = None
        edge_server.services = []

        # Removing layers from edge servers not initially set as hosts for container registries
        if len(edge_server.container_registries) == 0:
            layers = list(edge_server.container_layers)
            edge_server.container_layers = []
            for layer in layers:
                layer.server = None
                ContainerLayer.remove(layer)

    for user in User.all():
        for app in user.applications:
            user.delays[str(app.id)] = 0
            user.communication_paths[str(app.id)] = []


def evaluate_placement() -> tuple:
    """Evaluates the placement scheme suggested by the chromosome."""
    delay_sla_violations = 0
    privacy_sla_violations = 0
    overall_edge_server_power_consumption = 0
    watts_per_core = []
    number_of_used_cpu_cores = 0
    overloaded_edge_servers = 0

    for user in User.all():
        for app in user.applications:
            user.set_communication_path(app=app)
            delay_sla = user.delay_slas[str(app.id)]
            delay = user._compute_delay(app=app, metric="latency")

            # Calculating objective #1: Number of Delay SLA Violations
            if delay > delay_sla:
                delay_sla_violations += 1

            # Calculating objective #2: Number of Privacy SLA Violations
            for service in app.services:
                if service.privacy_requirement > user.providers_trust[str(service.server.infrastructure_provider)]:
                    privacy_sla_violations += 1

    for edge_server in EdgeServer.all():
        # Calculating objective #3: Infrastructure's Power Consumption
        overall_edge_server_power_consumption += edge_server.get_power_consumption()
        watts_per_core.append(
            edge_server.cpu_demand * round(edge_server.power_model_parameters["max_power_consumption"] / edge_server.cpu)
        )
        number_of_used_cpu_cores += edge_server.cpu_demand

        # Calculating the edge server's free resources
        free_cpu = edge_server.cpu - edge_server.cpu_demand
        free_memory = edge_server.memory - edge_server.memory_demand
        free_disk = edge_server.disk - edge_server.disk_demand

        # Calculating penalty #1: Number of overloaded edge servers
        if free_cpu < 0 or free_memory < 0 or free_disk < 0:
            overloaded_edge_servers += 1

    # Aggregating the solution's fitness scores and penalties
    fitness_values = (
        delay_sla_violations,
        privacy_sla_violations,
        sum(watts_per_core) / number_of_used_cpu_cores,
    )
    penalties = overloaded_edge_servers

    output = (fitness_values, penalties)

    return output


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
    min_delay_violations = float("inf")
    min_privacy_violations = float("inf")
    min_power_consumption = float("inf")
    max_delay_violations = float("-inf")
    max_privacy_violations = float("-inf")
    max_power_consumption = float("-inf")
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
        min_delay_violations = min(min_delay_violations, solution["Delay Violations"])
        max_delay_violations = max(max_delay_violations, solution["Delay Violations"])

        min_privacy_violations = min(min_privacy_violations, solution["Priv. Violations"])
        max_privacy_violations = max(max_privacy_violations, solution["Priv. Violations"])

        min_power_consumption = min(min_power_consumption, solution["Power Consumption"])
        max_power_consumption = max(max_power_consumption, solution["Power Consumption"])

    # Applying the a placement scheme found by the NSGA-II algorithm
    best_solution = sorted(
        solutions,
        key=lambda s: min_max_norm(x=s["Delay Violations"], min=min_delay_violations, max=max_delay_violations)
        + min_max_norm(x=s["Priv. Violations"], min=min_privacy_violations, max=max_privacy_violations)
        + min_max_norm(x=s["Power Consumption"], min=min_power_consumption, max=max_power_consumption),
    )[0]["placement"]
    apply_placement(solution=best_solution)
