# Importing EdgeSimPy components
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.application import Application

# Importing helper methods
from simulation.helper_methods import *


def argos(parameters: dict = {}):
    """Privacy-aware service provisioning strategy for edge computing environments proposed in [1].

    [1] Souza, P.; Crestani, Â.; Rubin, F.; Ferreto, T. and Rossi, F. (2022). Latency-aware Privacy-preserving
    Service Migration in Federated Edges. In International Conference on Cloud Computing and Services Science (CLOSER),
    pages 288-295. DOI: 10.5220/0011084500003200.

    Args:
        parameters (dict, optional): Algorithm parameters. Defaults to {}.
    """
    apps = sorted(Application.all(), key=lambda app: app.users[0].delay_slas[str(app.id)])

    for app in apps:
        user = app.users[0]
        services = sorted(app.services, key=lambda s: (-s.privacy_requirement, -s.cpu_demand))

        edge_servers = sorted(get_host_candidates(user=user), key=lambda s: (-s["trust_degree"], s["delay"]))

        for service in services:
            # Greedily iterating over the list of edge servers to find a host for the service
            for edge_server_metadata in edge_servers:
                edge_server = edge_server_metadata["object"]

                if edge_server.has_capacity_to_host(service):
                    provision(user=user, application=app, service=service, edge_server=edge_server)
                    break


def get_host_candidates(user: object) -> list:
    """Get list of host candidates for hosting services of a given user.
    Args:
        user (object): User object.
    Returns:
        list: List of host candidates.
    """
    user_switch = user.base_station.network_switch
    host_candidates = []
    for edge_server in EdgeServer.all():
        host_candidates.append(
            {
                "object": edge_server,
                "delay": calculate_path_delay(origin_network_switch=user_switch, target_network_switch=edge_server.network_switch),
                "trust_degree": user.providers_trust[str(edge_server.infrastructure_provider)],
            }
        )

    return host_candidates
