# EdgeSimPy components
from edge_sim_py import *

# Python libraries
from random import seed, choice
import matplotlib.pyplot as plt
import networkx as nx
import random
import copy


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


def display_topology(topology: object, output_filename: str = "topology"):
    # Customizing visual representation of topology
    positions = {}
    labels = {}
    colors = []
    sizes = []

    color_options = ["red", "green", "blue", "purple", "orange"]

    for index, node in enumerate(topology.nodes()):
        positions[node] = node.coordinates if hasattr(node, "coordinates") else index
        labels[node] = node.id if hasattr(node, "id") else index
        node_size = 500 if any(user.coordinates == node.coordinates for user in User.all()) else 100
        sizes.append(node_size)

        if len(node.base_station.edge_servers) > 0:
            colors.append(color_options[node.base_station.edge_servers[0].infrastructure_provider - 1])
        else:
            colors.append("black")

    # Configuring drawing scheme
    nx.draw(
        topology,
        pos=positions,
        node_color=colors,
        node_size=sizes,
        labels=labels,
        font_size=6,
        font_weight="bold",
        font_color="whitesmoke",
    )

    # Saving a topology image in the disk
    plt.savefig(f"{output_filename}.png", dpi=150)


# Application -> provisioned
def application_to_dict(self) -> dict:
    """Method that overrides the way the object is formatted to JSON."
    Returns:
        dict: JSON-friendly representation of the object as a dictionary.
    """
    dictionary = {
        "attributes": {
            "id": self.id,
            "label": self.label,
            "provisioned": self.provisioned,
        },
        "relationships": {
            "services": [{"class": type(service).__name__, "id": service.id} for service in self.services],
            "users": [{"class": type(user).__name__, "id": user.id} for user in self.users],
        },
    }
    return dictionary


# User -> providers_trust
def user_to_dict(self) -> dict:
    """Method that overrides the way User objects are formatted to JSON."

    Returns:
        dict: JSON-friendly representation of the object as a dictionary.
    """
    access_patterns = {}
    for app_id, access_pattern in self.access_patterns.items():
        access_patterns[app_id] = {"class": access_pattern.__class__.__name__, "id": access_pattern.id}

    dictionary = {
        "attributes": {
            "id": self.id,
            "coordinates": self.coordinates,
            "coordinates_trace": self.coordinates_trace,
            "delays": copy.deepcopy(self.delays),
            "delay_slas": copy.deepcopy(self.delay_slas),
            "communication_paths": copy.deepcopy(self.communication_paths),
            "making_requests": copy.deepcopy(self.making_requests),
            "providers_trust": copy.deepcopy(self.providers_trust),
        },
        "relationships": {
            "access_patterns": access_patterns,
            "mobility_model": self.mobility_model.__name__,
            "applications": [{"class": type(app).__name__, "id": app.id} for app in self.applications],
            "base_station": {"class": type(self.base_station).__name__, "id": self.base_station.id},
        },
    }
    return dictionary


# EdgeServer -> infrastructure_provider
def edge_server_to_dict(self) -> dict:
    """Method that overrides the way EdgeServer objects are formatted to JSON."

    Returns:
        dict: JSON-friendly representation of the object as a dictionary.
    """
    dictionary = {
        "attributes": {
            "id": self.id,
            "available": self.available,
            "model_name": self.model_name,
            "cpu": self.cpu,
            "memory": self.memory,
            "disk": self.disk,
            "cpu_demand": self.cpu_demand,
            "memory_demand": self.memory_demand,
            "disk_demand": self.disk_demand,
            "coordinates": self.coordinates,
            "max_concurrent_layer_downloads": self.max_concurrent_layer_downloads,
            "active": self.active,
            "power_model_parameters": self.power_model_parameters,
            "infrastructure_provider": self.infrastructure_provider,
        },
        "relationships": {
            "power_model": self.power_model.__name__ if self.power_model else None,
            "base_station": {"class": type(self.base_station).__name__, "id": self.base_station.id} if self.base_station else None,
            "network_switch": {"class": type(self.network_switch).__name__, "id": self.network_switch.id}
            if self.network_switch
            else None,
            "services": [{"class": type(service).__name__, "id": service.id} for service in self.services],
            "container_layers": [{"class": type(layer).__name__, "id": layer.id} for layer in self.container_layers],
            "container_images": [{"class": type(image).__name__, "id": image.id} for image in self.container_images],
            "container_registries": [{"class": type(reg).__name__, "id": reg.id} for reg in self.container_registries],
        },
    }
    return dictionary


