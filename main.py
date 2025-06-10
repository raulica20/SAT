import os
import time
import psutil
from collections import defaultdict, deque
from itertools import combinations


class SATSolver:
    def __init__(self):
        self.clauses = []
        self.num_vars = 0
        self.num_clauses = 0
        self.assignment = {}
        self.unit_clauses = deque()
        self.level = {}
        self.trail = []
        self.trail_lim = []
        self.start_time = None

    def load_cnf(self, filepath):
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('c'):
                    continue
                if line.startswith('p'):
                    parts = line.split()
                    self.num_vars = int(parts[2])
                    self.num_clauses = int(parts[3])
                    continue
                clause = [int(x) for x in line.strip().split()[:-1]]
                if clause:
                    self.clauses.append(clause)

    def check_satisfiability(self):
        for clause in self.clauses:
            satisfied = False
            for lit in clause:
                var = abs(lit)
                if var in self.assignment and self.assignment[var] == (lit > 0):
                    satisfied = True
                    break
            if not satisfied:
                return False
        return True

    def pure_literal_elimination(self):
        literal_count = defaultdict(int)
        for clause in self.clauses:
            for lit in clause:
                literal_count[lit] += 1
        pure_literals = []
        for var in range(1, self.num_vars + 1):
            pos, neg = var, -var
            if (pos in literal_count) and (neg not in literal_count):
                pure_literals.append(pos)
            elif (neg in literal_count) and (pos not in literal_count):
                pure_literals.append(neg)
        for lit in pure_literals:
            var = abs(lit)
            if var not in self.assignment:
                self.assignment[var] = lit > 0
                self.level[var] = 0 if not self.trail_lim else len(self.trail_lim)
                self.trail.append(var)
        self.clauses = [c for c in self.clauses if not any(
            lit in pure_literals for lit in c)]

    def unit_propagation_dpll(self):
        clauses_copy = self.clauses.copy()
        updated = True
        while updated:
            updated = False
            unit_clauses = []
            for clause in clauses_copy:
                if any(abs(lit) in self.assignment and self.assignment[abs(lit)] == (lit > 0) for lit in clause):
                    continue
                unassigned_lits = [lit for lit in clause if abs(lit) not in self.assignment]
                if len(unassigned_lits) == 1:
                    unit_clauses.append(unassigned_lits[0])
            for unit_lit in unit_clauses:
                var = abs(unit_lit)
                value = unit_lit > 0
                if var in self.assignment and self.assignment[var] != value:
                    return False
                if var not in self.assignment:
                    self.assignment[var] = value
                    self.level[var] = 0 if not self.trail_lim else len(self.trail_lim)
                    self.trail.append(var)
                    updated = True
            new_clauses = []
            for clause in clauses_copy:
                if any(abs(lit) in self.assignment and self.assignment[abs(lit)] == (lit > 0) for lit in clause):
                    continue
                new_clause = [lit for lit in clause if
                              abs(lit) not in self.assignment or self.assignment[abs(lit)] == (lit > 0)]
                if not new_clause:
                    return False
                new_clauses.append(new_clause)
            clauses_copy = new_clauses
        self.clauses = clauses_copy
        return True

    def resolution(self, cnf):
        clauses = set(frozenset(clause) for clause in cnf)
        iteration_limit = 5000
        clause_limit = 50000
        time_limit = 60
        start_time = time.time()
        iteration_count = 0
        if frozenset() in clauses:
            return False
        if not clauses:
            return True
        while True:
            iteration_count += 1
            if time.time() - start_time > time_limit:
                print("Resolution timed out after", time_limit, "seconds")
                return None
            if iteration_count > iteration_limit or len(clauses) > clause_limit:
                if frozenset() in clauses:
                    return False
                break
            clause_list = list(clauses)
            max_pairs_to_check = min(100000, len(clause_list) * (len(clause_list) - 1) // 2)
            clause_list.sort(key=len)
            new_clauses_added = False
            resolvents = set()
            pairs_checked = 0
            for i, j in combinations(range(min(2000, len(clause_list))), 2):
                pairs_checked += 1
                if pairs_checked > max_pairs_to_check:
                    break
                ci, cj = clause_list[i], clause_list[j]
                if len(ci) > 5 and len(cj) > 5:
                    continue
                for lit in ci:
                    if -lit in cj:
                        resolvent = frozenset((ci | cj) - {lit, -lit})
                        if not resolvent:
                            return False
                        if len(resolvent) > 20:
                            continue
                        if any(existing <= resolvent for existing in clauses):
                            continue
                        if resolvent not in clauses:
                            resolvents.add(resolvent)
                            new_clauses_added = True
                        break
            if not new_clauses_added:
                return True
            clauses.update(resolvents)
            clauses = self.resolution_simplify(clauses)
            if frozenset() in clauses:
                return False

    def resolution_simplify(self, clauses):
        unit_clauses = [c for c in clauses if len(c) == 1]
        simplified = set(clauses)
        while unit_clauses:
            unit = next(iter(unit_clauses[0]))
            unit_clauses.pop(0)
            to_remove = set()
            to_add = set()
            for clause in simplified:
                if unit in clause:
                    to_remove.add(clause)
                elif -unit in clause:
                    new_clause = frozenset(lit for lit in clause if lit != -unit)
                    if not new_clause:
                        return {frozenset()}
                    to_remove.add(clause)
                    to_add.add(new_clause)
                    if len(new_clause) == 1:
                        unit_clauses.append(new_clause)
            simplified = (simplified - to_remove) | to_add
        return simplified

    def dp(self):
        cnf = [clause.copy() for clause in self.clauses]
        return self._dp_recursive(cnf)

    def _dp_recursive(self, cnf):
        unit_clauses = [c for c in cnf if len(c) == 1]
        while unit_clauses:
            unit_lit = unit_clauses[0][0]
            var = abs(unit_lit)
            value = unit_lit > 0
            new_cnf = []
            for clause in cnf:
                if unit_lit in clause:
                    continue
                if -unit_lit in clause:
                    new_clause = [lit for lit in clause if lit != -unit_lit]
                    if not new_clause:
                        return False
                    new_cnf.append(new_clause)
                    if len(new_clause) == 1:
                        unit_clauses.append(new_clause)
                else:
                    new_cnf.append(clause)
            cnf = new_cnf
            unit_clauses = unit_clauses[1:]
        literal_count = defaultdict(int)
        for clause in cnf:
            for lit in clause:
                literal_count[lit] += 1
        pure_literals = []
        for var in range(1, self.num_vars + 1):
            pos = var
            neg = -var
            if (pos in literal_count) ^ (neg in literal_count):
                pure_literals.append(pos if pos in literal_count else neg)
        for lit in pure_literals:
            cnf = [clause for clause in cnf if lit not in clause]
        if not cnf:
            return True
        split_var = abs(cnf[0][0])
        new_cnf_true = [clause.copy() for clause in cnf if split_var not in clause]
        for clause in new_cnf_true:
            if -split_var in clause:
                clause.remove(-split_var)
        if self._dp_recursive(new_cnf_true):
            return True
        new_cnf_false = [clause.copy() for clause in cnf if -split_var not in clause]
        for clause in new_cnf_false:
            if split_var in clause:
                clause.remove(split_var)
        return self._dp_recursive(new_cnf_false)

    def dpll(self):
        self.assignment = {}
        self.level = {}
        self.trail = []
        self.trail_lim = []
        self.unit_clauses = deque()
        self.start_time = time.time()
        original_clauses = [clause.copy() for clause in self.clauses]
        self.unit_clauses.extend([clause[0] for clause in self.clauses if len(clause) == 1])
        try:
            self.pure_literal_elimination()
            result = self._dpll_recursive()
            self.clauses = original_clauses
            return result
        except Exception as e:
            print(f"DPLL Error: {str(e)}")
            self.clauses = original_clauses
            return None

    def _dpll_recursive(self):
        if time.time() - self.start_time > 60:
            print("DPLL timed out")
            return None
        if not self.unit_propagation_dpll():
            return False
        if not self.clauses:
            return True
        unassigned_vars = [var for var in range(1, self.num_vars + 1) if var not in self.assignment]
        if not unassigned_vars:
            return self.check_satisfiability()
        var = self._select_variable(unassigned_vars)
        saved_assignment = self.assignment.copy()
        saved_level = self.level.copy()
        saved_trail = self.trail.copy()
        saved_clauses = [clause.copy() for clause in self.clauses]
        self.assignment[var] = True
        self.level[var] = len(self.trail_lim) if self.trail_lim else 0
        self.trail.append(var)
        if not self.trail_lim or self.trail_lim[-1] != len(self.trail):
            self.trail_lim.append(len(self.trail))
        new_unit = [var]
        self.clauses.append(new_unit)
        self.unit_clauses.append(var)
        if self._dpll_recursive():
            return True
        self.assignment = saved_assignment.copy()
        self.level = saved_level.copy()
        self.trail = saved_trail.copy()
        self.clauses = [clause.copy() for clause in saved_clauses]
        self.unit_clauses.clear()
        self.assignment[var] = False
        self.level[var] = len(self.trail_lim) if self.trail_lim else 0
        self.trail.append(var)
        if not self.trail_lim or self.trail_lim[-1] != len(self.trail):
            self.trail_lim.append(len(self.trail))
        new_unit = [-var]
        self.clauses.append(new_unit)
        self.unit_clauses.append(-var)
        return self._dpll_recursive()

    def _select_variable(self, unassigned_vars):
        var_scores = defaultdict(float)
        for clause in self.clauses:
            for lit in clause:
                var = abs(lit)
                if var in unassigned_vars:
                    var_scores[var] += 2.0 ** -len(clause)
        return max(unassigned_vars, key=lambda v: var_scores.get(v, 0))


def get_algorithm_choice():
    available_algorithms = ['resolution', 'dp', 'dpll']
    print("\nAvailable SAT solving algorithms:")
    for i, algo in enumerate(available_algorithms, 1):
        print(f"{i}. {algo.upper()}")
    choices = input("\nEnter the number of the algorithm you want to use: ")
    selected_indices = [int(x.strip()) - 1 for x in choices.split(',') if x.strip().isdigit()]
    selected_algorithms = []
    for idx in selected_indices:
        if 0 <= idx < len(available_algorithms):
            selected_algorithms.append(available_algorithms[idx])
    if not selected_algorithms:
        print("No valid selection. Using all algorithms by default.")
        return available_algorithms
    return selected_algorithms


def benchmark_sat_solver(directory, algorithms):
    results = []
    process = psutil.Process()
    for filename in os.listdir(directory):
        if filename.endswith('.cnf'):
            filepath = os.path.join(directory, filename)
            print(f"\nBenchmarking file: {filename}")
            for algorithm in algorithms:
                solver = SATSolver()
                solver.load_cnf(filepath)
                start_time = time.time()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB
                try:
                    if algorithm == 'resolution':
                        result = solver.resolution(solver.clauses)
                    elif algorithm == 'dp':
                        result = solver.dp()
                    elif algorithm == 'dpll':
                        result = solver.dpll()
                    else:
                        raise ValueError(f"Unknown algorithm: {algorithm}")
                    elapsed_time = time.time() - start_time
                    end_memory = process.memory_info().rss / 1024 / 1024  # MB
                    peak_memory = end_memory - start_memory
                    if result is None:
                        status = "TIMEOUT"
                    else:
                        status = "SAT" if result else "UNSAT"
                except Exception as e:
                    elapsed_time = time.time() - start_time
                    end_memory = process.memory_info().rss / 1024 / 1024  # MB
                    peak_memory = end_memory - start_memory
                    status = "ERROR"
                    print(f"Error in {algorithm.upper()}: {str(e)}")
                print(f"{algorithm.upper():<10} | {status:<6} | Time: {elapsed_time:.4f}s | Memory: {peak_memory:.2f}MB")
                results.append({
                    'file': filename,
                    'algorithm': algorithm,
                    'time': elapsed_time,
                    'memory': peak_memory,
                    'result': status,
                    'vars': solver.num_vars,
                    'clauses': solver.num_clauses
                })
    return results


def print_benchmark_summary(results):
    print("\nBenchmark Summary:")
    print("=" * 100)
    print("{:<20} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
        "File", "Algorithm", "Result", "Time(s)", "Memory(MB)", "Variables", "Clauses"))
    print("-" * 100)
    for res in results:
        print("{:<20} {:<10} {:<10} {:<10.4f} {:<10.2f} {:<10} {:<10}".format(
            res['file'], res['algorithm'], res['result'], res['time'],
            res['memory'], res['vars'], res['clauses']))
    algorithms = list(set(r['algorithm'] for r in results))
    print("\nAverage Time and Memory by Algorithm:")
    for algo in sorted(algorithms):
        algo_times = [r['time'] for r in results if
                      r['algorithm'] == algo and r['result'] != "ERROR" and r['result'] != "TIMEOUT"]
        algo_memories = [r['memory'] for r in results if
                         r['algorithm'] == algo and r['result'] != "ERROR" and r['result'] != "TIMEOUT"]
        if algo_times:
            avg_time = sum(algo_times) / len(algo_times)
            avg_memory = sum(algo_memories) / len(algo_memories)
            print(f"{algo.upper():<10}: Time: {avg_time:.4f}s, Memory: {avg_memory:.2f}MB (completed runs: {len(algo_times)})")
        else:
            print(f"{algo.upper():<10}: No successful completions")
    print("\nResults by Algorithm:")
    for algo in sorted(algorithms):
        results_by_type = {}
        for result_type in ["SAT", "UNSAT", "TIMEOUT", "ERROR"]:
            count = sum(1 for r in results if r['algorithm'] == algo and r['result'] == result_type)
            if count > 0:
                results_by_type[result_type] = count
        result_str = ", ".join([f"{k}: {v}" for k, v in results_by_type.items()])
        print(f"{algo.upper():<10}: {result_str}")


if __name__ == "__main__":
    cnf_directory = input("Enter the directory path containing CNF files: ").strip()
    algorithms = get_algorithm_choice()
    print("\nSelected algorithms:", ", ".join([algo.upper() for algo in algorithms]))
    if os.path.isdir(cnf_directory):
        benchmark_results = benchmark_sat_solver(cnf_directory, algorithms)
        print_benchmark_summary(benchmark_results)
    else:
        print(f"Directory not found: {cnf_directory}")