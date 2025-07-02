from csp_modelling import Constraint, Variable, CSP
from constraints import *
import random

class UnassignedVars:
    '''class for holding the unassigned variables of a CSP. We can extract
       from, re-initialize it, and return variables to it.  Object is
       initialized by passing a select_criteria (to determine the
       order variables are extracted) and the CSP object.

       select_criteria = ['random', 'fixed', 'mrv'] with
       'random' == select a random unassigned variable
       'fixed'  == follow the ordering of the CSP variables (i.e.,
                   csp.variables()[0] before csp.variables()[1]
       'mrv'    == select the variable with minimum values in its current domain
                   break ties by the ordering in the CSP variables.
    '''
    def __init__(self, select_criteria, csp):
        if select_criteria not in ['random', 'fixed', 'mrv']:
            print("Error UnassignedVars given an illegal selection criteria {}. Must be one of 'random', "
                  "'stack', 'queue', or 'mrv'".format(select_criteria))
        self.unassigned = list(csp.variables())
        self.csp = csp
        self._select = select_criteria
        if select_criteria == 'fixed':
            #reverse unassigned list so that we can add and extract from the back
            self.unassigned.reverse()

    def extract(self):
        if not self.unassigned:
            pass #print "Warning, extracting from empty unassigned list"
            return None
        if self._select == 'random':
            i = random.randint(0,len(self.unassigned)-1)
            nxtvar = self.unassigned[i]
            self.unassigned[i] = self.unassigned[-1]
            self.unassigned.pop()
            return nxtvar
        if self._select == 'fixed':
            return self.unassigned.pop()
        if self._select == 'mrv':
            nxtvar = min(self.unassigned, key=lambda v: v.curDomainSize())
            self.unassigned.remove(nxtvar)
            return nxtvar

    def empty(self):
        return len(self.unassigned) == 0

    def insert(self, var):
        if not var in self.csp.variables():
            pass #print "Error, trying to insert variable {} in unassigned that is not in the CSP problem".format(var.name())
        else:
            self.unassigned.append(var)


def bt_search(algo, csp, variableHeuristic, allSolutions, trace):
    '''Main interface routine for calling different forms of backtracking search
       algorithm is one of ['BT', 'FC', 'GAC']
       csp is a CSP object specifying the csp problem to solve
       variableHeuristic is one of ['random', 'fixed', 'mrv']
       allSolutions True or False. True means we want to find all solutions.
       trace True of False. True means turn on tracing of the algorithm

       bt_search returns a list of solutions. Each solution is itself a list
       of pairs (var, value). Where var is a Variable object, and value is
       a value from its domain.
    '''
    varHeuristics = ['random', 'fixed', 'mrv']
    algorithms = ['BT', 'FC', 'GAC']

    #statistics
    bt_search.nodesExplored = 0

    if variableHeuristic not in varHeuristics:
        pass #print "Error. Unknown variable heursitics {}. Must be one of {}.".format(
            #variableHeuristic, varHeuristics)
    if algo not in algorithms:
        pass #print "Error. Unknown algorithm heursitics {}. Must be one of {}.".format(
            #algo, algorithms)

    uv = UnassignedVars(variableHeuristic, csp)
    Variable.clearUndoDict()
    for v in csp.variables():
        v.reset()
    if algo == 'BT':
         solutions = BT(uv, csp, allSolutions, trace)
    elif algo == 'FC':
        for cnstr in csp.constraints():
            if cnstr.arity() == 1:
                FCCheck(cnstr, None, None)  #FC with unary constraints at the root
        solutions = FC(uv, csp, allSolutions, trace)
    elif algo == 'GAC':
        GacEnforce(csp.constraints(), csp, None, None) #GAC at the root
        solutions = GAC(uv, csp, allSolutions, trace)

    return solutions

def BT(unAssignedVars, csp, allSolutions, trace):
    if unAssignedVars.empty():
        if trace: print("{} Solution Found".format(csp.name()))
        soln = []
        for v in csp.variables():
            soln.append((v, v.getValue()))
        return [soln]
    solns = []
    nxtvar = unAssignedVars.extract()
    if trace: print("==>Trying {}".format(nxtvar.name()))
    for val in nxtvar.domain():
        if trace: print("==> {} = {}".format(nxtvar.name(), val))
        nxtvar.setValue(val)
        constraintsOK = True
        for cnstr in csp.constraintsOf(nxtvar):
            if cnstr.numUnassigned() == 0:
                if not cnstr.check():
                    constraintsOK = False
                    if trace: print("<==falsified constraint\n")
                    break
        if constraintsOK:
            new_solns = BT(unAssignedVars, csp, allSolutions, trace)
            if new_solns:
                solns.extend(new_solns)
            if len(solns) > 0 and not allSolutions:
                break

    nxtvar.unAssign()
    unAssignedVars.insert(nxtvar)
    return solns

