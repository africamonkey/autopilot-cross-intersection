try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


BRAKE_DECEL = 4.0


def has_collision(summary_path):
    tree = ET.ElementTree(file=summary_path)
    root = tree.getroot()
    collisions = 0
    for step in root:
        collisions += int(step.attrib['collisions'])
    return collisions > 0


def avg_brake_time(emission_path):
    tree = ET.ElementTree(file=emission_path)
    root = tree.getroot()
    step = 0.1
    last_speed = {}
    brake_time = 0
    for timestamp in root:
        for vehicle in timestamp:
            id = vehicle.attrib['id']
            if len(id) > 7 and id[0:7] == 'SN_flow':
                continue
            speed = float(vehicle.attrib['speed'])
            last = last_speed.get(id, 0)
            if speed < last - BRAKE_DECEL * step:
                brake_time += step
            last_speed[id] = speed
    if len(last_speed):
        brake_time /= len(last_speed)
    else:
        brake_time = 0
    return brake_time


def get_duration(tripinfo_path):
    tree = ET.ElementTree(file=tripinfo_path)
    root = tree.getroot()
    for tripinfo in root:
        id = tripinfo.attrib['id']
        duration = float(tripinfo.attrib['duration'])
        if len(id) > 7 and id[0:7] == 'SN_flow':
            return duration
    return None
