#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <filesystem>
#include <unordered_map>
#include <sstream>
#include <regex>
#include <chrono>
#include <thread>
#include <windows.h>
#include <psapi.h>

namespace fs = std::filesystem;

void show_memory_usage() {
    HANDLE hProcess = GetCurrentProcess();
    PROCESS_MEMORY_COUNTERS memCounters;

    if (GetProcessMemoryInfo(hProcess, &memCounters, sizeof(memCounters))) {
        double workingSetSizeMB = static_cast<double>(memCounters.WorkingSetSize) / 1024 / 1024;
        double pagefileUsageMB = static_cast<double>(memCounters.PagefileUsage) / 1024 / 1024;

        std::cout << "Memorie utilizata (MB): " << workingSetSizeMB << " MB" << std::endl;
        std::cout << "Memorie virtuala (MB): " << pagefileUsageMB << " MB" << std::endl;
    } else {
        std::cerr << "Eroare la obtinerea informatiilor despre memorie!" << std::endl;
    }

    CloseHandle(hProcess);
}

class CNF {
public:
    int numar_variabile;
    int numar_clauze;
    std::vector<std::vector<int>> clauze;

    bool incarca_din_fisier(const std::string& fisier) {
        std::ifstream file(fisier);
        if (!file.is_open()) {
            std::cerr << "Eroare la deschiderea fisierului: " << fisier << std::endl;
            return false;
        }

        std::string linie;
        bool in_header = true;
        while (getline(file, linie)) {
            std::stringstream ss(linie);
            if (linie[0] == 'c') {
                continue;
            }
            if (linie[0] == 'p') {
                ss >> linie >> linie >> numar_variabile >> numar_clauze;
                in_header = false;
            } else if (!in_header) {
                std::vector<int> clauza;
                int litera;
                while (ss >> litera) {
                    if (litera == 0) break;
                    clauza.push_back(litera);
                }
                clauze.push_back(clauza);
            }
        }
        return true;
    }
};

bool unit_propagation(CNF& cnf, std::unordered_map<int, bool>& solutie) {
    bool modificare = false;
    for (auto& clauza : cnf.clauze) {
        if (clauza.size() == 1) {
            int litera = clauza[0];
            if (solutie.find(abs(litera)) == solutie.end()) {
                solutie[abs(litera)] = (litera > 0);
                modificare = true;
            }
        }
    }
    return modificare;
}

bool DPLL(CNF& cnf, std::unordered_map<int, bool>& solutie) {
    while (unit_propagation(cnf, solutie));

    for (const auto& clauza : cnf.clauze) {
        bool satisfacut = false;
        for (int litera : clauza) {
            if (solutie.find(abs(litera)) != solutie.end()) {
                if (solutie[abs(litera)] == (litera > 0)) {
                    satisfacut = true;
                    break;
                }
            }
        }
        if (!satisfacut) {
            return false;
        }
    }

    return true;
}

std::vector<std::string> gaseste_toate_cnf(const std::string& folder) {
    std::vector<std::string> fisier_cnf;

    for (const auto& entry : fs::directory_iterator(folder)) {
        if (entry.path().extension() == ".cnf") {
            fisier_cnf.push_back(entry.path().string());
        }
    }

    std::sort(fisier_cnf.begin(), fisier_cnf.end(), [](const std::string& a, const std::string& b) {
        std::regex rgx(R"(\d+)");
        std::smatch match_a, match_b;

        std::regex_search(a, match_a, rgx);
        std::regex_search(b, match_b, rgx);

        return std::stoi(match_a.str()) < std::stoi(match_b.str());
    });

    return fisier_cnf;
}

int main() {
    auto start_time = std::chrono::high_resolution_clock::now();

    std::cout << "Utilizarea memoriei înainte de procesare:" << std::endl;
    show_memory_usage();

    std::string folder = "cnf";
    std::vector<std::string> fisier_cnf = gaseste_toate_cnf(folder);

    if (fisier_cnf.empty()) {
        std::cerr << "Nu am gasit niciun fisier .cnf in folderul 'cnf/'!" << std::endl;
        return 1;
    }

    for (const auto& path : fisier_cnf) {
        std::cout << "Folosesc fisierul: " << path << std::endl;

        CNF cnf;
        if (!cnf.incarca_din_fisier(path)) {
            std::cerr << "Eroare la incarcarea fisierului CNF." << std::endl;
            continue;
        }

        std::unordered_map<int, bool> solutie;
        if (DPLL(cnf, solutie)) {
            std::cout <<  "nu este satisfiabila!" << std::endl;
            for (const auto& [var, val] : solutie) {
                std::cout << "x" << var << " = " << (val ? "true" : "false") << std::endl;
            }
        } else {
            std::cout <<  "  este satisfiabila!" << std::endl;
        }
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end_time - start_time;

    std::cout << "Timp de execuție: " << duration.count() << " secunde" << std::endl;

    std::cout << "Utilizarea memoriei după procesare:" << std::endl;
    show_memory_usage();

    return 0;
}
