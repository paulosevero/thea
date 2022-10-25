# Importing EdgeSimPy components
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.application import Application
from edge_sim_py.components.service import Service

# Importing helper methods
from simulation.helper_methods import *


def get_application_delay_score(app: object):
    """Calculates the application delay score considering the number application's SLA and the number of edge servers close enough
    to the application's user that could be used to host the application's services without violating the delay SLA.

    Args:
        app (object): Application whose delay score will be calculated.

    Returns:
        delay_score (float): Application's delay score.
    """
    # Gathering information about the application
    delay_sla = app.users[0].delay_slas[str(app.id)]
    user_switch = app.users[0].base_station.network_switch

    # Gathering the list of hosts close enough to the user that could be used to host the services without violating the delay SLA
    edge_servers_that_dont_violate_delay_sla = [
        1
        for edge_server in EdgeServer.all()
        if calculate_path_delay(origin_network_switch=user_switch, target_network_switch=edge_server.network_switch) <= delay_sla
    ]

    if sum(edge_servers_that_dont_violate_delay_sla) == 0:
        delay_score = 0
    else:
        delay_score = 1 / ((len(edge_servers_that_dont_violate_delay_sla) * delay_sla) ** (1 / 2))

    return delay_score


def get_service_privacy_complexity_score(user: object, service: object):
    """Calculates the service complexity score, which considers the service capacity and the amount of available resources
    from edge servers within the infrastructure with enough trust to don't violate the service's privacy requirement.

    Args:
        user (object): User that accesses the service.
        service (object): Service that must obtain the service complexity score.

    Returns:
        service_complexity_score (float): Service's complexity score.
    """
    normalized_capacity_with_enough_privacy = sum(
        normalize_cpu_and_memory(cpu=edge_server.cpu - edge_server.cpu_demand, memory=edge_server.memory - edge_server.memory_demand)
        for edge_server in EdgeServer.all()
        if user.providers_trust[str(edge_server.infrastructure_provider)] >= service.privacy_requirement
    )

    normalized_service_demand = normalize_cpu_and_memory(cpu=service.cpu_demand, memory=service.memory_demand)
    service_complexity_score = normalized_service_demand / max(normalized_service_demand, normalized_capacity_with_enough_privacy)

    return service_complexity_score


def get_norm(metadata: dict, attr_name: str, min: dict, max: dict) -> float:
    """Wrapper to normalize a value using the Min-Max Normalization method.

    Args:
        metadata (dict): Dictionary that contains the metadata of the object whose values are being normalized.
        attr_name (str): Name of the attribute that must be normalized.
        min (dict): Dictionary that contains the minimum values of the attributes.
        max (dict): Dictionary that contains the maximum values of the attributes.

    Returns:
        normalized_value (float): Normalized value.
    """
    normalized_value = min_max_norm(x=metadata[attr_name], min=min[attr_name], max=max[attr_name])
    return normalized_value


