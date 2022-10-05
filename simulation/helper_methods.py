# Importing EdgeSimPy components
from edge_sim_py.components.container_layer import ContainerLayer
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.network_switch import NetworkSwitch

# Importing Python libraries
import networkx as nx


def optimized_set_communication_path(self, app: object, communication_path: list = []) -> list:
    """Updates the set of links used during the communication of user and its application.
    Args:
        app (object): User application.
        communication_path (list, optional): User-specified communication path. Defaults to [].
    Returns:
        list: Updated communication path.
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
                path = find_shortest_path(
                    origin_network_switch=origin.network_switch, target_network_switch=target.network_switch
                )

            # Adding the best path found to the communication path
            self.communication_paths[str(app.id)].append([network_switch.id for network_switch in path])

            # Computing the new demand of chosen links
            path = [[NetworkSwitch.find_by_id(i) for i in p] for p in self.communication_paths[str(app.id)]]
            topology._allocate_communication_path(communication_path=path, app=app)

    # Computing application's delay
    self._compute_delay(app=app, metric="latency")

    return self.communication_paths[str(app.id)]


def provision(user: object, application: object, service: object, edge_server: object):
    """Provisions an application's service on an edge server.

    Args:
        user (object): User that accesses the application.
        application (object): Application to whom the service belongs.
        service (object): Service to be provisioned.
        edge_server (object): Edge server that will host the edge server.
    """
    # Updating the host's resource usage
    edge_server.cpu_demand += service.cpu_demand
    edge_server.memory_demand += service.memory_demand

    # Creating relationship between the host and the registry
    service.server = edge_server
    edge_server.services.append(service)

    for layer_metadata in edge_server._get_uncached_layers(service=service):
        layer = ContainerLayer(
            digest=layer_metadata.digest,
            size=layer_metadata.size,
            instruction=layer_metadata.instruction,
        )

        # Updating host's resource usage based on the layer size
        edge_server.disk_demand += layer.size

        # Creating relationship between the host and the layer
        layer.server = edge_server
        edge_server.container_layers.append(layer)

    user.set_communication_path(app=application)


def find_shortest_path(origin_network_switch: object, target_network_switch: object) -> int:
    """Finds the shortest path (delay used as weight) between two network switches (origin and target).

    Args:
        origin_network_switch (object): Origin network switch.
        target_network_switch (object): Target network switch.

    Returns:
        path (list): Shortest path between the origin and target network switches.
    """
    topology = origin_network_switch.model.topology
    path = []

    if not hasattr(topology, "delay_shortest_paths"):
        topology.delay_shortest_paths = {}

    key = (origin_network_switch, target_network_switch)

    if key in topology.delay_shortest_paths.keys():
        path = topology.delay_shortest_paths[key]
    else:
        path = nx.shortest_path(G=topology, source=origin_network_switch, target=target_network_switch, weight="delay")
        topology.delay_shortest_paths[key] = path

    return path


def get_delay(origin_network_switch: object, target_network_switch: object) -> int:
    """Gets the distance (in terms of delay) between two network switches (origin and target).

    Args:
        origin_network_switch (object): Origin network switch.
        target_network_switch (object): Target network switch.

    Returns:
        delay (int): Delay between the origin and target network switches.
    """
    topology = origin_network_switch.model.topology

    path = find_shortest_path(origin_network_switch=origin_network_switch, target_network_switch=target_network_switch)
    delay = topology.calculate_path_delay(path=path)

    return delay
