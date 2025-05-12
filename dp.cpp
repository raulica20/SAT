#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <map>
#include <string>
#include <algorithm>
#include <chrono>
#include <windows.h>
#include <psapi.h>
#include <filesystem>

using namespace std;
namespace fs = std::filesystem;

typedef vector<int> Clause;
typedef vector<Clause> CNF;

map<string, int> symbolToId;
map<int, string> idToSymbol;
int nextVarId = 1;

void show_memory_usage() {
    HANDLE hProcess = GetCurrentProcess();
    PROCESS_MEMORY_COUNTERS memCounters;
    if (GetProcessMemoryInfo(hProcess, &memCounters, sizeof(memCounters))) {
        double workingSetSizeMB = static_cast<double>(memCounters.WorkingSetSize) / 1024 / 1024;
        double pagefileUsageMB = static_cast<double>(memCounters.PagefileUsage) / 1024 / 1024;
        cout << "Memorie utilizata (MB): " << workingSetSizeMB << " MB" << endl;
        cout << "Memorie virtuala (MB): " << pagefileUsageMB << " MB" << endl;
    } else {
        cerr << "Eroare la obtinerea informatiilor despre memorie!" << endl;
    }
    CloseHandle(hProcess);
}

int getLiteralId(const string &token) {
    bool neg = false;
    string symbol = token;
    if (token[0] == '-') {
        neg = true;
        symbol = token.substr(1);
    }
    if (symbolToId.find(symbol) == symbolToId.end()) {
        symbolToId[symbol] = nextVarId;
        idToSymbol[nextVarId] = symbol;
        nextVarId++;
    }
    int id = symbolToId[symbol];
    return neg ? -id : id;
}

bool isSatisfied(const CNF &formula) {
    return formula.empty();
}

bool hasEmptyClause(const CNF &formula) {
    for (auto &clause : formula)
        if (clause.empty()) return true;
    return false;
}

CNF simplify(const CNF &formula, int literal) {
    CNF newFormula;
    for (auto &clause : formula) {
        if (find(clause.begin(), clause.end(), literal) != clause.end()) continue;
        Clause newClause;
        for (int lit : clause) {
            if (lit != -literal)
                newClause.push_back(lit);
        }
        newFormula.push_back(newClause);
    }
    return newFormula;
}

int chooseLiteral(const CNF &formula) {
    for (auto &clause : formula)
        for (int lit : clause)
            return lit;
    return 0;
}

void printModel(const map<int, bool> &model) {
    for (auto &[var, val] : model)
        cout << idToSymbol[var] << " = " << (val ? "True" : "False") << "  ";
    cout << endl;
}

bool dp(CNF formula, map<int, bool> &model) {
    if (isSatisfied(formula)) return true;
    if (hasEmptyClause(formula)) return false;
    int literal = chooseLiteral(formula);
    model[abs(literal)] = (literal > 0);
    if (dp(simplify(formula, literal), model))
        return true;
    model[abs(literal)] = !(literal > 0);
    return dp(simplify(formula, -literal), model);
}

vector<CNF> readFormulasFromFolder(const string &folder_path) {
    vector<CNF> formulas;
    for (const auto &entry : fs::directory_iterator(folder_path)) {
        if (entry.path().extension() == ".cnf") {
            ifstream infile(entry.path());
            string line;
            CNF current;
            while (getline(infile, line)) {
                if (line.empty()) {
                    if (!current.empty()) {
                        formulas.push_back(current);
                        current.clear();
                    }
                    continue;
                }
                stringstream ss(line);
                string token;
                Clause clause;
                while (ss >> token)
                    clause.push_back(getLiteralId(token));
                current.push_back(clause);
            }
            if (!current.empty())
                formulas.push_back(current);
        }
    }
    return formulas;
}

int main() {
    string folder_path = "cnf";
    auto start_time = chrono::high_resolution_clock::now();
    cout << "Utilizarea memoriei înainte de procesare:" << endl;
    show_memory_usage();
    vector<CNF> formulas = readFormulasFromFolder(folder_path);
    for (size_t i = 0; i < formulas.size(); ++i) {
        map<int, bool> model;
        bool sat = dp(formulas[i], model);
        cout << "Formula " << i + 1 << " - " << (sat ? "sat" : "unsat") << endl;
    }
    auto end_time = chrono::high_resolution_clock::now();
    chrono::duration<double> duration = end_time - start_time;
    cout << "Timp de execuție: " << duration.count() << " secunde" << endl;
    cout << "Utilizarea memoriei după procesare:" << endl;
    show_memory_usage();
    return 0;
}