def thea(parameters: dict = {}):
    """Heuristic algorithm that provisions composite applications on federated edge infrastructures taking into account the delay
    and privacy requirements of applications, the trust degree between application users and infrastructure providers, and the
    power consumption of edge servers.

    Args:
        parameters (dict, optional): Algorithm parameters. Defaults to {}.
    """
    while sum(1 for app in Application.all() if app.provisioned == False) > 0:
        apps = []
        for app in [app for app in Application.all() if app.provisioned == False]:

            delay_score = get_application_delay_score(app=app) * len(app.services)
            privacy_score = sum(
                [
                    normalize_cpu_and_memory(cpu=service.cpu_demand, memory=service.memory_demand) * service.privacy_requirement
                    for service in app.services
                ]
            )

            app_attrs = {
                "object": app,
                "number_of_services": len(app.services),
                "delay_sla": app.users[0].delay_slas[str(app.id)],
                "delay_score": delay_score,
                "privacy_score": privacy_score,
            }
            apps.append(app_attrs)

        apps = sorted(apps, key=lambda app: (app["delay_score"] * app["privacy_score"]) ** (1 / 2), reverse=True)

        app = apps[0]["object"]
        user = app.users[0]

        for service in app.services:
            edge_servers = get_host_candidates(user=user, service=service)

            # Finding the minimum and maximum values for the edge server attributes
            minimum = {}
            maximum = {}
            for edge_server_metadata in edge_servers:
                for attr_name, attr_value in edge_server_metadata.items():
                    if attr_name != "object":
                        if attr_name not in minimum or attr_name in minimum and attr_value < minimum[attr_name]:
                            minimum[attr_name] = attr_value
                        if attr_name not in maximum or attr_name in maximum and attr_value > maximum[attr_name]:
                            maximum[attr_name] = attr_value

            edge_servers = sorted(
                edge_servers,
                key=lambda s: (
                    s["sla_violations"],
                    get_norm(metadata=s, attr_name="affected_services_cost", min=minimum, max=maximum)
                    + get_norm(metadata=s, attr_name="power_consumption", min=minimum, max=maximum)
                    + get_norm(metadata=s, attr_name="delay_cost", min=minimum, max=maximum),
                ),
            )

            # Greedily iterating over the list of edge servers to find a host for the service
            for edge_server_metadata in edge_servers:
                edge_server = edge_server_metadata["object"]

                if edge_server.has_capacity_to_host(service):
                    provision(user=user, application=app, service=service, edge_server=edge_server)
                    break

        # Setting the application as provisioned once all of its services have been provisioned
        app.provisioned = True


def get_host_candidates(user: object, service: object) -> list:
    """Get list of host candidates for hosting services of a given user.
    Args:
        user (object): User object.
    Returns:
        list: List of host candidates.
    """
    chain = list([service.application.users[0]] + service.application.services)
    prev_item = chain[chain.index(service) - 1]
    switch_of_previous_item_in_chain = (
        prev_item.base_station.network_switch if chain.index(service) - 1 == 0 else prev_item.server.network_switch
    )
    app_delay = user.delays[str(service.application.id)] if user.delays[str(service.application.id)] != None else 0

    host_candidates = []

    for edge_server in EdgeServer.all():
        additional_delay = calculate_path_delay(
            origin_network_switch=switch_of_previous_item_in_chain, target_network_switch=edge_server.network_switch
        )
        overall_delay = app_delay + additional_delay

        delay_cost = additional_delay if service == service.application.services[-1] else 0

        trust_degree = user.providers_trust[str(edge_server.infrastructure_provider)]

        # Checking if any of the SLAs (delay or privacy) would be violated by hosting the service on the edge server
        violates_privacy_sla = 1 if trust_degree < service.privacy_requirement else 0
        violates_delay_sla = 1 if overall_delay > user.delay_slas[str(service.application.id)] else 0
        sla_violations = violates_delay_sla + violates_privacy_sla

        # Gathering the edge server's power consumption cost based on its CPU usage
        static_power_consumption = edge_server.power_model_parameters["static_power_percentage"]
        consumption_per_core = edge_server.power_model_parameters["max_power_consumption"] / edge_server.cpu
        power_consumption = consumption_per_core + static_power_consumption * (1 - sign(edge_server.cpu_demand))

        # Gathering the list of non-provisioned services that could possibly rely on the edge server regarding its trust degree
        affected_services = []
        for affected_service in Service.all():
            affected_user = affected_service.application.users[0]
            trust_on_the_edge_server = affected_user.providers_trust[str(edge_server.infrastructure_provider)]
            relies_on_the_edge_server = trust_on_the_edge_server >= affected_service.privacy_requirement

            if affected_service.server == None and affected_service != service and relies_on_the_edge_server:
                distance_to_affected_user = calculate_path_delay(
                    origin_network_switch=affected_user.base_station.network_switch, target_network_switch=edge_server.network_switch
                )
                distance_cost = 1 / max(1, distance_to_affected_user)
                affected_services.append(distance_cost)

        affected_services_cost = sum(affected_services) if service == service.application.services[-1] else 0

        host_candidates.append(
            {
                "object": edge_server,
                "sla_violations": sla_violations,
                "affected_services_cost": affected_services_cost,
                "power_consumption": power_consumption,
                "delay_cost": delay_cost,
            }
        )

    return host_candidates
