import random
from ast import literal_eval


def load_random_state(seed_file=None):
    if not seed_file:
        return random.getstate()
    with open(seed_file) as f:
        s = f.readline()
        random_state_saved = literal_eval(s)
        random.setstate(random_state_saved)
    return random_state_saved
