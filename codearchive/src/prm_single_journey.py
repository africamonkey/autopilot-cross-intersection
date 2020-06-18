import os
from random_state import load_random_state
from flow.core.params import SumoParams, EnvParams
from flow.core.experiment import Experiment
from flow.controllers import PRMController
from ttc_env import CrossRoadAccelEnv, ADDITIONAL_ENV_PARAMS

from cross_road_network import CrossRoadNetwork
from sumo_parameters import get_net_params, get_initial_config, get_vehicle_params


def cross_road_experiment(render=None):
    """ Parameters & Returns: tutorials/tutorial05_networks.ipynb """
    vehicles = get_vehicle_params(PRMController, {
        "t_c": 6.0,
        "d_s": 55.0,
        "lambda_a": 1,
        "r_go": 0.1,
        "max_accel": 2.0,
        "max_deaccel": 4.5,
        "desire_v": 20.0,
        "d_nudge": 10.0,
        "discount": 0.2,
        "debug": False,
    })

    env_params = EnvParams(
        warmup_steps=150,
        additional_params=ADDITIONAL_ENV_PARAMS,
    )
    net_params = get_net_params(inflow_probability=0.3)
    sumo_params = SumoParams(
        render=True,
        emission_path="./emission/",
        summary_path="./emission/",
        tripinfo_path="./emission/",
        sim_step=0.1,
        restart_instance=True
    )
    if render is not None:
        sumo_params.render = render
    initial_config = get_initial_config()

    network = CrossRoadNetwork(
        name="cross_road_network",
        vehicles=vehicles,
        net_params=net_params,
        initial_config=initial_config
    )

    env = CrossRoadAccelEnv(env_params, sumo_params, network)
    return Experiment(env)


if __name__ == "__main__":
    random_state = load_random_state()
    exp = cross_road_experiment()
    emission_location = os.path.join(exp.env.sim_params.emission_path, exp.env.network.name)
    print(emission_location + '-emission.xml')
    with open(emission_location + '-seed', "w") as seed_file:
        seed_file.write(random_state.__str__())
    exp.run(1, 600)
