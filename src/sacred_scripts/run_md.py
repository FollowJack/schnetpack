from sacred import Experiment
import os
import torch
import yaml
from shutil import rmtree

from schnetpack.sacred.calculator_ingredients import (calculator_ingradient,
                                                      build_calculator)
from schnetpack.sacred.simulator_ingredients import (simulator_ingredient,
                                                     build_simulator)
from schnetpack.sacred.integrator_ingredients import (integrator_ingredient,
                                                      build_integrator)
from schnetpack.sacred.system_ingredients import (system_ingredient,
                                                  build_system)
from schnetpack.sacred.thermostat_ingredients import thermostat_ingredient, \
    build_thermostat


md = Experiment('md', ingredients=[simulator_ingredient, calculator_ingradient,
                                   integrator_ingredient, system_ingredient,
                                   thermostat_ingredient])


@md.config
def config():
    """configuration for the simulation experiment"""
    experiment_dir = './experiments'
    simulation_steps = 1000
    device = 'cpu'
    path_to_molecules = os.path.join(experiment_dir, 'data/ethanol.xyz')
    simulation_dir = os.path.join(experiment_dir, 'simulation')
    training_dir = os.path.join(experiment_dir, 'training')
    model_path = os.path.join(training_dir, 'best_model')
    overwrite = True


@md.capture
def save_config(_config, simulation_dir):
    """
    Save the configuration to the model directory.

    Args:
        _config (dict): configuration of the experiment
        simulation_dir (str): path to the simulation directory

    """
    with open(os.path.join(simulation_dir, 'config.yaml'), 'w') as f:
        yaml.dump(_config, f, default_flow_style=False)


@md.capture
def load_model(model_path):
    return torch.load(model_path)


@md.capture
def setup_simulation(simulation_dir, device, path_to_molecules):
    model = load_model()
    calculator = build_calculator(model=model)
    integrator = build_integrator()
    system = build_system(device=device, path_to_molecules=path_to_molecules)
    thermostat = build_thermostat()
    simulator = build_simulator(system=system,
                                integrator_object=integrator,
                                calculator_object=calculator,
                                simulation_dir=simulation_dir,
                                thermostat_object=thermostat)
    return simulator


@md.capture
def create_dirs(_log, simulation_dir, overwrite):
    """
    Create the directory for the experiment.

    Args:
        _log:
        experiment_dir (str): path to the experiment directory
        overwrite (bool): overwrites the model directory if True

    """
    _log.info("Create model directory")
    if simulation_dir is None:
        raise ValueError('Config `experiment_dir` has to be set!')

    if os.path.exists(simulation_dir) and not overwrite:
        raise ValueError(
            'Model directory already exists (set overwrite flag?):',
            simulation_dir)

    if os.path.exists(simulation_dir) and overwrite:
        rmtree(simulation_dir)

    if not os.path.exists(simulation_dir):
        os.makedirs(simulation_dir)


@md.command
def simulate(simulation_dir, simulation_steps):
    create_dirs()
    save_config()
    simulator = setup_simulation(simulation_dir=simulation_dir)
    simulator.simulate(simulation_steps)


@md.automain
def main():
    print(md.config)


