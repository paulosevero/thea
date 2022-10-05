# Importing EdgeSimPy components
from edge_sim_py.components.user import User
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.service import Service
from edge_sim_py.components.container_layer import ContainerLayer

# Importing helper methods
from .helper_methods import *

# Importing Pymoo components
from pymoo.util.display import Display
from pymoo.core.problem import Problem
from pymoo.optimize import minimize
from pymoo.factory import get_sampling, get_crossover, get_mutation
from pymoo.algorithms.moo.nsga2 import NSGA2

# Importing Python libraries
import numpy as np

SAMPLE_TEST = True


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
        if SAMPLE_TEST:
            if edge_server.cpu_demand > 0:
                if edge_server.cpu == 8:
                    overall_edge_server_power_consumption += 250
                elif edge_server.cpu == 12:
                    overall_edge_server_power_consumption += 550
        else:
            overall_edge_server_power_consumption += edge_server.get_power_consumption()

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
        overall_edge_server_power_consumption,
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

        self.output.append("Delay Viol.", objective_1)
        self.output.append("Priv. Viol.", objective_2)
        self.output.append("Power Cons.", objective_3)


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
    # Defining the NSGA-II attributes
    algorithm = NSGA2(
        pop_size=100,
        sampling=get_sampling("int_random"),
        crossover=get_crossover("int_ux", prob=1),
        mutation=get_mutation("int_pm", prob=0.2),
        eliminate_duplicates=True,
    )

    # Running the NSGA-II algorithm
    problem = PlacementProblem()
    res = minimize(problem, algorithm, termination=("n_gen", 100), seed=1, verbose=True, display=TheaDisplay())

    # Parsing the NSGA-II's output
    solutions = []
    for i in range(len(res.X)):
        placement = res.X[i].tolist()
        fitness = {
            "Delay Violations": res.F[i][0],
            "Privacy Violations": res.F[i][1],
            "Power Consumption": res.F[i][2],
        }
        overloaded_servers = res.CV[i][0].tolist()

        solutions.append({"placement": placement, "fitness": fitness, "overloaded_servers": overloaded_servers})

    # Applying the a placement scheme found by the NSGA-II algorithm
    # best_solution = [7, 8, 1, 1, 7, 4, 4, 1, 5, 5]  # This is the solution manually calculated in the whiteboard
    best_solution = sorted(
        solutions,
        key=lambda s: (s["fitness"]["Delay Violations"] * s["fitness"]["Privacy Violations"] * s["fitness"]["Power Consumption"])
        ** (1 / 3),
    )[0]["placement"]

    print(f"best_solution => {best_solution}")

    apply_placement(solution=best_solution)
    result = evaluate_placement()

    if SAMPLE_TEST:
        print("==== SOLUTIONS ====")
        for solution in solutions:
            print(f"    {solution}")
        print("")

        print(f"\nBEST SOLUTION: {best_solution}")

        print(f"OUTPUT: {result}")
        print(f"    Delay SLA Violations: {result[0][0]}")
        print(f"    Privacy SLA Violations: {result[0][1]}")
        print(f"    Power Consumption: {result[0][2]}")
        print(f"    Overloaded Edge Servers: {result[1]}")
