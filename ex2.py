from collections import defaultdict
import random

ids = ["323263442", "312485816"]  # CHECKING


def opposite_direction(some_direction):
    return {'L': 'R', 'R': 'L', 'U': 'D', 'D': 'U', 'LL': 'RR', 'RR': 'LL', 'UU': 'DD', 'DD': 'UU'}.get(some_direction)


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
        self.breeze_around = 0
        self.stench_around = 0
        if 11 <= initial_type <= 14:
            self.SAFE = True
        if initial_type == 20:
            self.WALL = True

    def update_after_obs(self, obs_from_dir, obs):
        if self.WALL:
            return
        if obs == 'breeze':
            self.KB_dict['B'+obs_from_dir] = True
            self.breeze_around = 0
            for direction in ['U', 'D', 'L', 'R']:
                if self.KB_dict['B'+direction]:
                    self.breeze_around += 1
        elif obs == 'stench':
            self.KB_dict['S'+obs_from_dir] = True
            self.stench_around = 0
            for direction in ['U', 'D', 'L', 'R']:
                if self.KB_dict['S'+direction]:
                    self.stench_around += 1
        elif obs == 'glitter':
            self.KB_dict['G'+obs_from_dir] = True
            if self.KB_dict['G'+opposite_direction(obs_from_dir)]:  # I assume ['glitter', 'tile', 'glitter'] => gold in the tile
                self.GOLD = True
        else:
            print('got undefined observation for some reason')
            return