# Service -> privacy_requirement
def service_to_dict(self) -> dict:
    """Method that overrides the way Service objects are formatted to JSON."

    Returns:
        dict: JSON-friendly representation of the object as a dictionary.
    """
    dictionary = {
        "attributes": {
            "id": self.id,
            "label": self.label,
            "state": self.state,
            "_available": self._available,
            "cpu_demand": self.cpu_demand,
            "memory_demand": self.memory_demand,
            "image_digest": self.image_digest,
            "privacy_requirement": self.privacy_requirement,
        },
        "relationships": {
            "application": {"class": type(self.application).__name__, "id": self.application.id},
            "server": {"class": type(self.server).__name__, "id": self.server.id} if self.server else None,
        },
    }
    return dictionary


# Defining a seed value to enable reproducibility
seed(1)

# Creating list of map coordinates
MAP_SIZE = 9
map_coordinates = hexagonal_grid(x_size=MAP_SIZE, y_size=MAP_SIZE)


# Creating base stations for providing wireless connectivity to users and network switches for wired connectivity
for coordinates in map_coordinates:
    # Creating the base station object
    base_station = BaseStation()
    base_station.wireless_delay = 0
    base_station.coordinates = coordinates

    # Creating network switch object using the "sample_switch()" generator, which embeds built-in power consumption specs
    network_switch = sample_switch()
    base_station._connect_to_network_switch(network_switch=network_switch)


# Creating a partially-connected mesh network topology
partially_connected_hexagonal_mesh(
    network_nodes=NetworkSwitch.all(),
    link_specifications=[
        {"number_of_objects": 208, "delay": 1, "bandwidth": 10},
    ],
)


def sgi_rackable_c2112_4g10() -> object:
    """Creates an EdgeServer object according to XXXX [TODO].

    Returns:
        edge_server (object): Created EdgeServer object.
    """
    edge_server = EdgeServer()
    edge_server.model_name = "SGI Rackable C2112-4G10"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    edge_server.cpu = 32
    edge_server.memory = 32768
    edge_server.disk = 1048576
    edge_server.mips = 2750

    # Power-related attributes
    edge_server.power_model_parameters = {
        "static_power_percentage": 265 / 1387,
        "max_power_consumption": 1387,
    }

    return edge_server


def proliant_dl360_gen9() -> object:
    """Creates an EdgeServer object according to XXXX [TODO].

    Returns:
        edge_server (object): Created EdgeServer object.
    """
    edge_server = EdgeServer()
    edge_server.model_name = "HPE ProLiant DL360 Gen9"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    edge_server.cpu = 36
    edge_server.memory = 65536
    edge_server.disk = 1048576
    edge_server.mips = 3000

    # Power-related attributes
    edge_server.power_model_parameters = {
        "static_power_percentage": 45 / 276,
        "max_power_consumption": 276,
    }

    return edge_server


def ar585_f1() -> object:
    """Creates an EdgeServer object according to XXXX [TODO].

    Returns:
        edge_server (object): Created EdgeServer object.
    """
    edge_server = EdgeServer()
    edge_server.model_name = "Acer AR585 F1"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    edge_server.cpu = 48
    edge_server.memory = 65536
    edge_server.disk = 1048576
    edge_server.mips = 3500

    # Power-related attributes
    edge_server.power_model_parameters = {
        "static_power_percentage": 127 / 559,
        "max_power_consumption": 559,
    }

    return edge_server


# Creating edge servers
SERVERS_PER_SPEC_TRUSTED_PROVIDERS = 1
SERVERS_PER_SPEC_UNTRUSTED_PROVIDER = 4
provider_specs = [
    {
        "id": 1,
        "edge_server_specs": [
            {"spec": sgi_rackable_c2112_4g10, "number_of_objects": SERVERS_PER_SPEC_TRUSTED_PROVIDERS},
            {"spec": proliant_dl360_gen9, "number_of_objects": SERVERS_PER_SPEC_TRUSTED_PROVIDERS},
            {"spec": ar585_f1, "number_of_objects": SERVERS_PER_SPEC_TRUSTED_PROVIDERS},
        ],
    },
    {
        "id": 2,
        "edge_server_specs": [
            {"spec": sgi_rackable_c2112_4g10, "number_of_objects": SERVERS_PER_SPEC_TRUSTED_PROVIDERS},
            {"spec": proliant_dl360_gen9, "number_of_objects": SERVERS_PER_SPEC_TRUSTED_PROVIDERS},
            {"spec": ar585_f1, "number_of_objects": SERVERS_PER_SPEC_TRUSTED_PROVIDERS},
        ],
    },
    {
        "id": 3,
        "edge_server_specs": [
            {"spec": sgi_rackable_c2112_4g10, "number_of_objects": SERVERS_PER_SPEC_UNTRUSTED_PROVIDER},
            {"spec": proliant_dl360_gen9, "number_of_objects": SERVERS_PER_SPEC_UNTRUSTED_PROVIDER},
            {"spec": ar585_f1, "number_of_objects": SERVERS_PER_SPEC_UNTRUSTED_PROVIDER},
        ],
    },
]

