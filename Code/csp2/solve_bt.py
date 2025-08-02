import os
import random
from bitarray import bitarray

from Code.minesweeper import Minesweeper
from constraints import MSConstraint
from csp_modelling import Variable, CSP
from backtracking import bt_search
import time
from collections import deque, defaultdict

def list_unrevealed_unflagged(game):
    rows, cols = game.rows, game.cols
    return [(r, c) for r in range(rows) for c in range(cols)
            if not game.revealed[r][c] and not game.flagged[r][c]]

def corner_cells(rows, cols):
    return [(0,0),(0,cols-1),(rows-1,0),(rows-1,cols-1)]

def pick_corner_edge_or_random(cells, rows, cols):
    if not cells:
        return None
    corners = [c for c in corner_cells(rows, cols) if c in cells]
    if corners:
        return random.choice(corners)
    edges = [ (r,c) for (r,c) in cells
              if r in (0, rows-1) or c in (0, cols-1) ]
    if edges:
        return random.choice(edges)
    return random.choice(cells)

def random_guess(game):
    choices = list_unrevealed_unflagged(game)
    return random.choice(choices)

def safest_guess(game, prob_map, total_mines):
    rows, cols = game.rows, game.cols
    unrevealed = list_unrevealed_unflagged(game)
    if not unrevealed:
        return None

    # Build constrained list
    constrained = []
    constrained_expected = 0.0
    constrained_set = set()
    for v, p in prob_map.items():
        r, c = divmod(int(v.name()), cols)
        if not game.revealed[r][c] and not game.flagged[r][c]:
            constrained.append(((r,c), p))
            constrained_expected += p
            constrained_set.add((r,c))

    # Remaining mines (estimate)
    flagged_count = sum(game.flagged[r][c] for r in range(rows) for c in range(cols))
    estimated_mines_left = total_mines - flagged_count - constrained_expected
    if estimated_mines_left < 0:
        estimated_mines_left = 0  

    unconstrained_cells = [cell for cell in unrevealed if cell not in constrained_set]
    if unconstrained_cells:
        p_uncon = estimated_mines_left / len(unconstrained_cells)

    # No unconstrained available
    else:
        p_uncon = 1.0  

    if constrained:
        best_con, p_con = min(constrained, key=lambda x: x[1])
        
        if unconstrained_cells and p_uncon < p_con:
            return pick_corner_edge_or_random(unconstrained_cells, rows, cols)
        else:
            return best_con
    else:
        return pick_corner_edge_or_random(unrevealed, rows, cols)

def frontier_guess(game, prob_map):
    rows, cols = game.rows, game.cols

    constrained = []
    for v, p in prob_map.items():
        r, c = divmod(int(v.name()), cols)
        if not game.revealed[r][c] and not game.flagged[r][c]:
            constrained.append(((r,c), p))
    if constrained:
        (cell, _p) = min(constrained, key=lambda x: x[1])
        return cell

    return pick_corner_edge_or_random(list_unrevealed_unflagged(game), rows, cols)

def frontier_balanced_guess(game, prob_map, total_mines, balance_param):
    rows, cols = game.rows, game.cols
    unrevealed = list_unrevealed_unflagged(game)
    if not unrevealed:
        return None

    constrained = []
    constrained_expected = 0.0
    constrained_set = set()
    for v, p in prob_map.items():
        r, c = divmod(int(v.name()), cols)
        if not game.revealed[r][c] and not game.flagged[r][c]:
            constrained.append(((r,c), p))
            constrained_expected += p
            constrained_set.add((r,c))

    flagged_count = sum(game.flagged[r][c] for r in range(rows) for c in range(cols))
    estimated_mines_left = total_mines - flagged_count - constrained_expected
    if estimated_mines_left < 0:
        estimated_mines_left = 0

    unconstrained_cells = [cell for cell in unrevealed if cell not in constrained_set]
    if unconstrained_cells:
        p_uncon = estimated_mines_left / len(unconstrained_cells)
    else:
        p_uncon = 1.0

    if constrained:
        best_con, p_con = min(constrained, key=lambda x: x[1])

        if p_con <= balance_param:
            return best_con

        if unconstrained_cells and p_uncon < p_con:
            return pick_corner_edge_or_random(unconstrained_cells, rows, cols)
        return best_con
    else:
        return pick_corner_edge_or_random(unrevealed, rows, cols)

