// domain_heuristic_node.hpp
#pragma once // Keep include guard

// Necessary includes for declarations
#include "base.hpp"     // For BaseNode, World, potentially futr_banned type, route_table type
#include "json.hpp"     // For nlohmann::json (used in constructor)
#include "utils.hpp"    // For GlobalConfig (used by static calcDomainCoords, maybe others)
#include <vector>       // For vis, route_table parameter
#include <string>       // For getName() return type
#include <utility>      // For std::pair (return type of calcDomainCoords)
#include <queue>        // Often needed by BFS implementation details, maybe move to .tpp if purely internal to compute()

// Forward declarations if possible (reduces compile times if full definitions aren't needed)
// class SomeType; // Example

template <int Kp, int Kn>
class DomainHeuristicNode : public BaseNode {

    std::vector<int> vis;
    // Assuming 'route_table' and 'futr_banned' are accessible via BaseNode or elsewhere

public:
    // --- Constructor ---
    DomainHeuristicNode(nlohmann::json config, int id, World world);

    // --- Static Member Functions ---
    // Calculates path cost within a domain using a precomputed route_table
    static void DfsE2ePath(int src, int dst, const std::vector<int>& route_table); // Pass route_table by const reference

    // Calculates domain coordinates (I, J) for a given satellite ID
    static std::pair<int, int> calcDomainCoords(int satelliteId);

    // --- Member Functions ---
    std::string getName() override;

    // Calculates the flat domain ID for a given satellite ID
    int calculateDomainId(int satelliteId);

    // Computes the intra-domain routing table (populates 'route_table') using BFS
    void compute() override;

private:
    // Declare private helper functions here if any
};

// --- Include the Template Implementation File ---
// This line effectively brings the definitions into any file that includes this header.
#include "domain_heuristic_node.tpp"