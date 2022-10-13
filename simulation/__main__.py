# Importing EdgeSimPy components
from edge_sim_py import *

# Importing helper methods
from .helper_methods import *

# Importing placement strategies
from .strategies import *

# Importing Python libraries
from random import seed
import argparse


def topology_collect(self) -> dict:
    """Method that collects a set of metrics for the object.

    The network topology aggregates the following metrics from the simulation:
        1. Infrastructure Usage
            - Overall Occupation
            - Occupation per Infrastructure Provider
            - Occupation per Server Model
            - Active Servers per Infrastructure Provider
            - Active Servers per Model
            - Power Consumption
                - Overall Power Consumption
                - Power Consumption per Server Model
        2. SLA Violations
            - Number of Delay SLA Violations
            - Number of Privacy SLA Violations
            - Number of Delay SLA Violations per Application Chain Size
            - Privacy Violations per Application Delay SLA
            - Privacy Violations per Service Privacy Requirement

    Returns:
        metrics (dict): Object metrics.
    """
    # Declaring infrastructure metrics
    overall_occupation = 0
    occupation_per_provider = {}
    occupation_per_model = {}
    overall_power_consumption = 0
    power_consumption_per_server_model = {}
    active_servers_per_infrastructure_provider = {}
    active_servers_per_model = {}

    # Declaring delay SLA metrics
    delay_sla_violations = 0
    delay_sla_violations_per_application_chain_size = {}
    delay_violations_per_delay_sla = {}

    # Declaring privacy SLA metrics
    privacy_sla_violations = 0
    privacy_violations_per_delay_sla = {}
    privacy_violations_per_service_privacy_requirement = {}
    privacy_sla_violations_per_application_chain_size = {}

    # Collecting infrastructure metrics
    for edge_server in EdgeServer.all():
        # Overall Occupation
        capacity = normalize_cpu_and_memory(cpu=edge_server.cpu, memory=edge_server.memory)
        demand = normalize_cpu_and_memory(cpu=edge_server.cpu_demand, memory=edge_server.memory_demand)
        overall_occupation += demand / capacity * 100

        # Occupation per Infrastructure Provider
        if edge_server.infrastructure_provider not in occupation_per_provider.keys():
            occupation_per_provider[edge_server.infrastructure_provider] = []
        occupation_per_provider[edge_server.infrastructure_provider].append(demand / capacity * 100)

        # Occupation per Server Model
        if edge_server.model_name not in occupation_per_model.keys():
            occupation_per_model[edge_server.model_name] = []
        occupation_per_model[edge_server.model_name].append(demand / capacity * 100)

        # Power consumption per Server Model
        if edge_server.model_name not in power_consumption_per_server_model.keys():
            power_consumption_per_server_model[edge_server.model_name] = []
        power_consumption_per_server_model[edge_server.model_name].append(edge_server.get_power_consumption())

    # Aggregating overall metrics
    overall_occupation = overall_occupation / EdgeServer.count()
    overall_power_consumption = sum(sum(model_consumption) for model_consumption in power_consumption_per_server_model.values())

    for provider_id in occupation_per_provider.keys():
        active_servers_per_infrastructure_provider[provider_id] = len(
            [item for item in occupation_per_provider[provider_id] if item > 0]
        )
        occupation_per_provider[provider_id] = sum(occupation_per_provider[provider_id]) / len(occupation_per_provider[provider_id])

    for model_name in occupation_per_model.keys():
        active_servers_per_model[model_name] = len([item for item in occupation_per_model[model_name] if item > 0])
        occupation_per_model[model_name] = sum(occupation_per_model[model_name]) / len(occupation_per_model[model_name])

    # Collecting delay SLA metrics
    for user in User.all():
        for app in user.applications:
            user.set_communication_path(app=app)
            delay_sla = user.delay_slas[str(app.id)]
            delay = user._compute_delay(app=app, metric="latency")

            # Calculating the number of delay SLA violations
            if delay > delay_sla:
                delay_sla_violations += 1

                if len(app.services) not in delay_sla_violations_per_application_chain_size.keys():
                    delay_sla_violations_per_application_chain_size[len(app.services)] = 0
                delay_sla_violations_per_application_chain_size[len(app.services)] += 1

                if delay_sla not in delay_violations_per_delay_sla.keys():
                    delay_violations_per_delay_sla[delay_sla] = 0
                delay_violations_per_delay_sla[delay_sla] += 1

            # Calculating the number of privacy SLA violations
            for service in app.services:
                if service.server and service.privacy_requirement > user.providers_trust[str(service.server.infrastructure_provider)]:
                    privacy_sla_violations += 1

                    if service.privacy_requirement not in privacy_violations_per_service_privacy_requirement.keys():
                        privacy_violations_per_service_privacy_requirement[service.privacy_requirement] = 0
                    privacy_violations_per_service_privacy_requirement[service.privacy_requirement] += 1

                    if len(app.services) not in privacy_sla_violations_per_application_chain_size.keys():
                        privacy_sla_violations_per_application_chain_size[len(app.services)] = 0
                    privacy_sla_violations_per_application_chain_size[len(app.services)] += 1

                    if delay_sla not in privacy_violations_per_delay_sla.keys():
                        privacy_violations_per_delay_sla[delay_sla] = 0
                    privacy_violations_per_delay_sla[delay_sla] += 1

    metrics = {
        "overall_occupation": overall_occupation,
        "occupation_per_provider": occupation_per_provider,
        "occupation_per_model": occupation_per_model,
        "overall_power_consumption": overall_power_consumption,
        "power_consumption_per_server_model": power_consumption_per_server_model,
        "active_servers_per_infrastructure_provider": active_servers_per_infrastructure_provider,
        "active_servers_per_model": active_servers_per_model,
        "delay_sla_violations": delay_sla_violations,
        "privacy_sla_violations": privacy_sla_violations,
        "delay_sla_violations_per_application_chain_size": delay_sla_violations_per_application_chain_size,
        "delay_violations_per_delay_sla": delay_violations_per_delay_sla,
        "privacy_violations_per_delay_sla": privacy_violations_per_delay_sla,
        "privacy_violations_per_service_privacy_requirement": privacy_violations_per_service_privacy_requirement,
        "privacy_sla_violations_per_application_chain_size": privacy_sla_violations_per_application_chain_size,
    }
    return metrics


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

    # Loading a sample dataset from GitHub
    simulator.initialize(input_file=dataset)

    # Executing the simulation
    User.set_communication_path = optimized_set_communication_path
    Topology.collect = topology_collect
    simulator.run_model()


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