def frontier_relative_balanced_guess(game, prob_map, total_mines, balance_param):
    rows, cols = game.rows, game.cols
    unrevealed = list_unrevealed_unflagged(game)
    if not unrevealed:
        return None

    constrained = []
    constrained_expected = 0.0
    constrained_set = set()
    for v, p in prob_map.items():
        r, c = divmod(int(v.name()), cols)
        if not game.revealed[r][c] and not game.flagged[r][c]:
            constrained.append(((r,c), p))
            constrained_expected += p
            constrained_set.add((r,c))

    flagged_count = sum(game.flagged[r][c] for r in range(rows) for c in range(cols))
    estimated_mines_left = total_mines - flagged_count - constrained_expected
    if estimated_mines_left < 0:
        estimated_mines_left = 0

    unconstrained_cells = [cell for cell in unrevealed if cell not in constrained_set]
    if unconstrained_cells:
        p_uncon = estimated_mines_left / len(unconstrained_cells)
    else:
        p_uncon = 1.0

    if constrained:
        best_con, p_con = min(constrained, key=lambda x: x[1])

        if p_con <= balance_param + p_uncon:
            return best_con

        if unconstrained_cells and p_uncon < p_con:
            return pick_corner_edge_or_random(unconstrained_cells, rows, cols)
        return best_con
    else:
        return pick_corner_edge_or_random(unrevealed, rows, cols)

def useful_relative_balanced_guess(game, prob_map, total_mines, constraints_list, balance_param):
    rows, cols = game.rows, game.cols
    unrevealed = list_unrevealed_unflagged(game)

    useful_vars = set()

    for cons in constraints_list:
        if cons.get_target() == len(cons.scope()) - 1:
            for var in cons.scope():
                useful_vars.add(var)

    useful_constrained = []
    constrained_expected = 0.0
    constrained_set = set()
    for v, p in prob_map.items():
        r, c = divmod(int(v.name()), cols)
        if not game.revealed[r][c] and not game.flagged[r][c]:
            constrained_expected += p
            constrained_set.add((r, c))
            if v in useful_vars:
                useful_constrained.append(((r, c), p))

    flagged_count = sum(game.flagged[r][c] for r in range(rows) for c in range(cols))
    estimated_mines_left = total_mines - flagged_count - constrained_expected
    if estimated_mines_left < 0:
        estimated_mines_left = 0

    unconstrained_cells = [cell for cell in unrevealed if cell not in constrained_set]
    if unconstrained_cells:
        p_uncon = estimated_mines_left / len(unconstrained_cells)
    else:
        p_uncon = 1.0

    if useful_constrained:
        best_con, p_con = min(useful_constrained, key=lambda x: x[1])

        if p_con <= balance_param + p_uncon:
            return best_con

        if unconstrained_cells and p_uncon < p_con:
            return pick_corner_edge_or_random(unconstrained_cells, rows, cols)

        return best_con

    else:
        return pick_corner_edge_or_random(unrevealed, rows, cols)

