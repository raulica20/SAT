#include <iostream>
#include <vector>
#include <set>
#include <string>
#include <fstream>
#include <sstream>
#include <filesystem>
#include <chrono>
#include <windows.h>
#include <psapi.h>

using namespace std;
namespace fs = std::filesystem;

using Clause = set<string>;

bool areEqual(const Clause &a, const Clause &b) {
    return a == b;
}

bool resolveClauses(const Clause &c1, const Clause &c2, Clause &resolvent) {
    for (const auto &lit : c1) {
        string neg = (lit[0] == '-') ? lit.substr(1) : "-" + lit;
        if (c2.count(neg)) {
            resolvent.clear();
            for (const auto &l : c1) if (l != lit) resolvent.insert(l);
            for (const auto &l : c2) if (l != neg) resolvent.insert(l);
            return true;
        }
    }
    return false;
}

bool resolutionSAT(vector<Clause> clauses) {
    vector<Clause> newClauses;
    while (true) {
        for (size_t i = 0; i < clauses.size(); ++i) {
            for (size_t j = i + 1; j < clauses.size(); ++j) {
                Clause resolvent;
                if (resolveClauses(clauses[i], clauses[j], resolvent)) {
                    if (resolvent.empty()) return false;
                    bool exists = false;
                    for (const auto &c : clauses)
                        if (areEqual(c, resolvent)) exists = true;
                    if (!exists)
                        newClauses.push_back(resolvent);
                }
            }
        }
        if (newClauses.empty()) return true;
        clauses.insert(clauses.end(), newClauses.begin(), newClauses.end());
        newClauses.clear();
    }
}

vector<Clause> readCNFFile(const string &filename) {
    ifstream fin(filename);
    vector<Clause> formula;
    string line;
    while (getline(fin, line)) {
        if (line.empty() || line[0] == 'c' || line[0] == 'p')
            continue;
        istringstream iss(line);
        string lit;
        Clause clause;
        while (iss >> lit) {
            if (lit == "0") break;
            clause.insert(lit);
        }
        if (!clause.empty())
            formula.push_back(clause);
    }
    return formula;
}

void printMemoryUsageMB() {
    PROCESS_MEMORY_COUNTERS_EX memCounters;
    GetProcessMemoryInfo(GetCurrentProcess(),
        reinterpret_cast<PPROCESS_MEMORY_COUNTERS>(&memCounters),
        sizeof(memCounters));
    cout << "Memorie privata (MB): " << memCounters.PrivateUsage / (1024 * 1024) << " MB" << endl;
}

int main() {
    string folderPath = "./cnf";  // modifică dacă ai altă locație

    for (const auto &entry : fs::directory_iterator(folderPath)) {
        if (entry.path().extension() == ".cnf") {
            cout << "Fisier: " << entry.path().filename() << endl;

            auto start = chrono::high_resolution_clock::now();

            vector<Clause> formula = readCNFFile(entry.path().string());
            bool sat = resolutionSAT(formula);

            auto end = chrono::high_resolution_clock::now();
            chrono::duration<double> elapsed = end - start;

            cout << "Rezultat: " << (sat ? "SAT" : "UNSAT") << endl;
            cout << "Timp executie: " << elapsed.count() << " secunde" << endl;
            printMemoryUsageMB();
            cout << "----------------------------" << endl;
        }
    }

    return 0;
}
