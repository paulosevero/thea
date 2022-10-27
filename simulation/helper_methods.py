# Importing EdgeSimPy components
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.user import User
from edge_sim_py.components.application import Application
from edge_sim_py.components.container_layer import ContainerLayer
from edge_sim_py.components.service import Service

# Importing Python libraries
import networkx as nx
import random


def uniform(n_items: int, valid_values: list, shuffle_distribution: bool = True) -> list:
    """Creates a list of size "n_items" with values from "valid_values" according to the uniform distribution.
    By default, the method shuffles the created list to avoid unbalanced spread of the distribution.

    Args:
        n_items (int): Number of items that will be created.
        valid_values (list): List of valid values for the list of values.
        shuffle_distribution (bool, optional): Defines whether the distribution is shuffled or not. Defaults to True.

    Raises:
        Exception: Invalid "valid_values" argument.

    Returns:
        uniform_distribution (list): List of values arranged according to the uniform distribution.
    """
    if not isinstance(valid_values, list) or isinstance(valid_values, list) and len(valid_values) == 0:
        raise Exception("You must inform a list of valid values within the 'valid_values' attribute.")

    # Number of occurrences that will be created of each item in the "valid_values" list
    distribution = [int(n_items / len(valid_values)) for _ in range(0, len(valid_values))]

    # List with size "n_items" that will be populated with "valid_values" according to the uniform distribution
    uniform_distribution = []

    for i, value in enumerate(valid_values):
        for _ in range(0, int(distribution[i])):
            uniform_distribution.append(value)

    # Computing leftover randomly to avoid disturbing the distribution
    leftover = n_items % len(valid_values)
    for i in range(leftover):
        random_valid_value = random.choice(valid_values)
        uniform_distribution.append(random_valid_value)

    # Shuffling distribution values in case 'shuffle_distribution' parameter is True
    if shuffle_distribution:
        random.shuffle(uniform_distribution)

    return uniform_distribution


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


def calculate_path_delay(origin_network_switch: object, target_network_switch: object) -> int:
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


def sign(value: int):
    """Calculates the sign of a real number using the well-known "sign" function (https://wikipedia.org/wiki/Sign_function).

    Args:
        value (int): Value whose sign must be calculated.

    Returns:
        (int): Sign of the passed value.
    """
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def min_max_norm(x, min, max):
    """Normalizes a given value (x) using the Min-Max Normalization method.

    Args:
        x (any): Value that must be normalized.
        min (any): Minimum value known.
        max (any): Maximum value known.

    Returns:
        (any): Normalized value.
    """
    if min == max:
        return 1
    return (x - min) / (max - min)


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


def find_minimum_and_maximum(metadata: list):
    """Finds the minimum and maximum values of a list of dictionaries.

    Args:
        metadata (list): List of dictionaries that contains the analyzed metadata.

    Returns:
        min_and_max (dict): Dictionary that contains the minimum and maximum values of the attributes.
    """
    min_and_max = {
        "minimum": {},
        "maximum": {},
    }

    for metadata_item in metadata:
        for attr_name, attr_value in metadata_item.items():
            if attr_name != "object":
                # Updating the attribute's minimum value
                if (
                    attr_name not in min_and_max["minimum"]
                    or attr_name in min_and_max["minimum"]
                    and attr_value < min_and_max["minimum"][attr_name]
                ):
                    min_and_max["minimum"][attr_name] = attr_value

                # Updating the attribute's maximum value
                if (
                    attr_name not in min_and_max["maximum"]
                    or attr_name in min_and_max["maximum"]
                    and attr_value > min_and_max["maximum"][attr_name]
                ):
                    min_and_max["maximum"][attr_name] = attr_value

    return min_and_max


def normalize_cpu_and_memory(cpu, memory) -> float:
    """Normalizes the CPU and memory values.

    Args:
        cpu (float): CPU value.
        memory (float): Memory value.

    Returns:
        normalized_value (float): Normalized value.
    """
    normalized_value = (cpu * memory) ** (1 / 2)
    return normalized_value


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
    """Evaluates a placement scheme based on the normalized number of SLA violations (delay and privacy) and power consumption."""
    # Gathering metrics
    metrics = Topology.first().collect()

    # Gathering the number of overloaded edge servers
    overloaded_edge_servers = metrics["overloaded_edge_servers"]

    # Gathering the overall edge server power consumption
    max_power_consumption_possible = sum([server.power_model_parameters["max_power_consumption"] for server in EdgeServer.all()])
    overall_power_consumption = metrics["overall_power_consumption"] / max_power_consumption_possible * 100

    # Gathering the number of SLA violations (delay and privacy)
    delay_sla_violations = metrics["delay_sla_violations"] / Application.count() * 100
    privacy_sla_violations = metrics["privacy_sla_violations"] / Service.count() * 100

    # Aggregating the results
    objectives = (delay_sla_violations, privacy_sla_violations, overall_power_consumption)
    penalties = overloaded_edge_servers

    output = (objectives, penalties)

    return output