def most_useful_guess(game, prob_map, total_mines, constraints_list):
    def best_pick_with_prob_zero_before_mine(cells, rows, cols, p_uncon):
        if not cells:
            return None, -1

        corners = [c for c in corner_cells(rows, cols) if c in cells]
        if corners:
            p_zero = (1 - p_uncon) ** 4
            p_zero_before_mine = p_zero / (p_zero + p_uncon)
            return random.choice(corners), p_zero_before_mine

        edges = [(r, c) for (r, c) in cells
                if r in (0, rows - 1) or c in (0, cols - 1)]
        if edges:
            p_zero = (1 - p_uncon) ** 6
            p_zero_before_mine = p_zero / (p_zero + p_uncon)
            return random.choice(edges), p_zero_before_mine

        else:
            p_zero = (1 - p_uncon) ** 9
            p_zero_before_mine = p_zero / (p_zero + p_uncon)
            return random.choice(cells), p_zero_before_mine

    rows, cols = game.rows, game.cols
    unrevealed = list_unrevealed_unflagged(game)

    useful_vars = set()

    for cons in constraints_list:
        if cons.get_target() == len(cons.scope()) - 1:
            for var in cons.scope():
                useful_vars.add(var)

    useful_constrained = []
    constrained_expected = 0.0
    constrained_set = set()
    for v, p in prob_map.items():
        r, c = divmod(int(v.name()), cols)
        if not game.revealed[r][c] and not game.flagged[r][c]:
            constrained_expected += p
            constrained_set.add((r, c))
            if v in useful_vars:
                useful_constrained.append(((r, c), p))

    flagged_count = sum(game.flagged[r][c] for r in range(rows) for c in range(cols))
    estimated_mines_left = total_mines - flagged_count - constrained_expected
    if estimated_mines_left < 0:
        estimated_mines_left = 0

    unconstrained_cells = [cell for cell in unrevealed if cell not in constrained_set]

    if unconstrained_cells:
        p_uncon = estimated_mines_left / len(unconstrained_cells)
    else:
        p_uncon = 1.0

    cell_free, p_zero_before_mine = best_pick_with_prob_zero_before_mine(
        unconstrained_cells, rows, cols, p_uncon
    )

    if useful_constrained:
        best_con, p_con_mine = min(useful_constrained, key=lambda x: x[1])
        p_con_safe = 1.0 - p_con_mine  # success metric for frontier

        if cell_free is not None and p_zero_before_mine > p_con_safe:
            return cell_free
        return best_con

    else:
        return pick_corner_edge_or_random(unrevealed, rows, cols)

def useful_more_than_k_guess(game, prob_map, total_mines, constraints_list, k):
    rows, cols = game.rows, game.cols
    unrevealed = list_unrevealed_unflagged(game)

    useful_cons_vars = set()

    for cons in constraints_list:
        if cons.get_target() == len(cons.scope()) - 1:
            for var in cons.scope():
                useful_cons_vars.add((cons, var))

    for cons, var in useful_cons_vars:
        game_copy = game.copy()

        other_vars = set(cons.scope())
        other_vars.remove(var)

        game.toggle_flag()






