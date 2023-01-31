# Thea

> This repository presents **Thea**, a resource management strategy designed for placing microservice-based applications in federated edge computing infrastructures while mutually considering the objectives of resource providers and their clients.

## Table of Contents

- [Overview](#overview)
  - [Motivation](#motivation)
  - [Repository Structure](#repository-structure)
- [Installation Guide](#installation-guide)
  - [Prerequisites](#prerequisites)
  - [Configuration](#configuration)
- [Usage Guide](#usage-guide)
  - [Reproducing Paper Experiments](#reproducing-paper-experiments)
    - [Faticanti](#faticanti)
    - [Argos](#argos)
    - [NSGA-II](#nsga-ii)
    - [Thea](#thea-1)
- [Manuscript](#manuscript)
  - [Access](#access)
  - [How to Cite](#how-to-cite)

## Overview

This section contains information about what motivated the design of Thea and about the repository structure.

### Motivation

Federated edge infrastructures present an enhanced availability of resources to clients due to the presence of multiple providers.
In this scenario, resource management techniques should employ decisions that mutually consider the objectives of resource providers and their clients while scheduling applications.
However, despite the contributions from existing strategies, they focus exclusively on addressing objectives for a single party.
To address this situation, Thea places microservice-based applications in federated edge environments by mutually considering the constraints imposed by resource providers and their clients.

### Repository Structure

Within the repository, you'll find the following directories and files, logically grouping common assets used to simulate microservice placement on federated edge computing infrastructures. You'll see something like this:

```
├── create_dataset.py
├── datasets/
├── pyproject.toml
├── run_experiments.py
├── results.ipynb
└── simulation/
    ├── __main__.py
    ├── custom_component_methods.py
    ├── helper_methods.py
    └── strategies/
        ├── argos.py
        ├── faticanti2020.py
        ├── nsgaii.py
        └── thea.py
```

In the root directory, the `pyproject.toml` file organizes all project dependencies, including the minimum required version of the Python language. This file guides the execution of Poetry, a Python library that installs the dependencies securely, avoiding conflicts with external packages.

> Modifications made to the `pyproject.toml` file are automatically inserted into `poetry.lock` whenever Poetry is called.

The `run_experiments.py` file makes it easy to execute the implemented strategies. For instance, with a few instructions, we can conduct a complete sensitivity analysis of the algorithms using different sets of parameters.

The `results.ipynb` file contains the code used to compute the results presented in the paper.

The `datasets` directory contains JSON files describing the scenario and components that will be simulated during the experiments and PNG files representing these scenarios. We can also create custom datasets and generate their representation by modifying the `create_dataset.py` file.

The `simulation` directory contains the `strategies` subdirectory, which accommodates the source code for the strategies used in the simulator. It also contains the `custom_component_methods.py` and the `helper_methods.py` files, which host methods that extend the standard functionality of the simulated components.

## Installation Guide

This section contains information about the prerequisites of the system and about how to configure the environment to execute the simulations.

Project dependencies are available for Linux, Windows, and macOS. However, we highly recommend using a recent version of a Debian-based Linux distribution. The installation below was validated on **Ubuntu 20.04.5 LTS**.

### Prerequisites

The first step needed to run the simulation is installing Python 3. We can do that by executing the following command:

```bash
sudo apt install python3 python3-distutils -y
```

We use a Python library called Poetry to manage project dependencies. In addition to selecting and downloading proper versions of project dependencies, Poetry automatically provisions virtual environments for the simulator, avoiding problems with external dependencies. On Linux and macOS, we can install Poetry with the following command:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

The command above installs Poetry executable inside Poetry’s bin directory. On Unix, it is located at `$HOME/.local/bin`. We can get more information about Poetry installation from their [documentation page](https://python-poetry.org/docs/#installation).

### Configuration

Considering that we already downloaded the repository, we first need to install dependencies using Poetry. To do so, we access the command line in the root directory and type the following command:

```bash
poetry shell
```

The command we just ran creates a virtual Python environment that we will use to run the simulator. Notice that Poetry automatically sends us to the newly created virtual environment. Next, we need to install the project dependencies using the following command:

```bash
poetry install
```

After a few moments, Poetry will have installed all the dependencies needed by the simulator and we will be ready to run the experiments.

## Usage Guide

This section contains general instructions about the execution of the simulator and specific instructions about how to reproduce our experiments.

### EdgeSimPy

We employ [EdgeSimPy](https://edgesimpy.github.io/) to simulate our strategy and compare it with strategies from related works.
The most basic arguments from EdgeSimPy are `--dataset` and `--algorithm`.
These arguments tell the simulator which dataset file and which algorithm (located at `simulator/strategies`) it should execute, respectively.
Also, we can pass additional parameters when executing maintenance strategies with configurable hyperparameters (as with NSGA-II).

### Reproducing Paper Experiments

Below are the commands executed to reproduce the experiments presented in our paper. Please notice that the commands below need to be run inside the virtual environment created by Poetry after the project's dependencies have been successfully installed.

#### Faticanti

```bash
python -B -m simulation --dataset "datasets/dataset1.json" --algorithm "faticanti2020"
```

#### Argos

```bash
python -B -m simulation --dataset "datasets/dataset1.json" --algorithm "argos"
```

#### NSGA-II

Unlike the other maintenance strategies, NSGA-II has configurable parameters that modify the behavior of the genetic algorithm it uses to make placement decisions. A description of the custom parameters adopted by this strategy is given below:

- `--pop_size`: determines how many individuals (solutions) will compose the population of the genetic algorithm.
- `--n_gen`: determines for how many generations the genetic algorithm will be executed.
- `--cross_prob`: determines the probability that individuals from the genetic algorithm's population are crossed to generate offsprings.
- `--mut_prob`: determines the probability that elements from the chromosome suffer a mutation.

```bash
python -B -m simulation --dataset "datasets/dataset1.json" --algorithm "nsgaii" --pop_size 120 --n_gen 800 --cross_prob 1 --mut_prob 0.2
```

#### Thea

```bash
python -B -m simulation --dataset "datasets/dataset1.json" --algorithm "thea"
```

## Manuscript

This section contains information about where to find Thea's manuscript and how to cite our work.

### Access

To be defined.

### How to Cite

To be defined.