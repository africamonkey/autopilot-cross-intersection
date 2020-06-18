import platform
from cross_road_network import CrossRoadNetwork
from flow.core.params import SumoParams, EnvParams
from flow.controllers import RLController
from rl_env import CrossRoadRLAccelEnv, ADDITIONAL_ENV_PARAMS
import json

import ray
from ray.rllib.agents.ppo.ppo import DEFAULT_CONFIG
from ray.tune import run_experiments
from ray.tune.registry import register_env
from ray.rllib.agents.ppo import PPOTrainer

from flow.utils.registry import make_create_env
from flow.utils.rllib import FlowParamsEncoder
from sumo_parameters import get_net_params, get_initial_config, get_vehicle_params


if __name__ == "__main__":
    network_name = CrossRoadNetwork
    name = "ppo_training"
    net_params = get_net_params(inflow_probability=0.3)
    initial_config = get_initial_config()
    vehicles = get_vehicle_params(RLController, {}, True)

    sumo_params = SumoParams(render=False, sim_step=0.1, restart_instance=True)
    HORIZON = 600
    env_params = EnvParams(
        horizon=HORIZON,
        warmup_steps=150,
        additional_params=ADDITIONAL_ENV_PARAMS,
    )
    env_name = CrossRoadRLAccelEnv
    flow_params = dict(
        exp_tag=name,
        env_name=env_name,
        network=network_name,
        simulator='traci',
        sim=sumo_params,
        env=env_params,
        net=net_params,
        veh=vehicles,
        initial=initial_config
    )
    flow_params_for_test = flow_params
    flow_params_for_test['veh'] = get_vehicle_params(RLController, {}, False)

    N_CPUS = 2
    N_ROLLOUTS = 20

    ray.init(num_cpus=N_CPUS)
    alg_run = "PPO"

    config = DEFAULT_CONFIG

    # Common Configs
    config["num_workers"] = N_CPUS - 1
    config["train_batch_size"] = HORIZON * N_ROLLOUTS
    config["gamma"] = 0.999
    config["horizon"] = HORIZON
    # config["log_level"] = "DEBUG"

    # PPO Specific Configs
    config["lr"] = 5e-5
    config["lambda"] = 0.95
    config["kl_coeff"] = 0.5
    config["clip_rewards"] = False
    config["clip_param"] = 0.1
    config["vf_clip_param"] = 10.0
    config["entropy_coeff"] = 0.01
    config["sgd_minibatch_size"] = 600
    config["num_sgd_iter"] = 30

    config["batch_mode"] = "complete_episodes"

    # save the flow params for replay
    flow_json = json.dumps(flow_params_for_test, cls=FlowParamsEncoder, sort_keys=True,
                           indent=4)  # generating a string version of flow_params
    config['env_config']['flow_params'] = flow_json  # adding the flow_params to config dict
    config['env_config']['run'] = alg_run

    # Call the utility function make_create_env to be able to
    # register the Flow env for this experiment
    create_env, gym_name = make_create_env(params=flow_params, version=0)

    # Register as rllib env with Gym
    register_env(gym_name, create_env)

    trials = run_experiments({
        flow_params["exp_tag"]: {
            "run": alg_run,
            "env": gym_name,
            "config": {
                **config
            },
            "checkpoint_freq": 5,  # number of iterations between checkpoints
            "checkpoint_at_end": True,  # generate a checkpoint at the end
            "max_failures": 999,
            "stop": {  # stopping conditions
                "training_iteration": 100000000,  # number of iterations to stop after
            },
        },
    })