for provider_spec in provider_specs:
    for edge_server_spec in provider_spec["edge_server_specs"]:
        for _ in range(edge_server_spec["number_of_objects"]):
            # Creating the edge server object
            edge_server = edge_server_spec["spec"]()

            # Defining the maximum number of layers that the edge server can pull simultaneously
            edge_server.max_concurrent_layer_downloads = 3

            # Specifying the edge server's power model
            edge_server.power_model = LinearServerPowerModel

            # Edge server's infrastructure provider
            edge_server.infrastructure_provider = provider_spec["id"]

            # Connecting the edge server to a random base station
            base_stations_without_edge_servers = [bs for bs in BaseStation.all() if len(bs.edge_servers) == 0]
            base_station = random.sample(base_stations_without_edge_servers, 1)[0]
            base_station._connect_to_edge_server(edge_server=edge_server)

# Defining specifications for container images and container registries
container_image_specifications = [
    {
        "name": "alpine",
        "tag": "latest",
        "digest": "sha256:a777c9c66ba177ccfea23f2a216ff6721e78a662cd17019488c417135299cd89",
        "layers": [
            {
                "digest": "sha256:df9b9388f04ad6279a7410b85cedfdcb2208c0a003da7ab5613af71079148139",
                "size": 2,
                "instruction": "ADD file:5d673d25da3a14ce1f6cf",
            }
        ],
        "layers_digests": ["sha256:df9b9388f04ad6279a7410b85cedfdcb2208c0a003da7ab5613af71079148139"],
    },
    {
        "name": "registry",
        "tag": "latest",
        "digest": "sha256:6060f78eda124040cfeb19d2fcc9af417f5ee23dc05d0894fcfe21f24c9cbf9a",
        "layers": [
            {
                "digest": "sha256:df9b9388f04ad6279a7410b85cedfdcb2208c0a003da7ab5613af71079148139",
                "size": 2,
                "instruction": "ADD file:5d673d25da3a14ce1f6cf",
            },
            {
                "digest": "sha256:b6846b9db566bc2ea5e2b0056c49772152c9b7c8f06343efb1ef764b23bb9d96",
                "size": 5,
                "instruction": "/bin/sh -c set -eux; \tversion=",
            },
        ],
        "layers_digests": [
            "sha256:df9b9388f04ad6279a7410b85cedfdcb2208c0a003da7ab5613af71079148139",
            "sha256:b6846b9db566bc2ea5e2b0056c49772152c9b7c8f06343efb1ef764b23bb9d96",
        ],
    },
]


container_registry_specifications = [
    {
        "number_of_objects": 1,
        "cpu_demand": 0,
        "memory_demand": 0,
        "images": [
            {"name": "registry", "tag": "latest"},
            {"name": "alpine", "tag": "latest"},
        ],
    }
]

# Parsing the specifications for container images and container registries
container_registries = create_container_registries(
    container_registry_specifications=container_registry_specifications,
    container_image_specifications=container_image_specifications,
)


# Defining the initial placement for container images and container registries
worst_fit_registries(container_registry_specifications=container_registries, servers=EdgeServer.all())


# Defining user placement and applications/services specifications
def random_user_placement():
    """Method that determines the coordinates of a given user randomly.

    Returns:
        coordinates (tuple): Random user coordinates.
    """
    coordinates = choice(map_coordinates)
    return coordinates


# Defining applications/services specifications
application_specifications = [
    {"number_of_objects": 2, "number_of_services": 2},
    {"number_of_objects": 2, "number_of_services": 4},
    {"number_of_objects": 2, "number_of_services": 6},
]

