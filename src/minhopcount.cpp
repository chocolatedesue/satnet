#include "satnet/minhopcount.hpp" // Include the header for this class
#include "satnet/base.hpp"
#include "satnet/utils.hpp"
#include <queue>     // For std::queue used in compute()
#include <stdexcept> // Potentially for error handling (optional)
#include <vector> // Assuming vis and route_table might be std::vector if not C-style arrays

// Constructor Definition
MinHopCountNode::MinHopCountNode(int id) : BaseNode(id), vis(GlobalConfig::N) {}

// getName Method Definition
std::string MinHopCountNode::getName() { return "MinHopCount"; }

// compute Method Definition
void MinHopCountNode::compute() {

  for (int i = 0; i < GlobalConfig::N; ++i) { // Using this->N explicitly
    this->vis[i] = 0;
    this->route_table[i] = 0;
  }

  std::queue<int> q;

  // Use this->id explicitly for clarity or if needed
  this->vis[this->id] = 1; // Mark distance from source to source as 1 (or 0 if
                           // preferred, adjust logic)
  q.push(this->id);

  while (!q.empty()) {
    int u = q.front();
    q.pop();

    // Iterate through possible moves (1 to 4)
    for (int direction = 1; direction <= 4; ++direction) {

      // Calculate the neighbor node v
      // Use this->move explicitly if needed
      int v = move(u, direction);
      // If neighbor v hasn't been visited yet
      if (this->vis[v] == 0) {
        this->vis[v] = this->vis[u] + 1; // Set distance/hop count
        q.push(v);                       // Add neighbor to the queue
      }

      // If we found a path to v with the same shortest distance
      // This part implements tie-breaking: choose the path whose
      // first step (from the source 'id') had the smallest direction index.
      if (this->vis[v] == this->vis[u] + 1) {
        // Determine the first direction taken from the source node 'id'
        // If u is the source, the first direction is the current 'direction'.
        // Otherwise, the first direction is stored in route_table[u].
        int first_direction =
            (u == this->id) ? direction : this->route_table[u];

        // If v has no route assigned yet, or if the new path's
        // first direction is better (smaller index) than the existing one
        if (this->route_table[v] == 0 ||
            first_direction < this->route_table[v]) {
          this->route_table[v] =
              first_direction; // Update the route table for v
        }
      }
    }
  }
}


// class MinHopCountPredNode : public BaseNode {
//   public:
//     // Constructor Declaration
//     MinHopCountPredNode(int id);
  
//     // Method Declarations
//     std::string getName() override;
//     void compute() override;
//     std::vector<int> vis; // Visited flags (size N)
//   };
  

MinHopCountPredNode::MinHopCountPredNode(int id): BaseNode(id), vis(GlobalConfig::N) {
  // Constructor implementation (if needed)
}

// getName Method Definition
std::string MinHopCountPredNode::getName() { return "MinHopCountPred"; }

// compute Method Definition
void MinHopCountPredNode::compute() {
  const auto &banned = GlobalConfig::futr_banned;
  
  // Initialize visited and route_table arrays

  for (int i = 0; i < GlobalConfig::N; ++i) { // Using this->N explicitly
    this->vis[i] = 0;
    this->route_table[i] = 0;
  }

  std::queue<int> q;

  // Use this->id explicitly for clarity or if needed
  this->vis[this->id] = 1; // Mark distance from source to source as 1 (or 0 if
                           // preferred, adjust logic)
  q.push(this->id);

  while (!q.empty()) {
    int u = q.front();
    q.pop();

    // Iterate through possible moves (1 to 4)
    for (int direction = 1; direction <= 4; ++direction) {
      if (banned[u][direction] == 1) {
        continue; // Skip if the move is banned
      }

      // Calculate the neighbor node v
      // Use this->move explicitly if needed
      int v = move(u, direction);
      
      // If neighbor v hasn't been visited yet
      if (this->vis[v] == 0) {
        this->vis[v] = this->vis[u] + 1; // Set distance/hop count
        q.push(v);                       // Add neighbor to the queue
      }

      // If we found a path to v with the same shortest distance
      // This part implements tie-breaking: choose the path whose
      // first step (from the source 'id') had the smallest direction index.
      if (this->vis[v] == this->vis[u] + 1) {
        // Determine the first direction taken from the source node 'id'
        // If u is the source, the first direction is the current 'direction'.
        // Otherwise, the first direction is stored in route_table[u].
        int first_direction =
            (u == this->id) ? direction : this->route_table[u];

        // If v has no route assigned yet, or if the new path's
        // first direction is better (smaller index) than the existing one
        if (this->route_table[v] == 0 ||
            first_direction < this->route_table[v]) {
          this->route_table[v] =
              first_direction; // Update the route table for v
        }
      }
    }
  }
}
// The MinHopCountPredNode class is similar to MinHopCountNode but