// domain_heuristic_node.tpp
// No include guard needed here - this file is meant to be included by the .hpp

// Include headers needed specifically for the implementations
#include <cmath>        // For std::floor
#include <stdexcept>    // For potential error handling (e.g., invalid config)
#include <limits>       // Potentially for checking invalid IDs or distances
// #include <iostream> // Uncomment for debugging print statements

// --- Constructor Definition ---
template <int Kp, int Kn>
DomainHeuristicNode<Kp, Kn>::DomainHeuristicNode(nlohmann::json config, int id, World world)
    : BaseNode(config, id, world) // Initialize base class
{
   
}

// --- Static Member Function Definitions ---

template <int Kp, int Kn>
void DomainHeuristicNode<Kp, Kn>::DfsE2ePath(int src, int dst, const std::vector<int>& route_table) {
    // Assumptions: check_lla_status() and calcuDelay(a, b) are globally available or static in another accessible class.
    // Ensure route_table access is within bounds.
    int is_vertical = check_lla_status(); // Assuming it exists
    // (Note: is_vertical is calculated but not used in the provided snippet)

    auto [I_src, J_src] = calcDomainCoords(src);
    auto [I_dst, J_dst] = calcDomainCoords(dst);

    if (I_src == I_dst && J_src == J_dst) {
        // Path calculation within the same domain
        int val = 0;
        int cur = src;
        const int max_hops = route_table.size(); // Safety break for cycles/errors
        int hops = 0;

        while (cur != dst && hops < max_hops) {
            if (cur < 0 || cur >= route_table.size()) {
                // Error: current node ID out of bounds
                // Consider logging this error
                break;
            }
            int nxt = route_table[cur]; // Get next hop from precomputed table
             if (nxt < 0 || nxt >= route_table.size()) {
                 // Error: Invalid next node ID or path broken indicator (-1?)
                 // Consider logging this error
                 break;
             }
            if (nxt == cur) {
                // Error: Cycle detected or invalid table entry
                // Consider logging this error
                break;
            }

            val += calcuDelay(cur, nxt); // Assuming it exists and handles nodes correctly
            cur = nxt;
            hops++;
        }
        // TODO: What should be done with 'val'? Return it? Log it?
        // Function currently returns void.
        // if (cur == dst) { /* Path found, maybe return val */ }
        // else { /* Path not found or error */ }
    } else {
        // Nodes are in different domains, this function only handles intra-domain.
        // Maybe log this or return an error code/special value if the function returned something.
    }
    return;
}


template <int Kp, int Kn>
std::pair<int, int> DomainHeuristicNode<Kp, Kn>::calcDomainCoords(int satelliteId) {
    // Assumption: GlobalConfig::Q and GlobalConfig::P are valid positive integers.
    if (GlobalConfig::Q <= 0 || GlobalConfig::P <= 0) {
        throw std::runtime_error("GlobalConfig::Q and GlobalConfig::P must be positive.");
    }
    int n_s = satelliteId % GlobalConfig::Q;
    int p_s = satelliteId / GlobalConfig::Q;

    // Use static_cast for clarity. Ensure P isn't zero.
    int I_s = static_cast<int>(std::floor(static_cast<double>(p_s) * Kp / GlobalConfig::P));
    int J_s = static_cast<int>(std::floor(static_cast<double>(n_s) * Kn / GlobalConfig::P));

    return std::make_pair(I_s, J_s);
}

// --- Member Function Definitions ---

template <int Kp, int Kn>
std::string DomainHeuristicNode<Kp, Kn>::getName() {
    // Simple override
    return "DomainHeuristicNode";
}

template <int Kp, int Kn>
int DomainHeuristicNode<Kp, Kn>::calculateDomainId(int satelliteId) {
    // Relies on the static helper function and template parameter Kp
    auto [I_s, J_s] = calcDomainCoords(satelliteId);
    // Potential issue if Kp or Kn is 0, resulting in non-unique IDs or division by zero downstream.
    return J_s * Kp + I_s;
}

template <int Kp, int Kn>
void DomainHeuristicNode<Kp, Kn>::compute() {
    // Assumptions:
    // - 'id' is the valid starting node ID for this instance.
    // - 'futr_banned' is a valid pointer (likely from BaseNode) to a structure allowing [node][direction] access.
    // - 'route_table' (likely from BaseNode) is correctly sized and intended to store predecessors.
    // - 'move(node, direction)' function is available and returns the next node ID or an invalid ID (<0?).
    // - Directions are 1, 2, 3, 4.

    if (!futr_banned || vis.empty() /* add check for route_table if needed */) {
        // Handle invalid state, maybe log an error or return early.
        // std::cerr << "Error: DomainHeuristicNode state not initialized correctly." << std::endl;
        return;
    }
    auto& banned = *futr_banned; // Assuming pointer access is correct

    // Reset state for this computation run
    std::fill(vis.begin(), vis.end(), -1);
    // Also reset route_table if it's being computed here
    // std::fill(route_table.begin(), route_table.end(), -1); // Assuming route_table is accessible & needs reset

    std::queue<int> q;

    // Validate starting node ID
    if (id < 0 || id >= vis.size()) {
         // Handle invalid starting ID
         // std::cerr << "Error: Invalid starting ID " << id << std::endl;
         return;
    }

    vis[id] = id; // Mark start node as visited (using 'id' as marker, or maybe 0?)
    // route_table[id] = id; // Indicate start node has no predecessor from within the domain BFS traversal? Or -1?
    q.push(id);

    while (!q.empty()) {
        int cur = q.front();
        q.pop();

        int current_domain_id = calculateDomainId(cur); // Calculate only once per node

        for (int direction = 1; direction <= 4; ++direction) { // Loop directions 1 to 4
            // Check bounds before accessing banned table if necessary
            // if (cur >= banned.size() || direction >= banned[cur].size()) continue; // Example bounds check

            if (banned[cur][direction] == 1) { // Check if link is banned
                continue;
            }

            int nxt = move(cur, direction); // Get neighbor

            // Check if move resulted in a valid node ID
            if (nxt < 0 || nxt >= vis.size()) { // Also check upper bound
                // Invalid move (e.g., off-grid) or invalid ID returned
                continue;
            }

            // Check if the neighbor is in the same domain
            if (calculateDomainId(nxt) != current_domain_id) {
                continue; // Skip neighbors in different domains
            }

            // Standard BFS check: if neighbor not visited yet
            if (vis[nxt] == -1) {
                vis[nxt] = cur; // Mark as visited, storing predecessor
                route_table[nxt] = cur; // Store predecessor in route_table
                q.push(nxt);
            }
        }
    }
}