# Defining user delay SLA values (application specs are mirrored for each provider and each application has its own user)
delay_slas = uniform(
    n_items=sum([app_spec["number_of_objects"] for app_spec in application_specifications]) * 2,
    valid_values=[3, 6],
    shuffle_distribution=True,
)

# Defining service demands
service_demand_values = [
    {"cpu": 2, "memory": 2 * 1024},
    {"cpu": 4, "memory": 4 * 1024},
    {"cpu": 8, "memory": 8 * 1024},
    {"cpu": 16, "memory": 16 * 1024},
]
# The number of services considers all service demand combinations multiplied by two (one for each highly trusted provider)
number_of_services = (
    sum([app_spec["number_of_objects"] * app_spec["number_of_services"] for app_spec in application_specifications]) * 2
)
service_demands = uniform(
    n_items=number_of_services,
    valid_values=service_demand_values,
    shuffle_distribution=True,
)

# Defining user/provider trust patterns
providers_trust_patterns = [[2, 1, 0], [1, 2, 0]]

for provider_trust_pattern in providers_trust_patterns:
    for app_spec in application_specifications:
        for _ in range(app_spec["number_of_objects"]):
            app = Application()
            app.provisioned = False

            # Creating the user that access the application
            user = User()

            # Defining user trust on the providers
            user.providers_trust = {1: provider_trust_pattern[0], 2: provider_trust_pattern[1], 3: provider_trust_pattern[2]}

            user.communication_paths[str(app.id)] = None
            user.delays[str(app.id)] = None
            user.delay_slas[str(app.id)] = delay_slas[user.id - 1]

            # Defining user's coordinates and connecting him to a base station
            user.mobility_model = random_mobility
            user._set_initial_position(coordinates=random_user_placement(), number_of_replicates=2)

            # Defining user's access pattern
            CircularDurationAndIntervalAccessPattern(
                user=user,
                app=app,
                start=1,
                duration_values=[float("inf")],
                interval_values=[0],
            )

            # Defining the relationship attributes between the user and the application
            user.applications.append(app)
            app.users.append(user)

            # Defining service privacy requirement values
            service_privacy_requirements = uniform(
                n_items=app_spec["number_of_services"], valid_values=[0, 1, 2], shuffle_distribution=False
            )
            service_privacy_requirements = sorted(service_privacy_requirements)

            # Creating the services that compose the application
            for service_index in range(app_spec["number_of_services"]):
                # Gathering information on the service image based on the specified 'name' and 'tag' parameters
                service_image = next((img for img in ContainerImage.all() if img.name == "alpine"), None)

                # Creating the service object
                service = Service(
                    image_digest=service_image.digest,
                    cpu_demand=None,
                    memory_demand=None,
                    label="Alpine",
                    state=0,
                )
                service.privacy_requirement = service_privacy_requirements[service_index]
                service.cpu_demand = service_demands[service.id - 1]["cpu"]
                service.memory_demand = service_demands[service.id - 1]["memory"]

                # Connecting the application to its new service
                app.connect_to_service(service)

##########################
#### DATASET ANALYSIS ####
##########################
# Calculating the network delay between users and edge servers (useful for defining reasonable delay SLAs)
users = []
for user in User.all():
    user_metadata = {"object": user, "all_delays": []}
    edge_servers = []
    for edge_server in EdgeServer.all():
        path = nx.shortest_path(
            G=Topology.first(), source=user.base_station.network_switch, target=edge_server.network_switch, weight="delay"
        )
        user_metadata["all_delays"].append(Topology.first().calculate_path_delay(path=path))
    user_metadata["min_delay"] = min(user_metadata["all_delays"])
    user_metadata["max_delay"] = max(user_metadata["all_delays"])
    user_metadata["avg_delay"] = sum(user_metadata["all_delays"]) / len(user_metadata["all_delays"])
    user_metadata["delays"] = {}
    for delay in sorted(list(set(user_metadata["all_delays"]))):
        user_metadata["delays"][delay] = user_metadata["all_delays"].count(delay)

    users.append(user_metadata)

print("\n\n==== NETWORK DISTANCE (DELAY) BETWEEN USERS AND EDGE SERVERS ====")
for user_metadata in users:
    user_attrs = {
        "object": user_metadata["object"],
        "sla": user_metadata["object"].delay_slas[str(user_metadata["object"].applications[0].id)],
        "min": user_metadata["min_delay"],
        "max": user_metadata["max_delay"],
        "avg": round(user_metadata["avg_delay"]),
        "delays": user_metadata["delays"],
    }
    print(f"{user_attrs}")
    if user_attrs["min"] > user_attrs["sla"]:
        print(f"\n\nWARNING: {user_attrs['object']} delay SLA is not achievable!\n\n")

