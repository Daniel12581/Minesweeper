from csp_modelling import Constraint

class MSConstraint(Constraint):
    """
    Constraint representing a Minesweeper “number” cell:
    Ensures that the sum of its adjacent (covered) variables equals the specified mine count.

    Each variable in scope is assumed to take values in {0,1}, where 1 indicates a mine.
    The target sum is (revealed_number − flagged_neighbors) for that cell.
    """

    def __init__(self, name, scope, target_mine_count):
        """
        Args:
            name (str): Identifier for this constraint.
            scope (list of Variable): The list of adjacent covered-cell variables.
            target_mine_count (int): The exact number of mines among those variables.
                                     (i.e., revealed_number − existing_flag_count)
        """
        super().__init__(name, scope)
        self._name = "Minesweeper_" + name
        self._target = target_mine_count

    def get_target(self):
        return self._target

    def check(self):
        """
        If some variables in scope are still unassigned, return True (cannot yet falsify).
        Once all are assigned, return True iff their sum equals self._target.
        """
        assigned_values = []
        for v in self.scope():
            if v.isAssigned():
                assigned_values.append(v.getValue())
            else:
                return True

        return sum(assigned_values) == self._target

    def hasSupport(self, var, val):
        """
        Return True iff 'var = val' can be extended to an assignment of every
        other variable in the scope that satisfies this constraint.

        Domains contain only 0/1, so we can reason with simple counts.
        """
        if var not in self.scope():
            return True

        if not var.inCurDomain(val):
            return False

        assigned_sum = 0
        unassigned = []
        for v in self.scope():
            if v is var:
                continue
            if v.isAssigned():
                assigned_sum += v.getValue()
            else:
                unassigned.append(v)

        remaining = self._target - (assigned_sum + val)

        min_possible = 0
        max_possible = 0
        for v in unassigned:
            has0 = v.inCurDomain(0)
            has1 = v.inCurDomain(1)
            if has1:
                max_possible += 1
            if not has0 and has1:
                min_possible += 1

        if remaining < min_possible or remaining > max_possible:
            return False

        return True