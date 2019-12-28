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
            'R': (0, 1),
            'D': (1, 0),
            'U': (-1, 0),
            'L': (0, -1)
        }
        self.map_dict = {}
        self.heroes = {}
        row_num = len(initial_map)
        col_num = len(initial_map[0])
        for row in range(row_num):
            self.map_dict[(row+1, 0)], self.map_dict[(row+1, col_num+1)] = TileKB(20), TileKB(20)  # making vertical walls
            for col in range(col_num):
                entity = initial_map[row][col]
                self.map_dict[(row+1, col+1)] = TileKB(entity)
                if 11 <= entity <= 14:
                    self.heroes[entity] = (row+1, col+1)
                    self.last_direction[entity] = None
        for col in range(col_num+2):
            self.map_dict[(0, col)], self.map_dict[(row_num+1, col)] = TileKB(20), TileKB(20)  # horizontal walls
        # Timeout: 60 seconds

    def should_i_shoot(self, curr_tile, direction):  # curr_tile is tuple of coordinates, direction is 'L'/'R'/'U'/'D'
        if direction in self.map_dict[curr_tile].shot_to_dir:
            return False
        dir_tup = self.directions[direction]
        if self.map_dict[t_add(dir_tup, curr_tile)].WALL or self.map_dict[t_add(dir_tup, curr_tile)].SAFE:
            return False
        return True

    def is_ok_move(self, curr_tile, direction):  # just checking if safe&not been at
        dir_tup = self.directions[direction]
        if self.map_dict[t_add(dir_tup, curr_tile)].WALL:
            return False
        if self.map_dict[t_add(dir_tup, curr_tile)].SAFE and self.map_dict[t_add(dir_tup, curr_tile)].been_at == 0:
            #print(f"location is {t_add(dir_tup, curr_tile)}")
            return True
        return False

    #  TODO : if stench - > shoot if didn't shoot already, if coor+dir != (WALL OR SAFE)  - Done
    #  more TODO: update SAFE tiles for heroes with no observations
    #  TODO glitter+SAFE+been_at ==0 => GO! (after checking if tile.GOLD == True)
    #  TODO don't step on other heroes!
    #  TODO before moving mark tile as safe and not only been_at += 1
    def get_next_action(self, partial_map, observations):
        print(self.heroes)  # TODO -DELETE
        print(observations)
        # ---------- choosing hero to go with ---------- #

        if self.last_action is None:
            curr_hero = random.choice(list(self.heroes.keys()))
        else:
            curr_hero = self.last_action[1]
            curr_hero_coor = self.heroes[curr_hero]
            if partial_map[curr_hero_coor[0]-1][curr_hero_coor[1]-1] != curr_hero:  # means the hero from last move is dead
                self.heroes.pop(curr_hero)
                if len(self.heroes) == 0:
                    return 'move', 11, 'R'  # we're dead anyway
                curr_hero = random.choice(list(self.heroes))  # already checked that it's not empty
        curr_hero_coor = self.heroes[curr_hero]

        # ----- looking at observations, updating KB accordingly after shooting if there's stench ----- #

        heroes_with_obs = []  # to know later which heroes had no observation, to mark the tiles next to him as SAFE
        for observation in observations:  # updating our KB
            coordinate = observation[0]
            obs = observation[1]
            hero = partial_map[coordinate[0]-1][coordinate[1]-1]
            if obs != 'glitter':
                heroes_with_obs.append(hero)
            if obs == 'stench':
                for direction in self.directions.keys():
                    if self.should_i_shoot(coordinate, direction):
                        self.map_dict[coordinate].shot_to_dir.append(direction)  # making sure not to shoot twice from same tile to same direction
                        print(f"i did {('shoot', hero, direction)}")
                        self.last_action = ('shoot', hero, direction)
                        return 'shoot', hero, direction
            for direction in self.directions:   # don't have to update if I shot something, because we'll stay at the same place
                self.map_dict[t_add(coordinate, self.directions[direction])].update_after_obs(opposite_direction(direction), obs)

        for hero in self.heroes:  # updating tiles near heroes with no observations as safe (no breeze, no stench means safe)
            if hero not in heroes_with_obs:
                for direction in self.directions:
                    self.map_dict[t_add(self.heroes[hero], self.directions[direction])].SAFE = True

        # ---------- Actual movement heuristic ---------- #

        for direction in self.directions:
            if self.is_ok_move(curr_hero_coor, direction):
                action = 'move', curr_hero, direction
                self.last_action = action
                self.map_dict[curr_hero_coor].been_at += 1
                # print(f"location = {curr_hero_coor} and been_at ={self.map_dict[curr_hero_coor].been_at}")
                self.map_dict[curr_hero_coor].SAFE = True
                self.heroes[curr_hero] = t_add(self.directions[direction], curr_hero_coor)
                print(f"i did {action}")
                return action
        # self.prev_map = partial_map   - probably don't need
        # --------- Going random direction --------- #
        for direction in self.directions:
            if self.map_dict[t_add(self.directions[direction], curr_hero_coor)].WALL:
                continue
            self.heroes[curr_hero] = t_add(curr_hero_coor, self.directions[direction])
            print(f"i did {('move', curr_hero, direction)} by default")
            self.map_dict[curr_hero_coor].been_at += 1
            self.last_action = 'move', curr_hero, direction
            return 'move', curr_hero, direction  # just default to see how it runs

        # TODO: before returning next, let's update been_at for the KBs and "came_from"
        # Timeout: 5 seconds