class WumpusController:
    def __init__(self, initial_map, initial_observations):
        #print(initial_map)
        self.row_num = len(initial_map)+2  # including walls
        self.col_num = len(initial_map[0])+2
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
        self.can_risk = True if len(self.heroes) > 1 else False

        # Timeout: 60 seconds

    def is_in_map(self, coordinates_tuple):
        if coordinates_tuple[0] <= 0 or coordinates_tuple[0] >= self.row_num-1:
            return False
        if coordinates_tuple[1] <= 0 or coordinates_tuple[1] >= self.col_num-1:
            return False
        return True

    def should_i_shoot(self, curr_tile, direction, partial_map):  # curr_tile is tuple of coordinates, direction is 'L'/'R'/'U'/'D'
        if direction in self.map_dict[curr_tile].shot_to_dir:
            return False
        dir_tup = self.directions[direction]
        destination = t_add(dir_tup, curr_tile)
        if self.map_dict[destination].WALL or self.map_dict[destination].SAFE:
            return False
        destination = t_add(destination, dir_tup)
        while not self.map_dict[destination].WALL:
            if 11 <= partial_map[destination[0]-1][destination[1]-1] <= 14:
                return False
            destination = t_add(destination, dir_tup)
        return True

    def is_ok_move(self, curr_tile, direction, partial_map, max_breeze, max_been_at):  # just checking if safe&not been at&not wall
        dir_tup = self.directions[direction]
        destination = t_add(dir_tup, curr_tile)
        destination_KB = self.map_dict[destination]
        if not self.is_in_map(destination) :
            return False
        if destination_KB.WALL or (11 <= partial_map[destination[0]-1][destination[1]-1] <= 14):
            return False
        if destination_KB.been_at <= max_been_at and destination_KB.breeze_around <= max_breeze:
            return True
        return False

    def update_after_move(self, action):
        hero, direction = action[1], action[2]
        hero_coor = self.heroes[hero]
        destination = t_add(hero_coor, self.directions[direction])
        self.heroes[hero] = destination
        self.last_action = action
        self.map_dict[hero_coor].been_at += 1
        self.map_dict[destination].SAFE = True
        #print(f"i did {action} from {hero_coor} to {destination}")
        return

    def glitter_procedure(self, hero, coordinates, partial_map):
        for direction in self.directions:
            action = 'move', hero, direction
            if self.is_ok_move(coordinates, direction, partial_map, 0, 0):
                return action
        for direction in self.directions:  # lowering standards to unsafe tiles
            action = 'move', hero, direction
            destination = t_add(coordinates, self.directions[direction])
            destination_KB = self.map_dict[destination]
            if destination_KB.been_at == 0 and not(destination_KB.WALL or (11 <= partial_map[destination[0]-1][destination[1]-1] <= 14)):
                return action
        return 'no_action'

    # TODO: if stench - > shoot if didn't shoot already, if coor+dir != (WALL OR SAFE)  - Done
    # TODO: update SAFE tiles for heroes with no observations - Done
    # TODO: glitter+SAFE+been_at ==0 => GO! (after checking if tile.GOLD == True)
    # TODO: don't step on other heroes! - Done
    # TODO: before moving mark tile as safe and not only been_at += 1 - Need to remember&verify for each heuristic
    # TODO: do something like "self.not_afraid_of_monsters = True" depending on # of heroes left
    # TODO: do something like breeze and died => map_dict[tile_coordinates].PIT=True
    # TODO: add conclusions for observations also with 2-Manhattan-Distance tiles
    # TODO: add moves based on "probably pit"
    def get_next_action(self, partial_map, observations):
        # print(observations)
        # ---------- choosing hero to go with ---------- #
        if self.last_action is None:
            curr_hero = random.choice(list(self.heroes.keys()))
        else:
            curr_hero = self.last_action[1]
            curr_hero_coor = self.heroes[curr_hero]
            if partial_map[curr_hero_coor[0]-1][curr_hero_coor[1]-1] != curr_hero:  # means the hero from last move is dead
                #print(f"hero {curr_hero} died and situation is: {self.heroes}, map:\n {partial_map}")
                self.heroes.pop(curr_hero)
                if len(self.heroes) == 0:
                    print("i recon that game over")
                    return 'move', 11, 'R'  # we're dead anyway
                elif len(self.heroes) <= 1:
                    self.can_risk = False
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
            else:
                print("spotted glitter")
                glitter_action = self.glitter_procedure(hero, coordinate, partial_map)
                if glitter_action != 'no_action':
                    self.update_after_move(glitter_action)
                    print(f"did {glitter_action} as glitter action")
                    return glitter_action
            if obs == 'stench':
                for direction in self.directions.keys():
                    if self.should_i_shoot(coordinate, direction, partial_map):
                        self.map_dict[coordinate].shot_to_dir.append(direction)  # making sure not to shoot twice from same tile to same direction
                        #print(f"i did {('shoot', hero, direction)}")
                        self.last_action = ('shoot', hero, direction)
                        return 'shoot', hero, direction
            for direction in self.directions:   # don't have to update if I shot something, because we'll stay at the same place
                next_to_tile = t_add(coordinate, self.directions[direction])
                self.map_dict[next_to_tile].update_after_obs(opposite_direction(direction), obs)
                next_next_to_tile = t_add(next_to_tile, self.directions[direction])  # want to update tile with dist of 2 also
                if self.is_in_map(next_next_to_tile):
                    self.map_dict[next_next_to_tile].update_after_obs(2*opposite_direction(direction), obs)

        for hero in self.heroes:  # updating tiles near heroes with no observations as safe (no breeze, no stench means safe)
            if hero not in heroes_with_obs:
                for direction in self.directions:
                    destination = t_add(self.heroes[hero], self.directions[direction])
                    self.map_dict[destination].SAFE = True

        # ---------- Actual movement heuristic ---------- #
        shuffled_directions = random.sample(list(self.directions.keys()), 4)

        # --------------- 1st priority action(safe&unexplored) --------------- #

        for direction in shuffled_directions:
            potential_action = 'move', curr_hero, direction
            if self.is_ok_move(curr_hero_coor, direction, partial_map, 0, 0):
                self.update_after_move(potential_action)
                #print("chose from safe&not been at")
                return potential_action

        # --------------- 2nd priority action(safe&explored,same hero) --------------- #

        for direction in shuffled_directions:
            potential_action = 'move', curr_hero, direction
            if self.is_ok_move(curr_hero_coor, direction, partial_map, 0, 1):
                self.update_after_move(potential_action)
                #print("chose from safe&not been at")
                return potential_action

        # --------------- 3rd priority action(suicidal if there's more than one hero left) --------------- #

        if self.can_risk:
            min_risk = 1000  # random big num
            chosen_action = 'no_action'
            for direction in shuffled_directions:
                destination = t_add(curr_hero_coor, self.directions[direction])
                destination_KB = self.map_dict[destination]
                curr_risk = destination_KB.breeze_around+destination_KB.stench_around
                if curr_risk < min_risk and not (destination_KB.WALL or 11 <= partial_map[destination[0]-1][destination[1]-1] <= 14):
                    min_risk = curr_risk
                    chosen_action = 'move', curr_hero, direction
            if chosen_action != 'no_action':
                self.update_after_move(chosen_action)
                return chosen_action

        # --------- Going random direction, avoiding possible pits --------- #

        for max_breeze in range(1, 5):
            for curr_hero in self.heroes.keys():
                curr_hero_coor = self.heroes[curr_hero]
                for direction in shuffled_directions:
                    curr_destination = t_add(self.directions[direction], curr_hero_coor)
                    if self.map_dict[curr_destination].WALL or (11 <= partial_map[curr_destination[0]-1][curr_destination[1]-1] <= 14)\
                            or self.map_dict[curr_destination].breeze_around >= max_breeze or self.map_dict[curr_destination].been_at >= 3:
                        continue
                    action = 'move', curr_hero, direction
                    self.update_after_move(action)
                    #print(f"max breeze is {max_breeze}")
                    return action  # just default to see how it runs

        # in case no action chosen:
        for direction in shuffled_directions:
            curr_destination = t_add(self.directions[direction], curr_hero_coor)
            if self.map_dict[curr_destination].WALL or (11 <= partial_map[curr_destination[0] - 1][curr_destination[1] - 1] <= 14) \
                    or self.map_dict[curr_destination].breeze_around >= 5 or self.map_dict[curr_destination].been_at >= 4:
                continue
            action = 'move', curr_hero, direction
            self.update_after_move(action)
            return action  # just default to see how it runs
        # TODO: before returning next, let's update been_at for the KBs and "came_from"
        # Timeout: 5 seconds
