#ifndef MINHOPCOUNT_HPP_
#define MINHOPCOUNT_HPP_

#include "satnet/base.hpp"
#include <string> // For std::string

class MinHopCountNode : public BaseNode {
public:
  // Constructor Declaration
  MinHopCountNode(int id);

  // Method Declarations
  std::string getName() override;
  void compute() override;
  std::vector<int> vis; // Visited flags (size N)
};

class MinHopCountPredNode : public BaseNode {
public:
  // Constructor Declaration
  MinHopCountPredNode(int id);

  // Method Declarations
  std::string getName() override;
  void compute() override;
  std::vector<int> vis; // Visited flags (size N)
};

#endif // MINHOPCOUNT_HPP_