def FCCheck(constraint, assignedVar, assignedVal):
    """
    Prune the domain of the single un-assigned variable in *constraint*.
    `assignedVar/assignedVal` are the var/value we just committed to higher up
    in the search tree – they are recorded as the *reason* when we prune.

    Returns "OK"  – at least one value survives
            "DWO" – domain-wipe-out (curDomainSize() == 0)
    """
    # There must be exactly one un-assigned variable in the constraint
    var = constraint.unAssignedVars()[0]

    # Iterate over a *copy* of the current domain because we may prune values
    for val in list(var.curDomain()):
        var.setValue(val)                # trial assignment
        if not constraint.check():       # violates the constraint → prune
            var.pruneValue(val, assignedVar, assignedVal)
        var.setValue(None)               # undo the trial assignment

        if var.curDomainSize() == 0:     # domain wipe-out
            return "DWO"

    return "OK"

def FC(unAssignedVars, csp, allSolutions, trace):
    """
    Standard Forward-Checking back-tracking search.
    Mirrors the lecture pseudo-code (slide 63).
    """
    if unAssignedVars.empty():           # -- all variables assigned → solution
        soln = [(v, v.getValue()) for v in csp.variables()]
        if trace:
            print("{} Solution Found".format(csp.name()))
        return [soln]

    bt_search.nodesExplored += 1
    solns = []

    var = unAssignedVars.extract()
    if trace:
        print("==>Trying {}".format(var.name()))

    for val in var.curDomain():          # *current* domain, not the original
        if trace:
            print("==> {} = {}".format(var.name(), val))

        var.setValue(val)
        noDWO = True

        # Forward checking on every constraint that now has exactly one
        # un-assigned variable left (i.e. just `var`)
        for constraint in csp.constraintsOf(var):
            if constraint.numUnassigned() == 1:
                if FCCheck(constraint, var, val) == "DWO":
                    noDWO = False        # wipe-out ⇒ abandon this value
                    break

        if noDWO:
            new_solns = FC(unAssignedVars, csp, allSolutions, trace)
            if new_solns:
                solns.extend(new_solns)
            if solns and not allSolutions:
                # found one solution and the caller only wants the first
                Variable.restoreValues(var, val)
                break

        # restore domains pruned while exploring var = val
        Variable.restoreValues(var, val)

    var.setValue(None)                   # un-assign before back-tracking
    unAssignedVars.insert(var)
    return solns

def GacEnforce(cnstrs, csp, assignedVar, assignedVal):
    while cnstrs:
        cnstr = cnstrs.pop(0)
        for var in cnstr.scope():
            for val in var.curDomain():
                if not cnstr.hasSupport(var, val):
                    var.pruneValue(val, assignedVar, assignedVal)
                    if var.curDomainSize() == 0:
                        return "DWO"
                    for recheck in csp.constraintsOf(var):
                        if recheck != cnstr and not recheck in cnstrs:
                            cnstrs.append(recheck)

    return "OK"

def GAC(unAssignedVars, csp, allSolutions, trace):
    if unAssignedVars.empty():
        if trace:
            pass # print("{} Solution Found".format(csp.name()))
        soln = []
        for v in csp.variables():
            soln.append((v, v.getValue()))
        return [soln]  # each call returns a list of solutions found

    bt_search.nodesExplored += 1
    solns = []  # so far we have no solutions from recursive calls
    var = unAssignedVars.extract()
    if trace:
        pass # print("==>Trying {}".format(var.name()))

    for val in var.curDomain():
        if trace:
            pass # print("==> {} = {}".format(var.name(), val))
        var.setValue(val)
        noDWO = True

        if GacEnforce(csp.constraintsOf(var), csp, var, val) == "DWO":
            noDWO = False

        if noDWO:
            new_solns = GAC(unAssignedVars, csp, allSolutions, trace)
            if new_solns:
                solns.extend(new_solns)
            if len(solns) > 0 and not allSolutions:
                break  # don't bother with other values of var as we found a solution

        Variable.restoreValues(var, val)

    var.setValue(None)
    unAssignedVars.insert(var)
    return solns
