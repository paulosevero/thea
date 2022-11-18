# Importing EdgeSimPy components
from edge_sim_py import *

# Importing helper methods
from .helper_methods import *


def user_set_communication_path(self, app: object, communication_path: list = []) -> list:
    """Updates the set of links used during the communication of user and its application.

    Args:
        app (object): User application.
        communication_path (list, optional): User-specified communication path. Defaults to [].

    Returns:
        communication_path (list): Updated communication path.
    """
    topology = Topology.first()

    # Releasing links used in the past to connect the user with its application
    if app in self.communication_paths:
        path = [[NetworkSwitch.find_by_id(i) for i in p] for p in self.communication_paths[str(app.id)]]
        topology._release_communication_path(communication_path=path, app=app)

    # Defining communication path
    if len(communication_path) > 0:
        self.communication_paths[str(app.id)] = communication_path
    else:
        self.communication_paths[str(app.id)] = []

        service_hosts_base_stations = [service.server.base_station for service in app.services if service.server]
        communication_chain = [self.base_station] + service_hosts_base_stations

        # Defining a set of links to connect the items in the application's service chain
        for i in range(len(communication_chain) - 1):

            # Defining origin and target nodes
            origin = communication_chain[i]
            target = communication_chain[i + 1]

            # Finding and storing the best communication path between the origin and target nodes
            if origin == target:
                path = []
            else:
                path = find_shortest_path(origin_network_switch=origin.network_switch, target_network_switch=target.network_switch)

            # Adding the best path found to the communication path
            self.communication_paths[str(app.id)].append([network_switch.id for network_switch in path])

            # Computing the new demand of chosen links
            path = [[NetworkSwitch.find_by_id(i) for i in p] for p in self.communication_paths[str(app.id)]]
            topology._allocate_communication_path(communication_path=path, app=app)

    # Computing application's delay
    self._compute_delay(app=app, metric="latency")

    communication_path = self.communication_paths[str(app.id)]
    return communication_path


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
    overloaded_edge_servers = 0
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
        overall_power_consumption += edge_server.get_power_consumption()

        # Number of overloaded edge servers
        free_cpu = edge_server.cpu - edge_server.cpu_demand
        free_memory = edge_server.memory - edge_server.memory_demand
        free_disk = edge_server.disk - edge_server.disk_demand
        if free_cpu < 0 or free_memory < 0 or free_disk < 0:
            overloaded_edge_servers += 1

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

    data = {}
    data["provider"] = []
    for provider_id in set([server.infrastructure_provider for server in EdgeServer.all()]):
        data["provider"].append(
            {
                "provider": provider_id,
                "occupation": occupation_per_provider[provider_id],
                "active_servers": active_servers_per_infrastructure_provider[provider_id],
            }
        )

    data["model"] = []
    for model_name in set([server.model_name for server in EdgeServer.all()]):
        data["model"].append(
            {
                "model_name": model_name,
                "occupation": occupation_per_model[model_name],
                "power_consumption": sum(power_consumption_per_server_model[model_name]),
                "active_servers": active_servers_per_model[model_name],
            }
        )

    data["chain_size"] = []
    for chain_size in set([len(app.services) for app in Application.all()]):
        data["chain_size"].append(
            {
                "chain_size": chain_size,
                "delay_sla_violations": delay_sla_violations_per_application_chain_size.get(chain_size, None),
                "privacy_sla_violations": privacy_sla_violations_per_application_chain_size.get(chain_size, None),
            }
        )

    data["delay_sla"] = []
    for delay_sla in set([user.delay_slas[str(app.id)] for user in User.all() for app in user.applications]):
        data["delay_sla"].append(
            {
                "delay_sla": delay_sla,
                "delay_sla_violations": delay_violations_per_delay_sla.get(delay_sla, None),
                "privacy_sla_violations": privacy_violations_per_delay_sla.get(delay_sla, None),
            }
        )

    data["privacy_requirement"] = []
    for privacy_requirement in set([service.privacy_requirement for service in Service.all()]):
        data["privacy_requirement"].append(
            {
                "privacy_requirement": privacy_requirement,
                "privacy_sla_violations": privacy_violations_per_service_privacy_requirement.get(privacy_requirement, None),
            }
        )

    metrics = {
        "overloaded_edge_servers": overloaded_edge_servers,
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
        **data,
    }

    return metrics
