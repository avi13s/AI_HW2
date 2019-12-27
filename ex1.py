import search
import random
import math
import utils


ids = ["323263442", "312485816"]


class WumpusState:
    def __init__(self, game_map):
        self.directions = {
            'U': (-1, 0),
            'D': (1, 0),
            'R': (0, 1),
            'L': (0, -1)
        }
        self.game_map = []
        self.heroes = {}
        self.keys = []
        self.gold = False
        self.gold_pos = []
        try:
            game_map = [[entity for entity in r] for r in game_map]
            self.game_map.append([20] * (len(game_map[0]) + 2))
            for row in game_map:
                self.game_map.append([20] + row + [20])
            self.game_map.append([20] * (len(game_map[0]) + 2))
            for row, entities in enumerate(self.game_map):
                for col, entity in enumerate(entities):
                    if 11 <= entity <= 14:
                        self.heroes[entity] = [row, col]
                    elif entity == 70:
                        self.gold_pos = [row, col]
        except:
            self.game_map = [[]]

    def to_hashable(self):
        game_map = tuple(tuple(c for c in r) for r in self.game_map)
        heroes = tuple(tuple((hero, tuple(pos))) for hero, pos in self.heroes.items())
        return game_map, heroes, tuple(self.keys), self.gold, tuple(self.gold_pos)

    @staticmethod
    def from_hashable(hashable_state):
        game_map, heroes, keys, gold, gold_pos = hashable_state
        state = WumpusState(None)
        state.game_map = [[c for c in r] for r in game_map]
        state.heroes = {hero: pos for hero, pos in heroes}
        state.keys = list(keys)
        state.gold = gold
        state.gold_pos = gold_pos
        return state


class WumpusProblem(search.Problem):
    """This class implements a wumpus problem"""

    def __init__(self, initial):
        """Don't forget to implement the goal test
        You should change the initial to your own representation.
        search.Problem.__init__(self, initial) creates the root node"""
        search.Problem.__init__(self, WumpusState(initial).to_hashable())

    def hit(self, game_map, hero_pos, direction):
        row, col = hero_pos
        row_delta, col_delta = direction
        row += row_delta
        col += col_delta
        entity = game_map[row][col]
        while entity != 20 and entity != 60 and\
                not (11 <= entity <= 14) and not (45 <= entity <= 49):
            row += row_delta
            col += col_delta
            entity = game_map[row][col]
        return row, col

    def suicide_plan(self, state: WumpusState, row, col):
        monsters = []
        for delta_row, delta_col in state.directions.values():
            entity_row = row + delta_row
            entity_col = col + delta_col
            if state.game_map[entity_row][entity_col] == 60:
                monsters.append((entity_row, entity_col))
        return monsters

    def actions(self, state):
        """Return the actions that can be executed in the given
        state. The result should be a tuple (or other iterable) of actions
        as defined in the problem description file"""
        state = WumpusState.from_hashable(state)
        actions = []
        for hero, hero_pos in state.heroes.items():
            for d, direction in state.directions.items():
                hit_row, hit_col = self.hit(state.game_map, hero_pos, direction)
                if state.game_map[hit_row][hit_col] == 60:
                    actions.append(('shoot', hero, d))
                row, col = hero_pos
                delta_row, delta_col = direction
                entity = state.game_map[row + delta_row][col + delta_col]
                if entity == 20 or entity == 30:
                    continue
                if 45 <= entity <= 49 and not entity + 10 in state.keys:
                    continue
                actions.append(('move', hero, d))
        return actions

    def result(self, state: WumpusState, action):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""
        state = WumpusState.from_hashable(state)
        action, hero, d = action
        delta_row, delta_col = state.directions[d]
        hero_row, hero_col = state.heroes[hero]
        if action == 'move':
            dst_row = hero_row + delta_row
            dst_col = hero_col + delta_col
            entity = state.game_map[dst_row][dst_col]
            monsters = self.suicide_plan(state, dst_row, dst_col)
            state.game_map[hero_row][hero_col] = 10
            state.heroes[hero] = [dst_row, dst_col]
            if entity == 30:
                print('FUCK')
                state.heroes.pop(hero)
            elif len(monsters) > 0:
                state.heroes.pop(hero)
                for monster_row, monster_col in monsters:
                    state.game_map[monster_row][monster_col] = 10
            elif entity == 10:
                state.game_map[dst_row][dst_col] = hero
            elif 45 <= entity <= 49:
                #state.keys.remove(entity + 10)  # TODO ???
                state.game_map[dst_row][dst_col] = hero
            elif 55 <= entity <= 59:
                state.keys.append(entity)
                state.game_map[dst_row][dst_col] = hero
            elif entity == 70:
                state.gold = True
                state.game_map[dst_row][dst_col] = hero
        elif action == 'shoot':
            hit_row, hit_col = self.hit(state.game_map, (hero_row, hero_col), (delta_row, delta_col))
            state.game_map[hit_row][hit_col] = 10
        return state.to_hashable()

    def goal_test(self, state: WumpusState):
        """ Given a state, checks if this is the goal state.
         Returns True if it is, False otherwise."""
        state = WumpusState.from_hashable(state)
        return state.gold

    @staticmethod
    def my_meth():
        return 0.5


    def h(self, node):
        """ This is the heuristic. It gets a node (not a state,
        state can be accessed via node.state)
        and returns a goal distance estimate"""
        if not node.action:
            return 0
        action, hero, direction = node.action
        #prev_state = WumpusState.from_hashable(node.parent.state)
        curr_state = WumpusState.from_hashable(node.state)
        if curr_state.gold:
            return 0
        #print(len(curr_state.heroes))
        if action == 'move':
            if len(curr_state.heroes) == 0:
                return 1000
            #elif utils.probability(0.3):
             #   return 0
            elif hero not in curr_state.heroes:
                if utils.probability(0.7):
                    return 0
            else:
                gold_pos = curr_state.gold_pos
                hero_pos = curr_state.heroes[hero]
                return (gold_pos[0]-hero_pos[0])**2+(gold_pos[1]-hero_pos[1])**2
            #if len(prev_state.heroes) > len(curr_state.heroes):
            #    return 100  # Suicide
            #return 0
        elif action == 'shoot':
            return WumpusProblem.my_meth()
        return 0.5


    """Feel free to add your own functions
    (-2, -2, None) means there was a timeout"""


def create_wumpus_problem(game):
    return WumpusProblem(game)

