import os
import random

from Code.minesweeper import Minesweeper
from constraints import MSConstraint
from csp_modelling import Variable, CSP
from backtracking import bt_search
import time

def random_guess(game, rows, cols):
    possible_guess = [
        (i, j)
        for i in range(rows)
        for j in range(cols)
        if not game.revealed[i][j] and not game.flagged[i][j]
    ]

    guess_cell = random.choice(possible_guess)
    r, c = guess_cell

    return r, c

def safest_guess(game, rows, cols, mines, solution_dicts, csp, varn):
    mine_prob = {}
    total_sols = len(solution_dicts)
    for var in csp.variables():
        mine_prob[var] = sum(sol_dict[var] for sol_dict in solution_dicts) / total_sols

    if mine_prob:
        best_constrained_var = min(mine_prob, key=mine_prob.get)
        best_constrained_prob = mine_prob[best_constrained_var]
        best_constrained_cell = divmod(int(best_constrained_var.name()), cols)

        unrevealed_unflagged = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if not game.revealed[r][c] and not game.flagged[r][c]
        ]
        unconstrained_cells = [
            (r, c) for (r, c) in unrevealed_unflagged
            if varn[(r, c)] not in mine_prob
        ]

        remaining_mines = mines - sum(game.flagged[r][c] for r in range(rows) for c in range(cols))
        remaining_cells = len(unrevealed_unflagged)
        unconstrained_prob = (
            remaining_mines / remaining_cells if remaining_cells else 1.0
        )

        if unconstrained_cells and unconstrained_prob < best_constrained_prob:
            corners = [(0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)]
            corners = [xy for xy in corners if xy in unconstrained_cells]
            if corners:
                guess_cell = random.choice(corners)
            else:
                edges = [
                    (r, c) for (r, c) in unconstrained_cells
                    if r == 0 or r == rows - 1 or c == 0 or c == cols - 1
                ]
                guess_cell = random.choice(edges) if edges else random.choice(unconstrained_cells)
        else:
            guess_cell = best_constrained_cell

        r, c = guess_cell

    else:
        unrevealed_unflagged = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if not game.revealed[r][c] and not game.flagged[r][c]
        ]

        corners = [(0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)]
        corners = [xy for xy in corners if xy in unrevealed_unflagged]
        if corners:
            guess_cell = random.choice(corners)
        else:
            edges = [
                (r, c) for (r, c) in unrevealed_unflagged
                if r in (0, rows - 1) or c in (0, cols - 1)
            ]
            guess_cell = random.choice(edges) if edges else random.choice(unrevealed_unflagged)

        r, c = guess_cell

    return r, c


def frontier_guess(game, rows, cols, mines, solution_dicts, csp, varn):
    mine_prob = {}
    total_sols = len(solution_dicts)
    for var in csp.variables():
        mine_prob[var] = sum(sol_dict[var] for sol_dict in solution_dicts) / total_sols

    if mine_prob:
        best_constrained_var = min(mine_prob, key=mine_prob.get)
        best_constrained_cell = divmod(int(best_constrained_var.name()), cols)
        r, c = best_constrained_cell

    else:
        unrevealed_unflagged = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if not game.revealed[r][c] and not game.flagged[r][c]
        ]

        corners = [(0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)]
        corners = [xy for xy in corners if xy in unrevealed_unflagged]
        if corners:
            guess_cell = random.choice(corners)
        else:
            edges = [
                (r, c) for (r, c) in unrevealed_unflagged
                if r in (0, rows - 1) or c in (0, cols - 1)
            ]
            guess_cell = random.choice(edges) if edges else random.choice(unrevealed_unflagged)

        r, c = guess_cell

    return r, c


def balanced_guess():
    ...

