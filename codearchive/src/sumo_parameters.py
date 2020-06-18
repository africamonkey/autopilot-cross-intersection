from flow.core.params import VehicleParams, InFlows, SumoCarFollowingParams
from flow.core.params import InitialConfig, NetParams
from flow.controllers import DieController, IDMController
from flow.controllers.routing_controllers import RandomRouter


def get_inflows(inflow_probability):
    inflows = InFlows()
    inflows.add(
        veh_type="human",
        edge="W2M",
        probability=inflow_probability,
        depart_lane="free",
        depart_speed="max",
        name="WE_flow"
    )
    inflows.add(
        veh_type="human",
        edge="E2M",
        probability=inflow_probability,
        depart_lane="free",
        depart_speed="max",
        name="EW_flow"
    )
    inflows.add(
        veh_type="av",
        edge="SS2M",
        period=1,
        depart_lane="free",
        depart_speed="0",
        name="SN_flow",
        begin=15,
        number=1
    )
    return inflows


def get_net_params(inflow_probability):
    net_params = NetParams(
        inflows=get_inflows(inflow_probability),
        additional_params={
            "length": 200,
            "cross_length": 13,
            "start_length": 11,
            "num_lanes": 1,
            "speed_limit": 20,
        }
    )
    return net_params


def get_initial_config():
    initial_config = InitialConfig()
    return initial_config


def get_car_following_params():
    car_following_params = SumoCarFollowingParams(speed_mode='no_collide')
    return car_following_params


def get_vehicle_params(av_acc_controller, av_acc_controller_params, training=False):
    vehicles = VehicleParams()
    if training:
        vehicles.add(
            veh_id="human",
            acceleration_controller=(DieController, {}),
            car_following_params=get_car_following_params(),
        )
    else:
        vehicles.add(
            veh_id="human",
            acceleration_controller=(IDMController, {}),
            car_following_params=get_car_following_params(),
        )
    vehicles.add(
        veh_id="av",
        acceleration_controller=(av_acc_controller, av_acc_controller_params),
        routing_controller=(RandomRouter, {}),
        car_following_params=get_car_following_params(),
    )
    return vehicles

