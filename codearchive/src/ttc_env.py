"""Environment for training the acceleration behavior of vehicles in a ring."""

from flow.core import rewards
from flow.envs.base import Env

from gym.spaces.box import Box

import numpy as np

ADDITIONAL_ENV_PARAMS = {
    'max_accel': 2.5,
    'max_decel': 4.5,
    'target_velocity': 10,
    'sort_vehicles': False
}


class CrossRoadAccelEnv(Env):

    def __init__(self, env_params, sim_params, network, simulator='traci'):
        for p in ADDITIONAL_ENV_PARAMS.keys():
            if p not in env_params.additional_params:
                raise KeyError(
                    'Environment parameter \'{}\' not supplied'.format(p))

        self.prev_pos = dict()
        self.absolute_position = dict()

        super().__init__(env_params, sim_params, network, simulator)

    @property
    def action_space(self):
        """See class definition."""
        return Box(
            low=-abs(self.env_params.additional_params['max_decel']),
            high=self.env_params.additional_params['max_accel'],
            shape=(self.initial_vehicles.num_rl_vehicles, ),
            dtype=np.float32)

    @property
    def observation_space(self):
        """See class definition."""
        self.obs_var_labels = ['Velocity', 'Absolute_pos']
        return Box(
            low=0,
            high=1,
            shape=(2 * self.initial_vehicles.num_vehicles, ),
            dtype=np.float32)

    def _apply_rl_actions(self, rl_actions):
        """See class definition."""
        sorted_rl_ids = [
            veh_id for veh_id in self.sorted_ids
            if veh_id in self.k.vehicle.get_rl_ids()
        ]
        self.k.vehicle.apply_acceleration(sorted_rl_ids, rl_actions)

    def compute_reward(self, rl_actions, **kwargs):
        """See class definition."""
        if self.env_params.evaluate:
            return np.mean(self.k.vehicle.get_speed(self.k.vehicle.get_ids()))
        else:
            return rewards.desired_velocity(self, fail=kwargs['fail'])

    def get_state(self):
        """See class definition."""
        speed = [self.k.vehicle.get_speed(veh_id) / self.k.network.max_speed()
                 for veh_id in self.sorted_ids]
        pos = [self.k.vehicle.get_x_by_id(veh_id) / self.k.network.length()
               for veh_id in self.sorted_ids]

        return np.array(speed + pos)

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
            done = True    # No Reinforcement Learning Vehicles, stop

        # compute the info for each agent
        infos = {}

        # compute the reward
        if self.env_params.clip_actions:
            rl_clipped = self.clip_actions(rl_actions)
            reward = self.compute_reward(rl_clipped, fail=crash)
        else:
            reward = self.compute_reward(rl_actions, fail=crash)

        return next_observation, reward, done, infos

    def reset(self):
        """See parent class.

        This also includes updating the initial absolute position and previous
        position.
        """
        obs = super().reset()

        for veh_id in self.k.vehicle.get_ids():
            self.absolute_position[veh_id] = self.k.vehicle.get_x_by_id(veh_id)
            self.prev_pos[veh_id] = self.k.vehicle.get_x_by_id(veh_id)

        return obs