def solve_bt(game, bt_method, bt_heuristic, guessing_heuristic, balance_param,
             first_probe=(0, 0), print_board = False, files = None):
    def rebuild_constraints():
        constraints_list.clear()
        for i in range(rows):
            for j in range(cols):
                if game.revealed[i][j]:
                    add_constraint_for_cell(i, j)

    def add_constraint_for_cell(i, j):
        n = game.get_cell_number(i, j)
        if n is None or n == game.MINE:
            return

        flagged_count = 0
        covered_neighbors = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = i + dr, j + dc
                if 0 <= rr < rows and 0 <= cc < cols:
                    if game.flagged[rr][cc]:
                        flagged_count += 1
                    elif not game.revealed[rr][cc]:
                        covered_neighbors.append(varn[(rr, cc)])

        target = n - flagged_count
        if covered_neighbors:
            name = f"cell_{i}_{j}"
            c = MSConstraint(name, covered_neighbors, target)
            constraints_list.append(c)

    def build_csp():
        vars_in_scope = set()
        for con in constraints_list:
            vars_in_scope.update(con.scope())
        return CSP("MinesweeperCSP",
                   list(vars_in_scope),
                   constraints_list)

    if bt_method not in {"BT", "FC", "GAC"} or bt_heuristic not in {"random", "mrv"} or \
        guessing_heuristic not in {"random", "safest", "frontier", "balanced"}:
        raise ValueError("bt_method must be one of random, FC, GAC")

    if guessing_heuristic == "balanced" and (balance_param < 0 or balance_param > 1):
        raise ValueError("balance_param must be between 0 and 1")

    rows = game.rows
    cols = game.cols
    mines = game.total_mines

    var_list = []
    varn = {}
    for r in range(rows):
        for c in range(cols):
            v = Variable(str(r * cols + c), [0, 1])
            var_list.append(v)
            varn[(r, c)] = v

    constraints_list = []

    r0, c0 = first_probe
    game.probe(r0, c0)

    if files:
        init_time = time.time()
        prev_time = time.time()
        cur_time = time.time()
        os.makedirs(os.path.dirname(files[0]), exist_ok=True)
        os.makedirs(os.path.dirname(files[1]), exist_ok=True)
        num_guesses = 0
        csv = open(files[0], "a")
        txt = open(files[1], "w", encoding="utf-8")
        txt.write("\n\n")
        s = ["", ""]

    while True:
        if print_board:
            print(game.get_board_str() + "\n")
        if files:
            prev_time = cur_time
            cur_time = time.time()
            txt.write(game.get_board_str() + "\n")
            txt.write(f"Took: {cur_time - prev_time} seconds\n\n")

        rebuild_constraints()
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

        csp = build_csp()
        all_sols = bt_search(csp = csp, algo = bt_method, variableHeuristic = bt_heuristic, allSolutions=True, trace=False)

        solution_dicts = []
        for sol in all_sols:
            solution_dicts.append({var: val for (var, val) in sol})

        forced_safe, forced_mine = set(), set()
        for var in csp.variables():
            vals = [sol_dict[var] for sol_dict in solution_dicts]

            r, c = divmod(int(var.name()), cols)
            if all(v == 0 for v in vals):
                forced_safe.add((r, c))
            elif all(v == 1 for v in vals):
                forced_mine.add((r, c))

        if forced_mine:
            for (r, c) in forced_mine:
                if not game.flagged[r][c]:
                    game.toggle_flag(r, c)

        if forced_safe:
            for (sr, sc) in forced_safe:
                if not game.revealed[sr][sc] and not game.flagged[sr][sc]:
                    game.probe(sr, sc)

        if forced_mine or forced_safe:
            continue

        if guessing_heuristic == "random":
            r, c = random_guess(game, rows, cols)

        elif guessing_heuristic == "safest":
            r, c = safest_guess(game, rows, cols, mines, solution_dicts, csp, varn)

        elif guessing_heuristic == "frontier":
            r, c = frontier_guess(game, rows, cols, mines, solution_dicts, csp, varn)

        elif guessing_heuristic == "balanced":
            r, c = ...

        newly = game.probe(r, c) or set()

        if files:
            num_guesses += 1

        for (i, j) in newly:
            add_constraint_for_cell(i, j)