def solve_bt(game, bt_method, bt_heuristic, guessing_heuristic,
             balance_param=1.0, first_probe=(0, 0),
             print_board=False, files=None):

    def add_constraint_for_cell(i, j):
        n = game.get_cell_number(i, j)
        if n is None or n == game.MINE:
            return
        flagged = 0
        covered = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0: continue
                rr, cc = i + dr, j + dc
                if 0 <= rr < rows and 0 <= cc < cols:
                    if game.flagged[rr][cc]:
                        flagged += 1
                    elif not game.revealed[rr][cc]:
                        covered.append(index_to_var[(rr, cc)])
        target = n - flagged
        if covered:
            constraints_list.append(MSConstraint(f"cell_{i}_{j}", covered, target))

    def rebuild_constraints(constraints_list):
        constraints_list.clear()
        for i in range(rows):
            for j in range(cols):
                if game.revealed[i][j]:
                    add_constraint_for_cell(i, j)


    def compute_components(constraints, index_to_var, var_to_index):
        adj = defaultdict(set)
        frontier_vars = set()
        for c in constraints:
            scope = c.scope()
            frontier_vars.update(scope)

            for i in range(len(scope)):
                for j in range(i + 1, len(scope)):
                    v1, v2 = scope[i], scope[j]
                    adj[v1].add(v2)
                    adj[v2].add(v1)

        comps = []
        seen = set()
        for v in frontier_vars:
            if v in seen:
                continue
            q = deque([v])
            seen.add(v)
            comp = []
            while q:
                cur = q.popleft()
                comp.append(cur)
                for nb in adj[cur]:
                    if nb not in seen:
                        seen.add(nb)
                        q.append(nb)
            comps.append(comp)
        return comps


    def constraints_for_component(comp_vars, constraints):
        comp_set = set(comp_vars)
        return [c for c in constraints if all(v in comp_set for v in c.scope())]

    if bt_method not in {"BT", "FC", "GAC"}:
        raise ValueError("bt_method must be one of BT, FC, GAC")
    if bt_heuristic not in {"random", "mrv"}:
        raise ValueError("bt_heuristic must be one of random, mrv")
    if guessing_heuristic not in {"random", "safest", "frontier", "frontier_balanced",
                                  "frontier_relative_balanced", "useful_relative_balanced",
                                  "most_useful"}:
        raise ValueError("guessing_heuristic invalid")
    if guessing_heuristic in {"balanced", "relative_balanced"} and not (0.0 <= balance_param <= 1.0):
        raise ValueError("balance_param out of range")

    rows, cols = game.rows, game.cols
    mines = game.total_mines

    index_to_var = {}
    var_to_index = {}
    for r in range(rows):
        for c in range(cols):
            v = Variable(str(r * cols + c), [0, 1])
            index_to_var[(r, c)] = v
            var_to_index[v] = (r, c)

    constraints_list = []

    game.probe(*first_probe)

    # File logging init (unchanged skeleton)
    if files:
        init_time = time.time()
        prev_time = init_time
        curr_time = init_time
        os.makedirs(os.path.dirname(files[0]), exist_ok=True)
        os.makedirs(os.path.dirname(files[1]), exist_ok=True)
        num_guesses = 0
        csv = open(files[0], "a")
        txt = open(files[1], "w", encoding="utf-8")
        txt.write("\n\n")

    # ------------- Main loop -------------
    while True:
        if print_board:
            print(game.get_board_str(), "\n")
        if files:
            prev_time = curr_time
            cur_time = time.time()
            txt.write(game.get_board_str() + "\n")
            txt.write(f"Took: {cur_time - prev_time} seconds\n\n")

        rebuild_constraints(constraints_list)

        # Terminal checks
        if game.game_over:
            if files:
                txt.seek(0)
                txt.write("Lost\n")
                txt.write(f"Total Time: {cur_time - init_time} seconds\n\n")
                csv.write(f"Lost, {cur_time - init_time}, {num_guesses}\n")
                csv.close()
                txt.close()
            return False
        if game.check_win():
            if files:
                txt.seek(0)
                txt.write("Won\n")
                txt.write(f"Total Time: {cur_time - init_time} seconds\n\n")
                csv.write(f"Won, {cur_time - init_time}, {num_guesses}\n")
                csv.close()
                txt.close()
            return True

        components = compute_components(constraints_list, index_to_var, var_to_index)

        forced_safe = set()
        forced_mine = set()
        prob_map = {}

        for comp_idx, comp_vars in enumerate(components):
            comp_constraints = constraints_for_component(comp_vars, constraints_list)

            local_mine_counts = {v: 0 for v in comp_vars}
            local_total = 0

            def acc(sol):
                nonlocal local_total
                local_total += 1
                for v, val in sol:
                    if val == 1:
                        local_mine_counts[v] += 1

            csp = CSP(f"Comp_{comp_idx}", comp_vars, comp_constraints)

            bt_search(csp=csp, algo=bt_method, variableHeuristic=bt_heuristic,
                      allSolutions=True, trace=False, track_sol=acc)

            for v in comp_vars:
                m = local_mine_counts[v]
                if m == 0:
                    forced_safe.add(var_to_index[v])
                elif m == local_total:
                    forced_mine.add(var_to_index[v])
                prob_map[v] = m / local_total

        if forced_mine or forced_safe:
            for (r, c) in forced_mine:
                if not game.flagged[r][c]:
                    game.toggle_flag(r, c)
            for (r, c) in forced_safe:
                if (not game.revealed[r][c]) and (not game.flagged[r][c]):
                    newly = game.probe(r, c) or set()
                    for (i, j) in newly:
                        add_constraint_for_cell(i, j)
            continue

        if guessing_heuristic == "random":
            r, c = random_guess(game)
        elif guessing_heuristic == "frontier":
            r, c = frontier_guess(game, prob_map)
        elif guessing_heuristic == "safest":
            r, c = safest_guess(game, prob_map, mines)
        elif guessing_heuristic == "frontier_balanced":
            r, c = frontier_balanced_guess(game, prob_map, mines, balance_param)
        elif guessing_heuristic == "frontier_relative_balanced":
            r, c = frontier_relative_balanced_guess(game, prob_map, mines, balance_param)
        elif guessing_heuristic == "useful_relative_balanced":
            r, c = useful_relative_balanced_guess(game, prob_map, mines, constraints_list, balance_param)
        elif guessing_heuristic == "most_useful":
            r, c = most_useful_guess(game, prob_map, mines, constraints_list)
        else:
            print("warning")
            r, c = random_guess(game)

        newly = game.probe(r, c) or set()
        for (i, j) in newly:
            add_constraint_for_cell(i, j)
        if files:
            num_guesses += 1