import ex2
import time
import inputs

CODES = {"passage": 10, "hero 1": 11, "hero 2": 12, "hero 3": 13, "hero 4": 14,
         "wall": 20, "pit": 30, "monster": 60, "gold": 70, "target": 75}
INVERSE_CODES = dict([(j, i) for i, j in CODES.items()])
ACTION_TIMEOUT = 5
CONSTRUCTOR_TIMEOUT = 60

class Checker:
    def __init__(self):
        pass

    def check_controller(self):
        pass

    def true_state_to_controller_input(self):
        pass

    def is_action_legal(self, action):
        pass

    def change_state_after_action(self, action):
        pass

    def at_goal(self):
        pass

class WumpusChecker(Checker):
    def __init__(self, input):
        super().__init__()
        self.initial_state = wrap_with_walls(input)
        self.x_dimension = len(self.initial_state)
        self.y_dimension = len(self.initial_state[0])
        self.current_state = state_to_dict(self.initial_state)
        self.turn_limit = 3 * len(input) + 3 * len(input[0]) + 5
        print(f"Maximal amount of turns is {self.turn_limit}!")

    def check_controller(self):
        constructor_start = time.time()
        state_to_controller, observations = self.true_state_to_controller_input()
        controller = ex2.WumpusController(state_to_controller, observations)
        constructor_finish = time.time()
        if constructor_finish - constructor_start > CONSTRUCTOR_TIMEOUT:
            return f"Timeout on constructor! Took {constructor_finish - constructor_start} seconds," \
                   f" should take no more than {CONSTRUCTOR_TIMEOUT}"

        counter = 0
        while not self.at_goal():
            state_to_controller, observations = self.true_state_to_controller_input()
            start = time.time()
            action = controller.get_next_action(state_to_controller, observations)
            finish = time.time()
            if finish-start > ACTION_TIMEOUT:
                return f"Timeout on action! Took {finish - start} seconds, should take no more than {ACTION_TIMEOUT}"
            if not self.is_action_legal(action):
                return f"Action {action} is illegal!"
            counter += 1
            if counter > self.turn_limit:
                return "Turn limit exceeded!"
            self.change_state_after_action(action)
        return f"Goal achieved in {counter} steps!"

    def true_state_to_controller_input(self):
        state_to_return = []
        for i in range(len(self.initial_state)):
            row = []
            for j in range(len(self.initial_state[0])):
                current_object = INVERSE_CODES[self.current_state[(i, j)]]
                if current_object == "pit" or current_object == "monster" or current_object == "gold":
                    row.append(CODES["passage"])
                else:
                    row.append(CODES[current_object])
            state_to_return.append(row)
        state_to_return = [tuple(row[1:-1]) for row in state_to_return[1:-1]]
        observations = self.create_observations()
        return tuple(state_to_return), observations

    def create_observations(self):
        observation_set = set()
        for i in range(len(self.initial_state)):
            for j in range(len(self.initial_state[0])):
                current_object = INVERSE_CODES[self.current_state[(i, j)]]
                if "hero" in current_object:
                    for x in range(i - 2, i + 3):
                        for y in range(j - 2, j + 3):
                            distance = abs(i - x) + abs(j - y)
                            if x < 0 or x > self.x_dimension - 1 or y < 0 or y > self.y_dimension - 1:
                                continue
                            if distance <= 2:
                                if "monster" == INVERSE_CODES[self.current_state[(x, y)]]:
                                    observation_set.add(((i, j), "stench"))
                                if distance == 1:
                                    if "pit" == INVERSE_CODES[self.current_state[(x, y)]]:
                                        observation_set.add(((i, j), "breeze"))
                                    if "gold" == INVERSE_CODES[self.current_state[(x, y)]]:
                                        observation_set.add(((i, j), "glitter"))
        return tuple(observation_set)

    def is_action_legal(self, action):
        if len(action) != 3:
            return False
        name_of_action, hero, direction = action[0], action[1], action[2]
        if not (name_of_action == "shoot" or name_of_action == "move"):
            return False
        if hero not in self.current_state.values():
            return False
        if direction not in ("U", "D", "L", "R"):
            return False
        return True

    def change_state_after_action(self, action):
        if action[0] == "move":
            self.change_state_after_moving(action)
        else:
            self.change_state_after_shooting(action)

    def change_state_after_moving(self, action):
        hero, direction = action[1], action[2]
        current_tile = None
        for i, j in self.current_state.items():
            if j == hero:
                current_tile = i

        if direction == "U":
            next_tile = (current_tile[0] - 1, current_tile[1])
        elif direction == "D":
            next_tile = (current_tile[0] + 1, current_tile[1])
        elif direction == "R":
            next_tile = (current_tile[0], current_tile[1] + 1)
        elif direction == "L":
            next_tile = (current_tile[0], current_tile[1] - 1)

        assert next_tile
        destination_object = INVERSE_CODES[self.current_state[next_tile]]
        if destination_object == "wall" or "hero" in destination_object:
            return

        self.current_state[current_tile] = CODES["passage"]
        if destination_object == "passage":
            self.current_state[next_tile] = hero
            self.monster_correction(next_tile, False)
        elif destination_object == "gold":
            self.current_state[current_tile] = CODES["target"]
            self.monster_correction(next_tile, True)
        return

    def monster_correction(self, tile, gold):
        relevant_locations = (
            (tile[0] - 1, tile[1]),
            (tile[0] + 1, tile[1]),
            (tile[0], tile[1] - 1),
            (tile[0], tile[1] + 1)
        )

        for location in relevant_locations:
            if self.current_state[location] == CODES["monster"]:
                self.current_state[location] = CODES["passage"]
                if gold:
                    self.current_state[tile] = CODES["gold"]
                else:
                    self.current_state[tile] = CODES["passage"]

    def change_state_after_shooting(self, action):
        hero, direction = action[1], action[2]
        current_tile = None
        for i, j in self.current_state.items():
            if j == hero:
                current_tile = i
        next_tile = current_tile
        while True:
            if direction == "U":
                next_tile = (next_tile[0] - 1, next_tile[1])
            elif direction == "D":
                next_tile = (next_tile[0] + 1, next_tile[1])
            elif direction == "R":
                next_tile = (next_tile[0], next_tile[1] + 1)
            elif direction == "L":
                next_tile = (next_tile[0], next_tile[1] - 1)
            if (self.current_state[next_tile] == CODES["passage"] or self.current_state[next_tile] == CODES["pit"] or
                self.current_state[next_tile] == CODES["gold"]):
                continue
            break

        if self.current_state[next_tile] == CODES["monster"] or "hero" in INVERSE_CODES[self.current_state[next_tile]]:
            self.current_state[next_tile] = CODES["passage"]

    def at_goal(self):
        if CODES["target"] in self.current_state.values():
            return True
        return False



def state_to_dict(state):
    dict_to_return = {}
    for row_index, row in enumerate(state):
        for column_index, cell in enumerate(row):
            dict_to_return[(row_index, column_index)] = cell
    return dict_to_return


def wrap_with_walls(map):
    x_dimension = len(map[0]) + 2
    new_map = [[CODES["wall"]] * x_dimension]
    for row in map:
        new_map.append([CODES["wall"]] + list(row) + [CODES["wall"]])
    new_map.append([CODES["wall"]] * x_dimension)
    return new_map


if __name__ == '__main__':
    print(ex2.ids)
    for number, input in enumerate(inputs.inputs):
        my_checker = WumpusChecker(input)
        print(f"Output on input number {number + 1}: {my_checker.check_controller()}")