# Calculating the infrastructure occupation and information about the services
edge_server_cpu_capacity = 0
edge_server_memory_capacity = 0
service_cpu_demand = 0
service_memory_demand = 0

for edge_server in EdgeServer.all():
    edge_server_cpu_capacity += edge_server.cpu
    edge_server_memory_capacity += edge_server.memory

for service in Service.all():
    service_cpu_demand += service.cpu_demand
    service_memory_demand += service.memory_demand

overall_cpu_occupation = round((service_cpu_demand / edge_server_cpu_capacity) * 100, 1)
overall_memory_occupation = round((service_memory_demand / edge_server_memory_capacity) * 100, 1)

print("\n\n==== INFRASTRUCTURE OCCUPATION OVERVIEW ====")
print(f"Edge Servers: {EdgeServer.count()}")
print(f"\tCPU Capacity: {edge_server_cpu_capacity}")
print(f"\tRAM Capacity: {edge_server_memory_capacity}")
print(f"Services: {Service.count()}")
print(f"\tCPU Demand: {service_cpu_demand}")
print(f"\t\t[Privacy Requirement = 0] {sum([s.cpu_demand for s in Service.all() if s.privacy_requirement == 0])}")
print(f"\t\t[Privacy Requirement = 1] {sum([s.cpu_demand for s in Service.all() if s.privacy_requirement == 1])}")
print(f"\t\t[Privacy Requirement = 2] {sum([s.cpu_demand for s in Service.all() if s.privacy_requirement == 2])}")
print(f"\tRAM Demand: {service_memory_demand}")
print(f"\t\t[Privacy Requirement = 0] {sum([s.memory_demand for s in Service.all() if s.privacy_requirement == 0])}")
print(f"\t\t[Privacy Requirement = 1] {sum([s.memory_demand for s in Service.all() if s.privacy_requirement == 1])}")
print(f"\t\t[Privacy Requirement = 2] {sum([s.memory_demand for s in Service.all() if s.privacy_requirement == 2])}")
print(f"Overall Occupation")
print(f"\tCPU: {overall_cpu_occupation}%")
print(f"\tRAM: {overall_memory_occupation}%")

# Calculating the occupation of each infrastructure provider
print("==== INFRASTRUCTURE PROVIDERS OVERVIEW ====")
for provider_id in range(1, len(provider_specs) + 1):
    provider_edge_servers = [s for s in EdgeServer.all() if s.infrastructure_provider == provider_id]

    users_with_trust0 = [user for user in User.all() if user.providers_trust[provider_id] == 0]
    users_with_trust1 = [user for user in User.all() if user.providers_trust[provider_id] == 1]
    users_with_trust2 = [user for user in User.all() if user.providers_trust[provider_id] == 2]

    demand_trust0 = sum(
        [sum([s.cpu_demand for s in u.applications[0].services if s.privacy_requirement == 0]) for u in users_with_trust0]
    )
    demand_trust1 = sum(
        [sum([s.cpu_demand for s in u.applications[0].services if s.privacy_requirement == 0]) for u in users_with_trust1]
    )
    demand_trust2 = sum(
        [sum([s.cpu_demand for s in u.applications[0].services if s.privacy_requirement == 0]) for u in users_with_trust2]
    )

    print(f"=== Provider {provider_id} ===")
    print(f"Overall CPU: {sum([s.cpu for s in provider_edge_servers])}")
    print(f"Overall RAM: {sum([s.memory for s in provider_edge_servers])}")
    print(f"\tUsers with trust 0: {len(users_with_trust0)}. CPU Demand: {demand_trust0}")
    print(f"\tUsers with trust 1: {len(users_with_trust1)}. CPU Demand: {demand_trust1}")
    print(f"\tUsers with trust 2: {len(users_with_trust2)}. CPU Demand: {demand_trust2}\n")

# Exporting scenario
Application._to_dict = application_to_dict
User._to_dict = user_to_dict
EdgeServer._to_dict = edge_server_to_dict
Service._to_dict = service_to_dict
ComponentManager.export_scenario(save_to_file=True, file_name="dataset1")
display_topology(Topology.first())
