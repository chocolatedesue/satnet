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

// class DijkstraProbeNode

class MinHopCountProbNode : public BaseNode {
protected:
  // Compute routes avoiding specific ports
  void
  computeWithBannedPorts(const std::vector<std::array<int, 5>> *banned_ptr);

public:
  MinHopCountProbNode(int id);
  virtual ~MinHopCountProbNode() = default;

  virtual std::string getName() override;
  // Compute routes using current banned ports (cur_banned)
  virtual void compute() override;
  std::vector<int> vis; // Visited flags (size N)
};

class MinHopCountPredNode : public MinHopCountProbNode {
public:
  // Constructor Declaration
  MinHopCountPredNode(int id);

  // Method Declarations
  std::string getName() override;
  void compute() override;
  std::vector<int> vis; // Visited flags (size N)
};

#endif // MINHOPCOUNT_HPP_