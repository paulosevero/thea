# Importing EdgeSimPy components
from edge_sim_py import *

# Importing helper methods
from .helper_methods import *

# Importing placement strategies
from .strategies import *

# Importing Python libraries
from random import seed
import argparse


def main(algorithm):
    seed(1)

    # Creating a Simulator object
    simulator = Simulator(
        tick_duration=1,
        tick_unit="seconds",
        stopping_criterion=lambda model: model.schedule.steps == 1,
        resource_management_algorithm=eval(algorithm),
        dump_interval=float("inf"),
    )

    # Loading a sample dataset from GitHub
    simulator.initialize(input_file="datasets/dataset1.json")

    # Executing the simulation
    User.set_communication_path = optimized_set_communication_path
    simulator.run_model()

    print("==== METRICS ====")
    print(f"ALGORITHM: {simulator.resource_management_algorithm.__name__}")
    delay_sla_violations = []
    privacy_sla_violations = []
    overall_edge_server_power_consumption = 0
    for user in User.all():
        for app in user.applications:
            delay_sla = user.delay_slas[str(app.id)]
            delay = user.delays[str(app.id)]

            # Calculating objective #1: Number of Delay SLA Violations
            if delay > delay_sla:
                if app not in delay_sla_violations:
                    delay_sla_violations.append(app)

            # Calculating objective #2: Number of Privacy SLA Violations
            for service in app.services:
                if service.privacy_requirement > user.providers_trust[str(service.server.infrastructure_provider)]:
                    privacy_sla_violations.append(service)

    for edge_server in EdgeServer.all():
        # Calculating objective #3: Infrastructure's Power Consumption
        overall_edge_server_power_consumption += edge_server.get_power_consumption()

    print(f"Delay SLA Violations: {len(delay_sla_violations)}")
    print(f"Privacy SLA Violations: {len(privacy_sla_violations)}")
    print(f"Power Consumption: {overall_edge_server_power_consumption}")

    providers_demand = {}
    for edge_server in EdgeServer.all():
        if edge_server.infrastructure_provider not in providers_demand.keys():
            providers_demand[edge_server.infrastructure_provider] = 0
        providers_demand[edge_server.infrastructure_provider] += edge_server.cpu_demand
    print(f"Providers Occupation: {providers_demand}")


if __name__ == "__main__":
    # Parsing named arguments from the command line
    parser = argparse.ArgumentParser()

    # Generic arguments
    parser.add_argument("--algorithm", "-a", help="Algorithm that will be executed")

    args = parser.parse_args()

    main(algorithm=args.algorithm)
