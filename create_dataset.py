# EdgeSimPy components
from edge_sim_py import *

# Python libraries
import copy
from random import seed, choice
import networkx as nx
import matplotlib.pyplot as plt


def display_topology(topology: object, output_filename: str = "topology"):
    # Customizing visual representation of topology
    positions = {}
    labels = {}
    colors = []
    for index, node in enumerate(topology.nodes()):
        positions[node] = node.coordinates if hasattr(node, "coordinates") else index
        labels[node] = node.id if hasattr(node, "id") else index

        if len(node.base_station.edge_servers) > 0:
            colors.append("red")
        else:
            colors.append("black")

    # Configuring drawing scheme
    nx.draw(topology, pos=positions, node_color=colors, labels=labels, font_size=6, font_weight="bold", font_color="whitesmoke")

    # Saving a topology image in the disk
    plt.savefig(f"{output_filename}.png", dpi=150)


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
            "base_station": {"class": type(self.base_station).__name__, "id": self.base_station.id}
            if self.base_station
            else None,
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
map_coordinates = hexagonal_grid(x_size=7, y_size=7)


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
        {"number_of_objects": 120, "delay": 1, "bandwidth": 10},
    ],
)


def sample_server1() -> object:
    """Creates an EdgeServer object according to a sample specifications set.

    Returns:
        edge_server (object): Created EdgeServer object.
    """
    edge_server = EdgeServer()
    edge_server.model_name = "Sample Server Spec #1"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    edge_server.cpu = 8
    edge_server.memory = 8192
    edge_server.disk = 131072

    # Power-related attributes
    edge_server.power_model_parameters = {
        "static_power_percentage": 54.1,
        "max_power_consumption": 243,
    }

    return edge_server


def sample_server2():
    """Creates an EdgeServer object according to a sample specifications set.

    Returns:
        edge_server (object): Created EdgeServer object.
    """
    edge_server = EdgeServer()
    edge_server.model_name = "Sample Server Spec #2"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    edge_server.cpu = 12
    edge_server.memory = 12288
    edge_server.disk = 131072

    # Power-related attributes
    edge_server.power_model_parameters = {
        "static_power_percentage": 127,
        "max_power_consumption": 559,
    }

    return edge_server


# Creating edge servers
base_stations_ids = [43, 49, 37, 32, 22, 28, 11, 1, 7]
infrastructure_providers = [1, 1, 2, 2, 3, 3, 1, 3, 2]
specs = [
    sample_server1,
    sample_server2,
    sample_server2,
    sample_server1,
    sample_server1,
    sample_server2,
    sample_server1,
    sample_server1,
    sample_server2,
]

