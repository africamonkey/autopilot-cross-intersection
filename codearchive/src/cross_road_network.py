"""Cross Road Network"""
from flow.networks import Network


class CrossRoadNetwork(Network):

    def specify_nodes(self, net_params):
        length = net_params.additional_params["length"]
        cross_length = net_params.additional_params["cross_length"]
        start_length = net_params.additional_params["start_length"]
        nodes = [
            {"id": "S", "x": 0, "y": -length},         # South
            {"id": "SS", "x": 0, "y": -start_length},  # South
            {"id": "E", "x": length, "y": 0},          # East
            {"id": "EE", "x": cross_length, "y": 0},   # East
            {"id": "N", "x": 0, "y": length},          # North
            {"id": "NN", "x": 0, "y": cross_length},   # North
            {"id": "W", "x": -length, "y": 0},         # West
            {"id": "WW", "x": -cross_length, "y": 0},  # West
            {"id": "M", "x": 0, "y": 0},               # Middle
        ]
        return nodes

    def specify_edges(self, net_params):
        length = net_params.additional_params["length"]
        cross_length = net_params.additional_params["cross_length"]
        start_length = net_params.additional_params["start_length"]
        lanes = net_params.additional_params["num_lanes"]
        speed_limit = net_params.additional_params["speed_limit"]

        edges = [
            {"id": "W2M", "numLanes": lanes, "speed": speed_limit, "from": "W", "to": "M", "length": length, "priority": 46},
            {"id": "E2M", "numLanes": lanes, "speed": speed_limit, "from": "E", "to": "M", "length": length, "priority": 46},
            {"id": "N2M", "numLanes": lanes, "speed": speed_limit, "from": "N", "to": "M", "length": length, "priority": 23},
            {"id": "S2SS", "numLanes": lanes, "speed": speed_limit, "from": "S", "to": "SS", "length": length - start_length, "priority": 23},
            {"id": "SS2M", "numLanes": lanes, "speed": speed_limit, "from": "SS", "to": "M", "length": start_length, "priority": 23},
            {"id": "M2WW", "numLanes": lanes, "speed": speed_limit, "from": "M", "to": "WW", "length": cross_length, "priority": 46},
            {"id": "WW2W", "numLanes": lanes, "speed": speed_limit, "from": "WW", "to": "W", "length": length - cross_length, "priority": 46},
            {"id": "M2EE", "numLanes": lanes, "speed": speed_limit, "from": "M", "to": "EE", "length": cross_length, "priority": 46},
            {"id": "EE2E", "numLanes": lanes, "speed": speed_limit, "from": "EE", "to": "E", "length": length - cross_length, "priority": 46},
            {"id": "M2NN", "numLanes": lanes, "speed": speed_limit, "from": "M", "to": "NN", "length": cross_length, "priority": 46},
            {"id": "NN2N", "numLanes": lanes, "speed": speed_limit, "from": "NN", "to": "N", "length": length - cross_length, "priority": 46},
            {"id": "M2S", "numLanes": lanes, "speed": speed_limit, "from": "M", "to": "S", "length": length, "priority": 46},
        ]
        return edges

    def specify_routes(self, net_params):
        rts = {
            "W2M": [
                (["W2M", "M2EE", "EE2E"], 1.0),
            ],
            "E2M": [
                (["E2M", "M2WW", "WW2W"], 1.0),
            ],
            "SS2M": [
                (["SS2M", "M2NN"], 1.0),   # Foward
                # (["SS2M", "M2WW"], 1.0), # Left
                # (["SS2M", "M2EE"], 1.0), # Right
            ],
        }
        return rts
