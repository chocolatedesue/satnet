#ifndef GLOBAL_CONFIG_H
#define GLOBAL_CONFIG_H

#include <vector>
#include <iostream> // For example output
#include <numeric>  // For std::iota potentially

class GlobalConfig {
public:
    // --- Singleton Access ---
    // Provides the single point of access to the instance
    static GlobalConfig& getInstance() {
        // Static local variable: constructed on first call,
        // C++11 guarantees thread-safe initialization.
        static GlobalConfig instance;
        return instance;
    }

    // --- Delete Copy/Move Operations ---
    // Prevent copies of the singleton instance
    GlobalConfig(const GlobalConfig&) = delete; // No copy constructor
    GlobalConfig& operator=(const GlobalConfig&) = delete; // No copy assignment
    GlobalConfig(GlobalConfig&&) = delete; // No move constructor
    GlobalConfig& operator=(GlobalConfig&&) = delete; // No move assignment

    // --- Configuration Members (Public for easy access) ---
    // Note: For better encapsulation, you could make these private
    // and provide public getter methods (e.g., getP(), getDomain(), etc.)
    // and potentially a loadConfig() method instead of direct modification.
    std::vector<int> domain;

    // --- Example Methods ---
    // Example function to load some default/initial values
    void loadDefaults() {
        std::cout << "Loading default configuration..." << std::endl;
        domain.resize(10); // Example: resize domain
        std::iota(domain.begin(), domain.end(), 1); // Fill domain with 1, 2, ..., 10
        P = 100;
        Q = 200;
        F = 50;
        N = 1000;
        loaded_ = true; // Mark as loaded
    }

    // Example function to print the current config state
    void printConfig() const {
        std::cout << "--- Current GlobalConfig ---" << std::endl;
        std::cout << "Domain: [";
        for (size_t i = 0; i < domain.size(); ++i) {
            std::cout << domain[i] << (i == domain.size() - 1 ? "" : ", ");
        }
        std::cout << "]" << std::endl;
        std::cout << "P: " << P << std::endl;
        std::cout << "Q: " << Q << std::endl;
        std::cout << "F: " << F << std::endl;
        std::cout << "N: " << N << std::endl;
        std::cout << "Loaded: " << (loaded_ ? "true" : "false") << std::endl;
        std::cout << "----------------------------" << std::endl;
    }


private:
    // --- Private Constructor ---
    // Constructor is private to prevent direct instantiation
    GlobalConfig() {
        std::cout << "GlobalConfig Singleton is being constructed." << std::endl;
        // You could potentially load *essential* defaults here,
        // but explicit loading (like loadDefaults() called from main) is often clearer.
    }

    // --- Private Destructor ---
    // Destructor can be private or public. Private prevents deleting via base pointer
    // if inheriting (not common for singletons), public is fine too.
    ~GlobalConfig() {
         std::cout << "GlobalConfig Singleton is being destructed." << std::endl;
    }

    // --- Private Members ---
    bool loaded_ = false; // Example internal state
};

#endif // GLOBAL_CONFIG_H