for i in range(9):
    # Creating the edge server object
    edge_server = specs[i]()

    # Defining the maximum number of layers that the edge server can pull simultaneously
    edge_server.max_concurrent_layer_downloads = 3

    # Specifying the edge server's power model
    edge_server.power_model = LinearServerPowerModel

    # Edge server's infrastructure provider
    edge_server.infrastructure_provider = infrastructure_providers[edge_server.id - 1]

    # Connecting the edge server to a random base station
    base_station = BaseStation.find_by_id(base_stations_ids[edge_server.id - 1])
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
        "name": "nginx",
        "tag": "latest",
        "digest": "sha256:83d487b625d8c7818044c04f1b48aabccd3f51c3341fc300926846bca0c439e6",
        "layers": [
            {
                "digest": "sha256:c229119241af7b23b121052a1cae4c03e0a477a72ea6a7f463ad7623ff8f274b",
                "size": 29,
                "instruction": "ADD file:966d3669b40f5fbaecee1",
            },
            {
                "digest": "sha256:2215908dc0a28873ff92070371b1ba3a3cb9d4440d44926c5f29f47a76b17b35",
                "size": 24,
                "instruction": "/bin/sh -c set -x     && addgr",
            },
        ],
        "layers_digests": [
            "sha256:c229119241af7b23b121052a1cae4c03e0a477a72ea6a7f463ad7623ff8f274b",
            "sha256:2215908dc0a28873ff92070371b1ba3a3cb9d4440d44926c5f29f47a76b17b35",
        ],
    },
    {
        "name": "ubuntu",
        "tag": "latest",
        "digest": "sha256:31cd7bbfd36421dfd338bceb36d803b3663c1bfa87dfe6af7ba764b5bf34de05",
        "layers": [
            {
                "digest": "sha256:e0b25ef516347a097d75f8aea6bc0f42a4e8e70b057e84d85098d51f96d458f9",
                "size": 27,
                "instruction": "ADD file:b83df51ab7caf8a4dc35f",
            }
        ],
        "layers_digests": ["sha256:e0b25ef516347a097d75f8aea6bc0f42a4e8e70b057e84d85098d51f96d458f9"],
    },
    {
        "name": "python",
        "tag": "latest",
        "digest": "sha256:dff8c1e4c3a609e87c05f1e08399332cf2dfb2b41d9bc91e142eb5c2bee887a0",
        "layers": [
            {
                "digest": "sha256:dbba69284b2786013fe94fefe0c2e66a7d3cecbb20f6d691d71dac891ee37be5",
                "size": 52,
                "instruction": "ADD file:e8d512b08fe2ddc6f2c85",
            },
            {
                "digest": "sha256:9baf437a1badb6aad2dae5f2cd4a7b53a6c7ab6c14cba1ed1ecb42b4822b0e87",
                "size": 4,
                "instruction": "/bin/sh -c set -eux; \tapt-get ",
            },
            {
                "digest": "sha256:6ade5c59e324bd7cf369c72ad781c23d37e8fb48c9bbb4abbecafafd9be4cc35",
                "size": 10,
                "instruction": "/bin/sh -c set -ex; \tif ! comm",
            },
            {
                "digest": "sha256:b19a994f6d4cdbb620339bd2e4ad47b229f14276b542060622ae447649294e5d",
                "size": 52,
                "instruction": "/bin/sh -c apt-get update && a",
            },
            {
                "digest": "sha256:8fc2294f89de5e20d0ae12149d6136444bcb8c775ea745f06f2eb775ab4504cd",
                "size": 187,
                "instruction": "/bin/sh -c set -ex; \tapt-get u",
            },
            {
                "digest": "sha256:9dc715194c21dec8f4d20ea4faa9929b2297b24c123fc8459709266f43e83449",
                "size": 5,
                "instruction": "/bin/sh -c set -eux; \tapt-get ",
            },
            {
                "digest": "sha256:59dc3c5729cd1d72b2fd0913953484d4ecc453f833e0ab53d074bcd6c0746d27",
                "size": 18,
                "instruction": "/bin/sh -c set -eux; \t\twget -O",
            },
            {
                "digest": "sha256:2050bfe553ed386581e99bb5724e3565b1dc444ce5d5ce7fb355876e66e655e8",
                "size": 2,
                "instruction": "/bin/sh -c set -eux; \t\twget -O",
            },
        ],
        "layers_digests": [
            "sha256:dbba69284b2786013fe94fefe0c2e66a7d3cecbb20f6d691d71dac891ee37be5",
            "sha256:9baf437a1badb6aad2dae5f2cd4a7b53a6c7ab6c14cba1ed1ecb42b4822b0e87",
            "sha256:6ade5c59e324bd7cf369c72ad781c23d37e8fb48c9bbb4abbecafafd9be4cc35",
            "sha256:b19a994f6d4cdbb620339bd2e4ad47b229f14276b542060622ae447649294e5d",
            "sha256:8fc2294f89de5e20d0ae12149d6136444bcb8c775ea745f06f2eb775ab4504cd",
            "sha256:9dc715194c21dec8f4d20ea4faa9929b2297b24c123fc8459709266f43e83449",
            "sha256:59dc3c5729cd1d72b2fd0913953484d4ecc453f833e0ab53d074bcd6c0746d27",
            "sha256:2050bfe553ed386581e99bb5724e3565b1dc444ce5d5ce7fb355876e66e655e8",
        ],
    },
    {
        "name": "postgres",
        "tag": "latest",
        "digest": "sha256:d67b82a04a19b72667264a9641873c15e2195ccfeb82b3d4a653673cdfc1f2cf",
        "layers": [
            {
                "digest": "sha256:5c2a8045f9de06328ab3d0ff505d990892219b7faee393bc9ac342347fc83d04",
                "size": 28,
                "instruction": "ADD file:32aa9fd7ee5c64e4bd494",
            },
            {
                "digest": "sha256:602c15e6b04ce0152d8397747b43883ed8da9c6d3b77f88a4156c8808b42a107",
                "size": 4,
                "instruction": "/bin/sh -c set -ex; \tif ! comm",
            },
            {
                "digest": "sha256:8e25582ffd7cb07fb4f3987d1cbca9c80ff0d95c0a4ffc067d9faa17f97074a0",
                "size": 1,
                "instruction": "/bin/sh -c set -eux; \tsavedApt",
            },
            {
                "digest": "sha256:59483323305f97a3f72f8358ad29d9b9c9234934cd21edad917ef2d92033f68e",
                "size": 7,
                "instruction": "/bin/sh -c set -eux; \tif [ -f ",
            },
            {
                "digest": "sha256:eb192a0edc8f2d7b523bfcd1e62331a5eb517945eed1b4973a87a775753eb36d",
                "size": 1,
                "instruction": "/bin/sh -c set -eux; \tapt-get ",
            },
            {
                "digest": "sha256:5fa84b0f5ddec145f4ffd600e50e8abad1db41e816a3f336c7feb6cab4b75ed4",
                "size": 83,
                "instruction": "/bin/sh -c set -ex; \t\texport P",
            },
        ],
        "layers_digests": [
            "sha256:5c2a8045f9de06328ab3d0ff505d990892219b7faee393bc9ac342347fc83d04",
            "sha256:602c15e6b04ce0152d8397747b43883ed8da9c6d3b77f88a4156c8808b42a107",
            "sha256:8e25582ffd7cb07fb4f3987d1cbca9c80ff0d95c0a4ffc067d9faa17f97074a0",
            "sha256:59483323305f97a3f72f8358ad29d9b9c9234934cd21edad917ef2d92033f68e",
            "sha256:eb192a0edc8f2d7b523bfcd1e62331a5eb517945eed1b4973a87a775753eb36d",
            "sha256:5fa84b0f5ddec145f4ffd600e50e8abad1db41e816a3f336c7feb6cab4b75ed4",
        ],
    },
    {
        "name": "redis",
        "tag": "latest",
        "digest": "sha256:1b36e146475b71ee04da1ce60f201308392ff8468107f91615885d2e49536010",
        "layers": [
            {
                "digest": "sha256:c229119241af7b23b121052a1cae4c03e0a477a72ea6a7f463ad7623ff8f274b",
                "size": 29,
                "instruction": "ADD file:966d3669b40f5fbaecee1",
            },
            {
                "digest": "sha256:5e59eaa723f193c889435d757b05fcc030596d2f075c7fecbbd538a53200aa40",
                "size": 1,
                "instruction": "/bin/sh -c set -eux; \tsavedApt",
            },
            {
                "digest": "sha256:fd5ad76698193c47aa7a5711c08dc24d97c5cc9d1a40e22a6647f45a6e1389a7",
                "size": 7,
                "instruction": "/bin/sh -c set -eux; \t\tsavedAp",
            },
        ],
        "layers_digests": [
            "sha256:c229119241af7b23b121052a1cae4c03e0a477a72ea6a7f463ad7623ff8f274b",
            "sha256:5e59eaa723f193c889435d757b05fcc030596d2f075c7fecbbd538a53200aa40",
            "sha256:fd5ad76698193c47aa7a5711c08dc24d97c5cc9d1a40e22a6647f45a6e1389a7",
        ],
    },
    {
        "name": "node",
        "tag": "latest",
        "digest": "sha256:87cea4658eb63b6bc1fb52a5f0c7f3c833615449f6e803cb8f2182f2a59ae09d",
        "layers": [
            {
                "digest": "sha256:dbba69284b2786013fe94fefe0c2e66a7d3cecbb20f6d691d71dac891ee37be5",
                "size": 52,
                "instruction": "ADD file:e8d512b08fe2ddc6f2c85",
            },
            {
                "digest": "sha256:9baf437a1badb6aad2dae5f2cd4a7b53a6c7ab6c14cba1ed1ecb42b4822b0e87",
                "size": 4,
                "instruction": "/bin/sh -c set -eux; \tapt-get ",
            },
            {
                "digest": "sha256:6ade5c59e324bd7cf369c72ad781c23d37e8fb48c9bbb4abbecafafd9be4cc35",
                "size": 10,
                "instruction": "/bin/sh -c set -ex; \tif ! comm",
            },
            {
                "digest": "sha256:b19a994f6d4cdbb620339bd2e4ad47b229f14276b542060622ae447649294e5d",
                "size": 52,
                "instruction": "/bin/sh -c apt-get update && a",
            },
            {
                "digest": "sha256:8fc2294f89de5e20d0ae12149d6136444bcb8c775ea745f06f2eb775ab4504cd",
                "size": 187,
                "instruction": "/bin/sh -c set -ex; \tapt-get u",
            },
            {
                "digest": "sha256:6b0eb7b290939e1eb2829c8c423a87f044b13dce23bfe7241f67408f9b732bc8",
                "size": 42,
                "instruction": '/bin/sh -c ARCH= && dpkgArch="',
            },
            {
                "digest": "sha256:9349bc5bacd1cfacfebf2f06fb628f9a759933cddd7d5039e1cfe3a05d26c0f8",
                "size": 2,
                "instruction": "/bin/sh -c set -ex   && for ke",
            },
        ],
        "layers_digests": [
            "sha256:dbba69284b2786013fe94fefe0c2e66a7d3cecbb20f6d691d71dac891ee37be5",
            "sha256:9baf437a1badb6aad2dae5f2cd4a7b53a6c7ab6c14cba1ed1ecb42b4822b0e87",
            "sha256:6ade5c59e324bd7cf369c72ad781c23d37e8fb48c9bbb4abbecafafd9be4cc35",
            "sha256:b19a994f6d4cdbb620339bd2e4ad47b229f14276b542060622ae447649294e5d",
            "sha256:8fc2294f89de5e20d0ae12149d6136444bcb8c775ea745f06f2eb775ab4504cd",
            "sha256:6b0eb7b290939e1eb2829c8c423a87f044b13dce23bfe7241f67408f9b732bc8",
            "sha256:9349bc5bacd1cfacfebf2f06fb628f9a759933cddd7d5039e1cfe3a05d26c0f8",
        ],
    },
    {
        "name": "mongo",
        "tag": "latest",
        "digest": "sha256:31bb47830cb0ff00f90be54a62f8be416189bd0b52f4a76bb5ac3f450860228a",
        "layers": [
            {
                "digest": "sha256:e0b25ef516347a097d75f8aea6bc0f42a4e8e70b057e84d85098d51f96d458f9",
                "size": 27,
                "instruction": "ADD file:b83df51ab7caf8a4dc35f",
            },
            {
                "digest": "sha256:7a6592c2fb05fb80b5a3c01c92bc623faf5fc0ded7dd0551be39ea78a4d9efc8",
                "size": 2,
                "instruction": "/bin/sh -c set -eux; \tapt-get ",
            },
            {
                "digest": "sha256:5dad2281c276115bf50711681c05326e6a65cec55a5d727481ac937664a35efa",
                "size": 6,
                "instruction": "/bin/sh -c set -ex; \t\tsavedApt",
            },
            {
                "digest": "sha256:97291b67bd8ea1784d4f2c2bb8d0563a2e67091848d6bda10ef42e8c54d96b32",
                "size": 201,
                "instruction": "/bin/sh -c set -x \t&& export D",
            },
        ],
        "layers_digests": [
            "sha256:e0b25ef516347a097d75f8aea6bc0f42a4e8e70b057e84d85098d51f96d458f9",
            "sha256:7a6592c2fb05fb80b5a3c01c92bc623faf5fc0ded7dd0551be39ea78a4d9efc8",
            "sha256:5dad2281c276115bf50711681c05326e6a65cec55a5d727481ac937664a35efa",
            "sha256:97291b67bd8ea1784d4f2c2bb8d0563a2e67091848d6bda10ef42e8c54d96b32",
        ],
    },
    {
        "name": "openjdk",
        "tag": "latest",
        "digest": "sha256:afbe5f6d76c1eedbbd2f689c18c1984fd67121b369fc0fbd51c510caf4f9544f",
        "layers": [
            {
                "digest": "sha256:e4430e06691f65e516df7d62db0ee5393acea9ade644cc6bc620efef0956dd17",
                "size": 40,
                "instruction": "ADD file:eaa532cad071c531a759e",
            },
            {
                "digest": "sha256:99ce5342b806de618f4fa582eca53ecee5a73ef976daa060d249227e1927d814",
                "size": 12,
                "instruction": "/bin/sh -c set -eux; \tmicrodnf",
            },
            {
                "digest": "sha256:603e156f2a3d954d3516817cf4a802f31365085b43426685c995ad144fde567a",
                "size": 178,
                "instruction": '/bin/sh -c set -eux; \t\tarch="$',
            },
        ],
        "layers_digests": [
            "sha256:e4430e06691f65e516df7d62db0ee5393acea9ade644cc6bc620efef0956dd17",
            "sha256:99ce5342b806de618f4fa582eca53ecee5a73ef976daa060d249227e1927d814",
            "sha256:603e156f2a3d954d3516817cf4a802f31365085b43426685c995ad144fde567a",
        ],
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
    {
        "name": "debian",
        "tag": "latest",
        "digest": "sha256:0040bafca14127bdc2dcb0d9897a26f5d44136e89c02046710de6ea01a227278",
        "layers": [
            {
                "digest": "sha256:dbba69284b2786013fe94fefe0c2e66a7d3cecbb20f6d691d71dac891ee37be5",
                "size": 52,
                "instruction": "ADD file:e8d512b08fe2ddc6f2c85",
            }
        ],
        "layers_digests": ["sha256:dbba69284b2786013fe94fefe0c2e66a7d3cecbb20f6d691d71dac891ee37be5"],
    },
]


