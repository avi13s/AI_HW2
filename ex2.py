from collections import defaultdict
import random

ids = ["323263442", "312485816"]


def opposite_direction(some_direction):
    return {'L': 'R', 'R': 'L', 'U': 'D', 'D': 'U'}.get(some_direction)


def t_add(tup1, tup2):
    return tup1[0]+tup2[0], tup1[1]+tup2[1]


class TileKB:
    def __init__(self, initial_type):
        self.KB_dict = defaultdict(lambda: False)
        self.been_at = 0
        self.WALL = False
        self.GOLD = False
        if 11 <= initial_type <= 14:
            self.SAFE = True
        if initial_type == 20:
            self.WALL = True

    def update_after_obs(self, obs_from_dir, obs):
        if self.WALL:
            return
        if obs == 'breeze':
            self.KB_dict['B'+obs_from_dir] = True
            if self.KB_dict['B'+opposite_direction(obs_from_dir)]:
                self.KB_dict['P_PIT'] = True
        elif obs == 'stench':
            self.KB_dict['S'+obs_from_dir] = True
        elif obs == 'glitter':
            self.KB_dict['G'+obs_from_dir] = True
            if self.KB_dict['G'+opposite_direction(obs_from_dir)]:  # I assume ['glitter', 'tile', 'glitter'] => gold in the tile
                self.GOLD = True
        else:
            print('got undefined observation for some reason')
            return


class WumpusController:
    def __init__(self, initial_map, initial_observations):
        self.prev_map = None
        self.prev_obs = None
        self.last_action = None
        self.directions = {
            'U': (-1, 0),
            'D': (1, 0),
            'R': (0, 1),
            'L': (0, -1)
        }
        self.map_dict = {}
        self.heroes = {}
        row_num = len(initial_map)
        col_num = len(initial_map[0])
        for row in range(row_num):
            self.map_dict[(row, 0)], self.map_dict[(row, col_num)] = TileKB(20), TileKB(20)  # making vertical walls
            for col in range(col_num):
                entity = initial_map[row][col]
                self.map_dict[(row+1, col+1)] = TileKB(entity)
                if 11 <= entity <= 14:
                    self.heroes[entity] = (row+1, col+1)
        for col in range(col_num+2):
            self.map_dict[(0, col)], self.map_dict[(row_num+1, col)] = TileKB(20), TileKB(20)  # horizontal walls

        # Timeout: 60 seconds

    def get_next_action(self, partial_map, observations):
        # TODO if hero died, update it
        if self.last_action is None:
            curr_hero = random.choice(self.heroes.keys())
        else:
            curr_hero = self.last_action[1]
            if partial_map(self.heroes[curr_hero]) != curr_hero:  # means the hero is dead
                self.heroes.pop(curr_hero)
                curr_hero = random.choice(self.heroes.keys())  # I assume it won't be empty cuz game would've stopped
        for observation in observations:
            coordinate = observation[0]
            obs = observation[1]
            for direction in self.directions:
                self.map_dict[t_add(coordinate, self.directions[direction])].update_after_obs(opposite_direction(direction), obs)
        self.prev_map = partial_map
        return 'move', 11, 'R'
        # TODO: before returning next, let's update been_at for the KBs
        # Timeout: 5 seconds









