# Importing EdgeSimPy components
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.application import Application
from edge_sim_py.components.service import Service

# Importing helper methods
from simulation.helper_methods import *


def thea(parameters: dict = {}):
    """Heuristic algorithm that provisions composite applications on federated edge infrastructures taking into account the delay
    and privacy requirements of applications, the trust degree between application users and infrastructure providers, and the
    power consumption of edge servers.

    Args:
        parameters (dict, optional): Algorithm parameters. Defaults to {}.
    """
    # Thea continues to run until all applications are provisioned
    while sum(1 for app in Application.all() if not app.provisioned) > 0:

        # Sorting applications according to their delay and privacy scores
        apps = []
        for app in [app for app in Application.all() if not app.provisioned]:
            app_attrs = {
                "object": app,
                "number_of_services": len(app.services),
                "delay_sla": app.users[0].delay_slas[str(app.id)],
                "delay_score": get_application_delay_score(app=app),
                "privacy_score": get_application_privacy_score(app=app),
            }
            apps.append(app_attrs)

        # Gathering the application with the highest delay and privacy score to be provisioned
        min_and_max = find_minimum_and_maximum(metadata=apps)
        app = sorted(
            apps,
            key=lambda app: (
                get_norm(metadata=app, attr_name="delay_score", min=min_and_max["minimum"], max=min_and_max["maximum"])
                + get_norm(metadata=app, attr_name="privacy_score", min=min_and_max["minimum"], max=min_and_max["maximum"])
            ),
            reverse=True,
        )[0]["object"]
        user = app.users[0]

        # Iterating over the list of services that compose the application
        for service in app.services:
            # Gathering the list of edge servers candidates for hosting the service
            edge_servers = get_host_candidates(user=user, service=service)

            # Finding the minimum and maximum values for the edge server attributes
            min_and_max = find_minimum_and_maximum(metadata=edge_servers)

            # Sorting edge server host candidates based on the number of SLA violations they
            # would cause to the application and their power consumption and delay costs
            edge_servers = sorted(
                edge_servers,
                key=lambda s: (
                    s["sla_violations"],
                    get_norm(metadata=s, attr_name="affected_services_cost", min=min_and_max["minimum"], max=min_and_max["maximum"])
                    + get_norm(metadata=s, attr_name="power_consumption", min=min_and_max["minimum"], max=min_and_max["maximum"])
                    + get_norm(metadata=s, attr_name="delay_cost", min=min_and_max["minimum"], max=min_and_max["maximum"]),
                ),
            )

            # Greedily iterating over the list of edge servers to find a host for the service
            for edge_server_metadata in edge_servers:
                edge_server = edge_server_metadata["object"]

                # Provisioning the service on the best edge server found it it has enough resources
                if edge_server.has_capacity_to_host(service):
                    provision(user=user, application=app, service=service, edge_server=edge_server)
                    break

        # Setting the application as provisioned once all of its services have been provisioned
        app.provisioned = True


def get_application_delay_score(app: object) -> float:
    """Calculates the application delay score considering the number application's SLA and the number of edge servers close enough
    to the application's user that could be used to host the application's services without violating the delay SLA.

    Args:
        app (object): Application whose delay score will be calculated.

    Returns:
        app_delay_score (float): Application's delay score.
    """
    # Gathering information about the application
    delay_sla = app.users[0].delay_slas[str(app.id)]
    user_switch = app.users[0].base_station.network_switch

    # Gathering the list of hosts close enough to the user that could be used to host the services without violating the delay SLA
    edge_servers_that_dont_violate_delay_sla = 0
    for edge_server in EdgeServer.all():
        if calculate_path_delay(origin_network_switch=user_switch, target_network_switch=edge_server.network_switch) <= delay_sla:
            edge_servers_that_dont_violate_delay_sla += 1

    if min(edge_servers_that_dont_violate_delay_sla, delay_sla) == 0:
        app_delay_score = 0
    else:
        app_delay_score = 1 / ((edge_servers_that_dont_violate_delay_sla * delay_sla) ** (1 / 2))

    app_delay_score = app_delay_score * len(app.services)

    return app_delay_score


def get_application_privacy_score(app: object):
    """Calculates the application privacy score considering the demand and privacy requirements of its services.

    Args:
        app (object): Application whose privacy score will be calculated.

    Returns:
        app_privacy_score (float): Application's privacy score.
    """
    app_privacy_score = 0

    for service in app.services:
        normalized_demand = normalize_cpu_and_memory(cpu=service.cpu_demand, memory=service.memory_demand)
        privacy_requirement = service.privacy_requirement
        service_privacy_score = normalized_demand * (1 + privacy_requirement)
        app_privacy_score += service_privacy_score

    return app_privacy_score


def get_host_candidates(user: object, service: object) -> list:
    """Get list of host candidates for hosting services of a given user.
    Args:
        user (object): User object.
    Returns:
        host_candidates (list): List of host candidates.
    """
    chain = list([service.application.users[0]] + service.application.services)
    prev_item = chain[chain.index(service) - 1]
    switch_of_previous_item_in_chain = (
        prev_item.base_station.network_switch if chain.index(service) - 1 == 0 else prev_item.server.network_switch
    )
    app_delay = user.delays[str(service.application.id)] if user.delays[str(service.application.id)] is not None else 0

    host_candidates = []

    for edge_server in EdgeServer.all():
        additional_delay = calculate_path_delay(
            origin_network_switch=switch_of_previous_item_in_chain, target_network_switch=edge_server.network_switch
        )
        overall_delay = app_delay + additional_delay
        delay_cost = additional_delay if service == service.application.services[-1] else 0

        # Checking if any of the SLAs (delay or privacy) would be violated by hosting the service on the edge server
        violates_privacy_sla = 1 if user.providers_trust[str(edge_server.infrastructure_provider)] < service.privacy_requirement else 0
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

            if affected_service.server is None and affected_service != service and relies_on_the_edge_server:
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
