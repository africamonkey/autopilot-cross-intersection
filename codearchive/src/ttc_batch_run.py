import os
import time
import argparse
import xml_analyzer
from ttc_single_journey import cross_road_experiment, load_random_state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="TTC Batch Run")
    parser.add_argument('--delete_all_xml', '-a', help="delete all xml", default=False)
    parser.add_argument('--delete_uncollision_xml', '-u', help="delete uncollision xml", default=False)
    parser.add_argument('--max_log', '-m', help="max log", default=2147483647)
    args = parser.parse_args()

    location_file = './emission/fail_runs'
    collisions = 0
    successes = 0
    sum_brake_time = 0
    sum_duration = 0
    success_log = 0
    for task in range(1000):
        exp = cross_road_experiment(render=False)
        emission_location = os.path.join(exp.env.sim_params.emission_path, exp.env.network.name)
        print('Task #{0}, emission location {1}'
              .format(task + 1, emission_location), flush=True)
        random_state = load_random_state()
        with open(emission_location + '-seed', "w") as seed_file:
            seed_file.write(random_state.__str__())
        exp.run(1, 600)
        retry = 0
        time_to_retry = 0.1
        while True:
            try:
                has_collision = xml_analyzer.has_collision(emission_location + '-summary.xml')
                duration = xml_analyzer.get_duration(emission_location + '-tripinfo.xml')
                is_success = duration is not None
                brake_time = xml_analyzer.avg_brake_time(emission_location + '-emission.xml')
            except Exception as e:
                time.sleep(time_to_retry)
                retry += 1
                print('parse error, retry {0}'.format(retry), flush=True)
                time_to_retry *= 2
                if retry > 10:
                    raise e
                continue
            break
        if has_collision:
            is_success = False
            collisions += 1
            with open(location_file, 'a') as f:
                f.write(emission_location)
                f.write('\n')
        if is_success:
            successes += 1
            sum_brake_time += brake_time
            sum_duration += duration
        try:
            if args.delete_all_xml or \
                    (args.delete_uncollision_xml and not has_collision) or \
                    (success_log >= int(args.max_log)):
                os.remove(emission_location + '-summary.xml')
                os.remove(emission_location + '-tripinfo.xml')
                os.remove(emission_location + '-emission.xml')
                os.remove(emission_location + '-seed')
            else:
                success_log += 1
        except Exception:
            pass

        print('Task #{0}, success rate {1}%, collision rate {2}%, avg duration {3}, avg brake time {4}'
              .format(task + 1,
                      successes * 100.0 / (task + 1),
                      collisions * 100.0 / (task + 1),
                      "NAN" if successes == 0 else sum_duration / successes,
                      "NAN" if successes == 0 else sum_brake_time / successes), flush=True)
