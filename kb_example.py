from logic import *

wumpus_kb = PropKB()

P11, P12, P21, P22, P31, B11, B21 = expr('P11, P12, P21, P22, P31, B11, B21')
wumpus_kb.tell(~P11)
wumpus_kb.tell(B11 | '<=>' | (P12 | P21))
wumpus_kb.tell(B21 | '<=>' | (P11 | P22 | P31))
wumpus_kb.tell(~B11)
wumpus_kb.tell(P31)
wumpus_kb.tell(B21)

print((P11 | P21))
print('Test 1: ', wumpus_kb.ask_if_true(B11))
print('Test 2: ', wumpus_kb.ask_if_true(B21))
print('A satisfiable interpretation to the Wumpus knowledge base is:\n',
      dpll_satisfiable(Expr('&', *wumpus_kb.clauses)))
