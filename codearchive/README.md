# Comparative Study of Controlling Autonomous Vehicles through Intersections

## Install Flow and SUMO Environments

We used Flow in this project. In order to compare with traditional methods, we added TTC, PRM controller to Flow. Please follow the [Flow setup documents](https://flow.readthedocs.io/en/latest/flow_setup.html) to install Flow and SUMO environments. Remember to download the Flow github repository modified by me, instead of the official one. 

Modified Flow github repository: `https://github.com/africamonkey/flow`

Kindly remind you that Flow only supports **Ubuntu** and **MacOS**. 

## Tutorials

We recommend you to read the tutorials of Flow, which can help you learn how to use Flow. 

Link: `https://github.com/flow-project/flow/tree/master/tutorials/`

## Source Codes

You can find everything in the folder `src`. 

### Network

Network was defined in `src/cross_road_network.py`. We described the intersection by specifying nodes and edges. We also specified car routes, where `"W2M"` indicated cars from west to east, `"E2M"` indicated cars from east to west, and `"SS2M"` indicated the autonomous car. The autonomous car goes straight by default, but you can uncomment the left turn/right turn to turn the car left/right.  

### SUMO Parameters

We defined inflows parameters, net parameters, car following parameters, and vehicle parameters in `src/sumo_parameters.py`. 

### Environments

1) Traditional Environment

This environment is modified based on AccelEnv(flow.envs.ring.accel) and is provided to TTC and PRM algorithm. See also in `src/ttc_env.py`. 

2) Reinforcement Learning Environment

This environment is provided to DQN and PPO algorithm. See also in `src/rl_env.py`. 

### Utilities

1) Random State

Save random state to make the scene reproducible. See also in `src/random_state.py`. 

2) XML Analyzer

After every simulation, SUMO will output a series of XMLs. XML analyzer help us read the XMLs ,judge whether succeed or not, collide or not, and calculate average transit time. See also in `src/xml_analyzer.py`. 

### Traditional Method

1) Single Journey

Single journey scripts use GUI version of SUMO. You can watch the simulation when the algorithm is running. Simulation runs only once, but you can use Random State Utility to reproduce. 

In `src/ttc_single_journey.py`, parameters `ttc_threshold` and `inflow_probability` can be set here. 

**Important:** `inflow_probability` specifies the traffic density from west to east **or** from east to west, it's one-way. So, if you want to represent 0.6 vehicles/second of traffic density, you should use `inflow_probability=0.3`. 

In `src/prm_single_journey.py`, parameters `t_c`, `d_s`, `lambda_a`, `r_go`, and `inflow_probability` can be set here. 

2) Batch Run

Batch run scripts use NO-GUI (i.e. command line) version of SUMO. They can help us batch run the simulations automatically, save emission files and random seeds for reproduction use. 

In `src/ttc_batch_run.py` and `src/prm_batch_run.py`, there are 3 command line arguments to control which kind of emissions and seeds should be saved: a) If `--delete_all_xml` was set to be true, all of the emissions and seeds would be deleted after simulations and analyzations. b) If `--delete_uncollision_xml` was set to be true, successful and timeout emissions and seeds would be deleted. c) `--max_log` indicates the maximum amount of emissions to save. 

Parameters like `inflow_probability` should be set in the corresponding single journey script. 

### Reinforcement Learning Method

1) Training

DQN training code can be found in `src/rl_dqn_training.py` while PPO training code can be found in `src/rl_ppo_training.py`. If you want to modify the configs, please follow the guide  [here](https://ray.readthedocs.io/en/latest/rllib-algorithms.html). Parameters `inflow_probability` should also be set in this file. 

Kindly remind you to set `N_CPUS` properly. 

Checkpoints and results will be saved to `~/ray_results/`. You can use Tensorboard to visualize the progress by typing command `tensorboard --logdir ~/ray_results/`. 

2) Single Journey

Single Journey scripts can be found in `src/rl_single_journey.py` and `src/rl_single_journey_nogui.py`. The NO-GUI version is for filtering collision/timeout cases, and save emissions/seeds. 

You need to change the result directory and checkpoint number to make it work. 

If you want to use the same `inflow_probability` as the training part, there's no more actions required. But if you train a model in `inflow_probability=0.3`, and want to see the performance in the `inflow_probability=0.1` environment, you should modify the `params.json` and `params.pkl` in corresponding training folder in `~/ray_results/`. Just search `inflow_probability` and you will find where to modify. 

3) Batch Run

Batch run scripts can be found in `src/rl_batch_run.py`. This will help us calculate success rate, collision rate, etc. 

4) Make A Video

Use `src/rl_make_video.py` to make a video. If you want to reproduce some cases that previously saved, `load_random_state()` function will help you. 

## Results

Raw results are provided in `results` folder. We also publish the trained models corresponding to these results, which are provided in `models` folder. 
