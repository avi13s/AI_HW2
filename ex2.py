from collections import defaultdict
import random

ids = ["323263442", "312485816"]  # CHECKING


def opposite_direction(some_direction):
    return {'L': 'R', 'R': 'L', 'U': 'D', 'D': 'U'}.get(some_direction)


def t_add(tup1, tup2):
    return tup1[0]+tup2[0], tup1[1]+tup2[1]


class TileKB:
    def __init__(self, initial_type):
        self.KB_dict = defaultdict(lambda: False)
        self.been_at = 0  # counting how much times a hero stepped here, updates after moving
        self.SAFE = False
        self.WALL = False
        self.GOLD = False
        self.shot_to_dir = []
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
        self.last_direction = {}  # maybe useful to know to which direction a hero went last
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
                    self.last_direction[entity] = None
        for col in range(col_num+2):
            self.map_dict[(0, col)], self.map_dict[(row_num+1, col)] = TileKB(20), TileKB(20)  # horizontal walls

        # Timeout: 60 seconds

    def should_i_shoot(self, curr_tile, direction):
        if direction in self.map_dict[curr_tile].shot_to_dir:
            return False
        dir_tup = self.directions[direction]
        if self.map_dict[t_add(dir_tup,curr_tile)].WALL or self.map_dict[t_add(dir_tup,curr_tile)].SAFE:
            return False
        return True

    #  TODO : if stench - > shoot if didn't shoot already, if coor+dir != (WALL OR SAFE)  - Done
    #  more TODO: update SAFE tiles for heroes with no observations
    #  TODO glitter+SAFE+been_at ==0 => GO! (after checking if tile.GOLD == True)
    #  TODO don't step on other heroes!
    def get_next_action(self, partial_map, observations):
        #print(observations)
        if self.last_action is None:
            curr_hero = random.choice(list(self.heroes.keys()))
        else:
            curr_hero = self.last_action[1]
            if partial_map(self.heroes[curr_hero]) != curr_hero:  # means the hero is dead
                self.heroes.pop(curr_hero)
                curr_hero = random.choice(self.heroes.keys())  # I assume it won't be empty cuz game would've stopped
        for observation in observations:  # updating our KB
            coordinate = observation[0]
            obs = observation[1]
            hero = partial_map[coordinate[0]-1][coordinate[1]-1]
            last_dir = self.last_direction[hero]
            if obs == 'stench':
                for direction in self.directions.keys():
                    if opposite_direction(direction) == last_dir:
                        continue
                    else:
                        if self.should_i_shoot(coordinate, direction):
                            self.map_dict[coordinate].shot_to_dir.append(direction)
                            print(f"i did {('shoot', hero, direction)}")
                            return 'shoot', hero, direction
            for direction in self.directions:
                self.map_dict[t_add(coordinate, self.directions[direction])].update_after_obs(opposite_direction(direction), obs)
        #self.prev_map = partial_map   - probably don't need
        self.heroes[curr_hero] = t_add(self.heroes[curr_hero], self.directions['R'])
        print(f"i did {('move', 11, 'R')}")
        return 'move', 11, 'R'  # just default to see how it runs
        # TODO: before returning next, let's update been_at for the KBs and "came_from"
        # Timeout: 5 seconds









