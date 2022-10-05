# Importing EdgeSimPy components
from edge_sim_py.components.user import User
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.application import Application

# Importing helper methods
from .helper_methods import *


def argos(parameters: dict = {}):
    """Privacy-aware service migration strategy for edge computing environments."""

    apps = sorted(Application.all(), key=lambda app: app.users[0].delay_slas[str(app.id)])

    for app in apps:
        user = app.users[0]
        services = sorted(app.services, key=lambda s: (-s.privacy_requirement, -s.cpu_demand))

        edge_servers = sorted(get_host_candidates(user=user), key=lambda s: (-s["is_trusted"], s["delay"]))

        for service in services:
            # Greedily iterating over the list of edge servers to find a host for the service
            for edge_server_metadata in edge_servers:
                edge_server = edge_server_metadata["object"]

                if edge_server.has_capacity_to_host(service):
                    provision(user=user, application=app, service=service, edge_server=edge_server)
                    break

        user.set_communication_path(app=app)


def get_host_candidates(user: object) -> list:
    """Get list of host candidates for hosting services of a given user.
    Args:
        user (object): User object.
    Returns:
        list: List of host candidates.
    """
    host_candidates = []

    for edge_server in EdgeServer.all():
        delay = get_delay(
            origin_network_switch=user.base_station.network_switch, target_network_switch=edge_server.network_switch
        )

        # trusted_users = sum([1 for u in User.all() if edge_server in u.trusted_servers and u != user])
        # is_trusted = 1 if edge_server in user.trusted_servers else 0
        trusted_users = [u.providers_trust[str(edge_server.infrastructure_provider)] for u in User.all() if u != user]
        is_trusted = user.providers_trust[str(edge_server.infrastructure_provider)]

        host_candidates.append(
            {
                "object": edge_server,
                "delay": delay,
                "trusted_users": trusted_users,
                "is_trusted": is_trusted,
            }
        )

    return host_candidates
