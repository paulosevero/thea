# Importing EdgeSimPy components
from edge_sim_py import *

# Importing helper methods
from .helper_methods import *

# Importing strategies
from .nsgaii import nsgaii
from .argos import argos
from .faticanti2020 import faticanti2020
from .thea import thea

# Importing Python libraries
from random import seed


seed(1)

# Creating a Simulator object
simulator = Simulator(
    tick_duration=1,
    tick_unit="seconds",
    stopping_criterion=lambda model: model.schedule.steps == 1,
    # resource_management_algorithm=nsgaii,
    # resource_management_algorithm=argos,
    # resource_management_algorithm=faticanti2020,
    resource_management_algorithm=thea,
    dump_interval=float("inf"),
)

# Loading a sample dataset from GitHub
simulator.initialize(input_file="datasets/sample_dataset1.json")

print(f"=== BEFORE === Container Layers: {ContainerLayer.count()}")

# Executing the simulation
User.set_communication_path = optimized_set_communication_path
simulator.run_model()

# print("=== EDGE SERVERS ===")
# for s in EdgeServer.all():
#     cap = [s.cpu, s.memory, s.disk]
#     dem = [s.cpu_demand, s.memory_demand, s.disk_demand]
#     print(f"    {s}. Capacity: {cap}. Demand: {dem}. Provider: {s.infrastructure_provider}. Power: {s.power_model_parameters}")

# print("")

# print("=== USERS ===")
# for u in User.all():
#     sw = u.base_station.network_switch
#     print(
#         f"    {u}. Coordinates: {u.coordinates} (sw={sw}). SLA: {u.delay_slas[str(u.applications[0].id)]}. Trust: {u.providers_trust}."
#     )
#     for a in u.applications:
#         u.set_communication_path(a)
#         delay = u.delays[str(a.id)]
#         delay_sla = u.delay_slas[str(a.id)]
#         print(f"        {a}. SLA: {delay_sla}. Delay: {delay}. Path: {u.communication_paths[str(a.id)]}")
#         for s in a.services:
#             trust = u.providers_trust[str(s.server.infrastructure_provider)] if s.server else None
#             sw = s.server.network_switch if s.server else None
#             print(
#                 f"            {s}. Dem: [{s.cpu_demand}, {s.memory_demand}]. Priv: {s.privacy_requirement}. Host: {s.server} (trust={trust}, sw={sw})"
#             )

# print(f"=== AFTER === Container Layers: {ContainerLayer.count()}")

print("==== METRICS ====")
SAMPLE_TEST = True
delay_sla_violations = []
privacy_sla_violations = []
overall_edge_server_power_consumption = 0
for user in User.all():
    for app in user.applications:
        delay_sla = user.delay_slas[str(app.id)]
        delay = user.delays[str(app.id)]

        # Calculating objective #1: Number of Delay SLA Violations
        if delay > delay_sla:
            if app not in delay_sla_violations:
                delay_sla_violations.append(app)

        # Calculating objective #2: Number of Privacy SLA Violations
        for service in app.services:
            if service.server and service.privacy_requirement > user.providers_trust[str(service.server.infrastructure_provider)]:
                privacy_sla_violations.append(service)

for edge_server in EdgeServer.all():
    # Calculating objective #3: Infrastructure's Power Consumption
    if SAMPLE_TEST:
        if edge_server.cpu_demand > 0:
            if edge_server.cpu == 8:
                overall_edge_server_power_consumption += 250
            elif edge_server.cpu == 12:
                overall_edge_server_power_consumption += 550
    else:
        overall_edge_server_power_consumption += edge_server.get_power_consumption()

print(f"Delay SLA Violations: {len(delay_sla_violations)} => {delay_sla_violations}")
print(f"Privacy SLA Violations: {len(privacy_sla_violations)} => {privacy_sla_violations}")
print(f"Power Consumption: {overall_edge_server_power_consumption}")
