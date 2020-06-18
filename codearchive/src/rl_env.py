"""Environment for training the acceleration behavior of vehicles in a ring."""
from gym.spaces import Discrete

from flow.envs.base import Env
from flow.utils.ttc_utils import car_ttc
from flow.core.util import ensure_dir

from gym.spaces.box import Box

import numpy as np

RL_ACCEL = [-4.0, -2.0, 0.0, 2.0]
X_OBSERVE_METER = 80
Y_OBSERVE_METER = 20
X_PIXEL = 20
Y_PIXEL = 10
INF = 1E20

ADDITIONAL_ENV_PARAMS = {
    'max_accel': 2.5,
    'max_decel': 4.5,
    'target_velocity': 10,
    'sort_vehicles': False,
    'reward_success': 2000,
    'penalty_collision': -20000,
    'penalty_step_base': 1.005,
    'low_speed_threshold': 1.0,
}


class CrossRoadRLAccelEnv(Env):

    def __init__(self, env_params, sim_params, network, simulator='traci'):
        for p in ADDITIONAL_ENV_PARAMS.keys():
            if p not in env_params.additional_params:
                raise KeyError(
                    'Environment parameter \'{}\' not supplied'.format(p))

        self.continuous_low_speed = 0
        self.prev_pos = dict()
        self.absolute_position = dict()
        if sim_params.emission_path is not None:
            self.path = sim_params.emission_path
            if self.path[-1] != '/':
                self.path += '/'
            self.path += 'pics'
            ensure_dir(self.path)

        super().__init__(env_params, sim_params, network, simulator)

    @property
    def action_space(self):
        """See class definition."""
        return Discrete(4)

    @property
    def observation_space(self):
        """See class definition."""
        return Box(
            low=-INF,
            high=INF,
            shape=(X_PIXEL * Y_PIXEL * 5 + 3, ),
            dtype=np.float32)

    def _apply_rl_actions(self, rl_chose):
        """See class definition."""
        sorted_rl_ids = [
            veh_id for veh_id in self.sorted_ids
            if veh_id in self.k.vehicle.get_rl_ids()
        ]
        rl_accel = RL_ACCEL[rl_chose]
        rl_actions = np.zeros(len(sorted_rl_ids))
        for i in range(len(sorted_rl_ids)):
            rl_actions[i] = rl_accel
        self.k.vehicle.apply_acceleration(sorted_rl_ids, rl_actions)

    def compute_reward(self, rl_actions, **kwargs):
        """See class definition."""
        fail = kwargs['fail']
        passed = kwargs['passed']
        if fail:
            return self.env_params.additional_params['penalty_collision']
        if passed:
            return self.env_params.additional_params['reward_success']
        penalty_base = self.env_params.additional_params['penalty_step_base']
        return -np.exp(min(self.continuous_low_speed * np.log(penalty_base), 20.0))

    def get_state(self):
        """See class definition."""
        velocity_cos = np.zeros((X_PIXEL, Y_PIXEL))
        velocity_sin = np.zeros((X_PIXEL, Y_PIXEL))
        ttc = np.ones((X_PIXEL, Y_PIXEL))
        velocity_real = np.zeros((X_PIXEL, Y_PIXEL))
        heading_angle = np.zeros((X_PIXEL, Y_PIXEL))
        global_ttc = 1.0
        len_rl_ids = len(self.k.vehicle.get_rl_ids())
        ori_rl = (0., 0., 0.)
        speed_rl = 0
        if len_rl_ids == 0:
            pass
        elif len_rl_ids >= 2:
            raise ValueError(
                "expect no more than 1 rl vehicle but found {0}",
                len_rl_ids
            )
        else: # len_rl_ids == 1
            rl_id = self.k.vehicle.get_rl_ids()[0]
            ori_rl = self.k.vehicle.get_orientation(rl_id)
            speed_rl = self.k.vehicle.get_speed(rl_id)
            if speed_rl < self.env_params.additional_params['low_speed_threshold']:
                self.continuous_low_speed += 1
            else:
                self.continuous_low_speed = 0
            for veh_id in self.k.vehicle.get_ids():
                if veh_id != rl_id:
                    ori_veh = self.k.vehicle.get_orientation(veh_id)
                    speed_veh = self.k.vehicle.get_speed(veh_id)
                    x_diff = int(np.floor((ori_veh[0] - ori_rl[0] + 1.20) / X_OBSERVE_METER * X_PIXEL + X_PIXEL / 2))
                    y_diff = int(np.floor((ori_veh[1] - ori_rl[1] + 1.20) / Y_OBSERVE_METER * Y_PIXEL))
                    if x_diff < 0 or x_diff >= X_PIXEL or y_diff < 0 or y_diff >= Y_PIXEL:
                        continue
                    velocity = speed_veh / self.k.network.max_speed()
                    angle = ori_veh[2] / 180.0 * np.pi
                    velocity_real[x_diff, y_diff] = max(velocity_real[x_diff, y_diff], velocity)
                    velocity_cos[x_diff, y_diff] = velocity * np.cos(angle)
                    velocity_sin[x_diff, y_diff] = velocity * np.sin(angle)
                    heading_angle[x_diff, y_diff] = ori_veh[2] / 360.0
                    calc_ttc = min(car_ttc(ori_rl, ori_veh, speed_rl, speed_veh), 20) / 20
                    ttc[x_diff, y_diff] = min(ttc[x_diff, y_diff], calc_ttc)
                    global_ttc = min(global_ttc, calc_ttc)
        velocity_cos = np.reshape(velocity_cos, (X_PIXEL, Y_PIXEL, 1))
        velocity_sin = np.reshape(velocity_sin, (X_PIXEL, Y_PIXEL, 1))
        velocity_real = np.reshape(velocity_real, (X_PIXEL, Y_PIXEL, 1))
        heading_angle = np.reshape(heading_angle, (X_PIXEL, Y_PIXEL, 1))
        ttc = np.reshape(ttc, (X_PIXEL, Y_PIXEL, 1))
        ret = np.concatenate([velocity_cos, velocity_sin, velocity_real, heading_angle, ttc], axis=2)
        ret = np.reshape(ret, (X_PIXEL * Y_PIXEL * 5, ))
        velocity = speed_rl / self.k.network.max_speed()
        angle = ori_rl[2] / 180.0 * np.pi
        ret = np.append(ret, velocity * np.cos(angle))
        ret = np.append(ret, velocity * np.sin(angle))
        ret = np.append(ret, global_ttc)
        return ret

    def additional_command(self):
        """See parent class.

        Define which vehicles are observed for visualization purposes, and
        update the sorting of vehicles using the self.sorted_ids variable.
        """
        for veh_id in self.k.vehicle.get_ids():
            if self.k.vehicle.get_type(veh_id) == "av":
                self.k.vehicle.set_color(veh_id, color=(255, 0, 0))

        # update the "absolute_position" variable
        for veh_id in self.k.vehicle.get_ids():
            this_pos = self.k.vehicle.get_x_by_id(veh_id)

            if this_pos == -1001:
                # in case the vehicle isn't in the network
                self.absolute_position[veh_id] = -1001
            else:
                change = this_pos - self.prev_pos.get(veh_id, this_pos)
                self.absolute_position[veh_id] = \
                    (self.absolute_position.get(veh_id, this_pos) + change) \
                    % self.k.network.length()
                self.prev_pos[veh_id] = this_pos

    @property
    def sorted_ids(self):
        """Sort the vehicle ids of vehicles in the network by position.

        This environment does this by sorting vehicles by their absolute
        position, defined as their initial position plus distance traveled.

        Returns
        -------
        list of str
            a list of all vehicle IDs sorted by position
        """
        if self.env_params.additional_params['sort_vehicles']:
            return sorted(self.k.vehicle.get_ids(), key=self._get_abs_position)
        else:
            return self.k.vehicle.get_ids()

    def _get_abs_position(self, veh_id):
        """Return the absolute position of a vehicle."""
        return self.absolute_position.get(veh_id, -1001)

    def step(self, rl_actions):
        """Advance the environment by one step. """
        crash = False
        passed = False
        for _ in range(self.env_params.sims_per_step):
            self.time_counter += 1
            self.step_counter += 1

            # perform acceleration actions for controlled human-driven vehicles
            if len(self.k.vehicle.get_controlled_ids()) > 0:
                accel = []
                for veh_id in self.k.vehicle.get_controlled_ids():
                    action = self.k.vehicle.get_acc_controller(
                        veh_id).get_action(self)
                    accel.append(action)
                self.k.vehicle.apply_acceleration(
                    self.k.vehicle.get_controlled_ids(), accel)

            # perform lane change actions for controlled human-driven vehicles
            if len(self.k.vehicle.get_controlled_lc_ids()) > 0:
                direction = []
                for veh_id in self.k.vehicle.get_controlled_lc_ids():
                    target_lane = self.k.vehicle.get_lane_changing_controller(
                        veh_id).get_action(self)
                    direction.append(target_lane)
                self.k.vehicle.apply_lane_change(
                    self.k.vehicle.get_controlled_lc_ids(),
                    direction=direction)

            # perform (optionally) routing actions for all vehicles in the
            # network, including RL and SUMO-controlled vehicles
            routing_ids = []
            routing_actions = []
            for veh_id in self.k.vehicle.get_ids():
                if self.k.vehicle.get_routing_controller(veh_id) \
                        is not None:
                    routing_ids.append(veh_id)
                    route_contr = self.k.vehicle.get_routing_controller(
                        veh_id)
                    routing_actions.append(route_contr.choose_route(self))

            self.k.vehicle.choose_routes(routing_ids, routing_actions)

            self.apply_rl_actions(rl_actions)

            self.additional_command()

            # advance the simulation in the simulator by one step
            self.k.simulation.simulation_step()

            # store new observations in the vehicles and traffic lights class
            self.k.update(reset=False)

            # update the colors of vehicles
            if self.sim_params.render:
                self.k.vehicle.update_vehicle_colors()

            # crash encodes whether the simulator experienced a collision
            crash = self.k.simulation.check_collision()

            # stop collecting new simulation steps if there is a collision
            if crash:
                break

            # render a frame
            self.render()

        states = self.get_state()

        # collect information of the state of the network based on the
        # environment class used
        self.state = np.asarray(states).T

        # collect observation new state associated with action
        next_observation = np.copy(states)

        # test if the environment should terminate due to a collision or the
        # time horizon being met
        done = (self.time_counter >= self.env_params.warmup_steps +
                self.env_params.horizon)  # or crash

        count_av = 0
        for i in self.k.vehicle.get_ids():
            if self.k.vehicle.get_type(i) == "av":
                count_av += 1
        if self.step_counter >= self.env_params.warmup_steps + 10 and count_av == 0:
            passed = True
            done = True    # No Reinforcement Learning Vehicles, stop

        # compute the info for each agent
        infos = {}

        # compute the reward
        if self.env_params.clip_actions:
            rl_clipped = self.clip_actions(rl_actions)
            reward = self.compute_reward(rl_clipped, fail=crash, passed=passed)
        else:
            reward = self.compute_reward(rl_actions, fail=crash, passed=passed)

        return next_observation, reward, done, infos

    def reset(self):
        """See parent class.

        This also includes updating the initial absolute position and previous
        position.
        """
        obs = super().reset()

        self.continuous_low_speed = 0
        for veh_id in self.k.vehicle.get_ids():
            self.absolute_position[veh_id] = self.k.vehicle.get_x_by_id(veh_id)
            self.prev_pos[veh_id] = self.k.vehicle.get_x_by_id(veh_id)

        return obs
