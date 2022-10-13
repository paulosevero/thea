# Importing EdgeSimPy components
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.service import Service

# Importing helper methods
from simulation.helper_methods import *


def faticanti2020(parameters: dict = {}):
    """Adapted version of [1], that focuses on finding host servers for microservice-based applications on
    Edge Computing scenarios with multiple infrastructure providers.

    [1] Faticanti, Francescomaria, et al. "Deployment of Application Microservices in Multi-Domain Federated
    Fog Environments." International Conference on Omni-layer Intelligent Systems (COINS). IEEE, 2020.

    Args:
        parameters (dict, optional): Algorithm parameters. Defaults to {}.
    """
    # Sorting services based on their positions in their application's service chain
    services = sorted(Service.all(), key=lambda service: service.application.services.index(service))

    for service in services:
        app = service.application
        user = app.users[0]

        # Sorting edge servers by: trustworthiness, distance from user (in terms of delay), and free resources
        edge_servers = sorted(
            EdgeServer.all(),
            key=lambda s: (
                -(user.providers_trust[str(s.infrastructure_provider)]),
                calculate_path_delay(origin_network_switch=user.base_station.network_switch, target_network_switch=s.network_switch),
                s.cpu - s.cpu_demand,
            ),
        )

        # Greedily iterating over the list of EdgeNode candidates to find the best node to host the service
        for edge_server in edge_servers:
            if edge_server.has_capacity_to_host(service):
                provision(user=user, application=app, service=service, edge_server=edge_server)
                break
