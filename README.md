SAT Solver
A Python implementation of SAT solvers for DIMACS CNF files, including Resolution, Davis-Putnam (DP), and DPLL algorithms with unit propagation and pure literal elimination.
Features

Algorithms:

Resolution: Basic resolution-based SAT solving.
Davis-Putnam (DP): Implements the Davis-Putnam algorithm.
DPLL: Davis-Putnam-Logemann-Loveland with unit propagation and pure literal elimination.


Input: DIMACS CNF files.
Output: Result (SAT, UNSAT, TIMEOUT, ERROR), execution time (seconds), and memory usage (MB).
Metrics: Measured using time and psutil for accurate resource tracking.
Heuristic for DPLL: Variable selection based on
$\sum_{C \ni v} 2^{-|C|}$, where $C$ is a clause containing variable $v$.
Timeout: Resolution may timeout after 300 seconds on large files.
Scalability: DP scales poorly for large instances; see the LaTeX paper for details.

Requirements

Python: 3.8 or higher
psutil: Install via pip install psutil

Installation

Clone the repository:
clone https://github.com/raulica20/SAT
cd SAT

Install the required package:
-install psutil

Place DIMACS CNF files in a directory (e.g., cnf_files/).

Usage:

Run the solver:
 main.py

Enter the directory containing CNF files when prompted:
the directory path containing CNF files: ../dataset/...(UF50 for example)

Select the algorithms to run (e.g., 1,3 for Resolution and DPLL):
textCollapseWrapCopyAvailable SAT solving algorithms:
1. RESOLUTION
2. DP
3. DPLL
Enter the numbers of the algorithm you want to use : 1