container_registry_specifications = [
    {
        "number_of_objects": 5,
        "cpu_demand": 0,
        "memory_demand": 0,
        "images": [
            {"name": "registry", "tag": "latest"},
            {"name": "alpine", "tag": "latest"},
            {"name": "nginx", "tag": "latest"},
            {"name": "ubuntu", "tag": "latest"},
            {"name": "python", "tag": "latest"},
            {"name": "debian", "tag": "latest"},
            {"name": "node", "tag": "latest"},
            {"name": "postgres", "tag": "latest"},
            {"name": "openjdk", "tag": "latest"},
            {"name": "redis", "tag": "latest"},
            {"name": "mongo", "tag": "latest"},
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


application_specifications = [
    {
        "number_of_objects": 1,
        "users": [
            {
                "delay_sla": 5,
                "provisioning_time_sla": 0,
                "base_station": BaseStation.find_by_id(5),
                "coordinates": random_user_placement,
                "mobility_model": pathway,
                "providers_trust": {"1": 1, "2": 2, "3": 3},
                "access_pattern": {
                    "model": CircularDurationAndIntervalAccessPattern,
                    "start": 1,
                    "duration_values": [float("inf")],
                    "interval_values": [0],
                },
            },
        ],
        "services": [
            {
                "image": {"name": "alpine"},
                "cpu_demand": 4,
                "memory_demand": 4096,
                "label": "alpine",
                "state": 0,
                "privacy_requirement": 1,
            },
            {
                "image": {"name": "nginx"},
                "cpu_demand": 7,
                "memory_demand": 7168,
                "label": "nginx",
                "state": 0,
                "privacy_requirement": 3,
            },
        ],
    },
    {
        "number_of_objects": 1,
        "users": [
            {
                "delay_sla": 4,
                "provisioning_time_sla": 0,
                "base_station": BaseStation.find_by_id(46),
                "coordinates": random_user_placement,
                "mobility_model": pathway,
                "providers_trust": {"1": 3, "2": 1, "3": 2},
                "access_pattern": {
                    "model": CircularDurationAndIntervalAccessPattern,
                    "start": 1,
                    "duration_values": [float("inf")],
                    "interval_values": [0],
                },
            },
        ],
        "services": [
            {
                "image": {"name": "ubuntu"},
                "cpu_demand": 5,
                "memory_demand": 5120,
                "label": "ubuntu",
                "state": 0,
                "privacy_requirement": 2,
            },
            {
                "image": {"name": "python"},
                "cpu_demand": 2,
                "memory_demand": 2048,
                "label": "python",
                "state": 0,
                "privacy_requirement": 3,
            },
        ],
    },
    {
        "number_of_objects": 1,
        "users": [
            {
                "delay_sla": 2,
                "provisioning_time_sla": 0,
                "base_station": BaseStation.find_by_id(17),
                "coordinates": random_user_placement,
                "mobility_model": pathway,
                "providers_trust": {"1": 2, "2": 3, "3": 1},
                "access_pattern": {
                    "model": CircularDurationAndIntervalAccessPattern,
                    "start": 1,
                    "duration_values": [float("inf")],
                    "interval_values": [0],
                },
            },
        ],
        "services": [
            {
                "image": {"name": "debian"},
                "cpu_demand": 4,
                "memory_demand": 4096,
                "label": "debian",
                "state": 0,
                "privacy_requirement": 2,
            }
        ],
    },
    {
        "number_of_objects": 1,
        "users": [
            {
                "delay_sla": 4,
                "provisioning_time_sla": 0,
                "base_station": BaseStation.find_by_id(41),
                "coordinates": random_user_placement,
                "mobility_model": pathway,
                "providers_trust": {"1": 1, "2": 2, "3": 3},
                "access_pattern": {
                    "model": CircularDurationAndIntervalAccessPattern,
                    "start": 1,
                    "duration_values": [float("inf")],
                    "interval_values": [0],
                },
            },
        ],
        "services": [
            {
                "image": {"name": "node"},
                "cpu_demand": 2,
                "memory_demand": 2048,
                "label": "node",
                "state": 0,
                "privacy_requirement": 1,
            },
            {
                "image": {"name": "postgres"},
                "cpu_demand": 5,
                "memory_demand": 5120,
                "label": "postgres",
                "state": 0,
                "privacy_requirement": 2,
            },
        ],
    },
    {
        "number_of_objects": 1,
        "users": [
            {
                "delay_sla": 5,
                "provisioning_time_sla": 0,
                "base_station": BaseStation.find_by_id(36),
                "coordinates": random_user_placement,
                "mobility_model": pathway,
                "providers_trust": {"1": 3, "2": 1, "3": 2},
                "access_pattern": {
                    "model": CircularDurationAndIntervalAccessPattern,
                    "start": 1,
                    "duration_values": [float("inf")],
                    "interval_values": [0],
                },
            },
        ],
        "services": [
            {
                "image": {"name": "openjdk"},
                "cpu_demand": 1,
                "memory_demand": 1024,
                "label": "openjdk",
                "state": 0,
                "privacy_requirement": 3,
            },
            {
                "image": {"name": "redis"},
                "cpu_demand": 5,
                "memory_demand": 5120,
                "label": "redis",
                "state": 0,
                "privacy_requirement": 2,
            },
            {
                "image": {"name": "mongo"},
                "cpu_demand": 3,
                "memory_demand": 3072,
                "label": "mongo",
                "state": 0,
                "privacy_requirement": 1,
            },
        ],
    },
]


# Creating applications and services based on the "application_specifications" list
users_base_stations = [5, 46, 17, 41, 36]
for app_spec in application_specifications:
    # Creating "n" applications with each of the specifications according to the "number_of_objects" attributes
    for _ in range(app_spec["number_of_objects"]):
        app = Application()

        # Creating users that access the application
        for user_spec in app_spec["users"]:
            user = User()

            # Connecting the user to the application
            user._connect_to_application(app=app, delay_sla=user_spec["delay_sla"])
            user.communication_paths[str(app.id)] = {}

            user.provisioning_time_slas = {}
            user.provisioning_time_slas[str(app.id)] = user_spec["provisioning_time_sla"]

            # Defining user's mobility model
            user.mobility_model = user_spec["mobility_model"]

            # User's trust in each of the infrastructure providers
            user.providers_trust = user_spec["providers_trust"]

            # Defining user's coordinates and connecting him to a base station
            initial_base_station = BaseStation.find_by_id(users_base_stations[user.id - 1])
            user._set_initial_position(coordinates=user_spec["base_station"].coordinates, number_of_replicates=60)
            # user._set_initial_position(coordinates=user_spec["coordinates"](), number_of_replicates=60)

            # Defining user's access pattern
            user_spec["access_pattern"]["model"](
                user=user,
                app=app,
                start=user_spec["access_pattern"]["start"],
                duration_values=user_spec["access_pattern"]["duration_values"],
                interval_values=user_spec["access_pattern"]["interval_values"],
            )

        # Creating the services that compose the application
        for service_spec in app_spec["services"]:
            # Gathering information on the service image based on the specified 'name' and 'tag' parameters
            service_image = next(
                (img for img in ContainerImage.all() if img.name == service_spec["image"]["name"]),
                None,
            )
            if not service_image:
                raise Exception(f"There is no image with name '{service_spec['image']}' inside the container registries.")

            # Creating the service object
            service = Service(
                image_digest=service_image.digest,
                cpu_demand=service_spec["cpu_demand"],
                memory_demand=service_spec["memory_demand"],
                label=service_spec["label"],
                state=service_spec["state"],
            )
            service.privacy_requirement = service_spec["privacy_requirement"]

            # Connecting the application to its new service
            app.connect_to_service(service)


# Exporting scenario
User._to_dict = user_to_dict
EdgeServer._to_dict = edge_server_to_dict
Service._to_dict = service_to_dict
ComponentManager.export_scenario(save_to_file=True, file_name="sample_dataset1")

display_topology(Topology.first())

print("=== EDGE SERVERS ===")
for s in EdgeServer.all():
    print(
        f"    {s}. Cap: [{s.cpu}, {s.memory}, {s.disk}]. Provider: {s.infrastructure_provider}. Power: {s.power_model_parameters}"
    )

print("")

print("=== USERS ===")
for u in User.all():
    print(f"    {u}. SLA: {u.delay_slas[str(u.applications[0].id)]}. Trust: {u.providers_trust}")
    for a in u.applications:
        print(f"        {a}")
        for s in a.services:
            print(f"            {s}. Dem: [{s.cpu_demand}, {s.memory_demand}]. Priv: {s.privacy_requirement}. Host: {s.server}")
