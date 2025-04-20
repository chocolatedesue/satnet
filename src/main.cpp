#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>

#include "satnet/base.hpp"
#include "satnet/dijkstra.hpp"
#include "satnet/domain_heuristic.hpp"
#include "satnet/minhopcount.hpp"
#include "satnet/space.hpp"
// #include "spdlog/spdlog.h"

// Define algorithm IDs as enum class for type safety
namespace satnet {
enum class AlgorithmId {
  BASE_NODE = 1000,
  COIN_FLIP_PRED_NODE = 2003,
  DIJKSTRA_PRED_NODE = 3003,
  MIN_HOP_COUNT_NODE = 5001,
  MIN_HOP_COUNT_PRED_NODE = 5002,
  DOMAIN_HEURISTIC_NODE = 5100
};
}

// Template function to run simulation with specific node type
template <typename NodeType> void runSimulation(const std::string &configFile) {
  SpaceSimulation<NodeType>(configFile).run();
}

int main(int argc, char **argv) {
  // Validate command-line arguments
  if (argc != 3) {
    std::cerr << "Usage: " << argv[0] << " <config_file> <algorithm_id>"
              << std::endl;
    return EXIT_FAILURE;
  }

  // Parse command-line arguments
  const std::string configFileName(argv[1]);
  const int algorithmId = std::stoi(argv[2]);

  // Map algorithm IDs to their names for display purposes
  const std::unordered_map<int, std::string> algorithmNames = {
      {static_cast<int>(satnet::AlgorithmId::BASE_NODE), "BaseNode"},
      {static_cast<int>(satnet::AlgorithmId::COIN_FLIP_PRED_NODE),
       "CoinFlipPredNode"},
      {static_cast<int>(satnet::AlgorithmId::DIJKSTRA_PRED_NODE),
       "DijkstraPredNode"},
      {static_cast<int>(satnet::AlgorithmId::MIN_HOP_COUNT_NODE),
       "MinHopCountNode"},
      {static_cast<int>(satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE),
       "DomainHeuristicNode<7, 10>"},
      {static_cast<int>(satnet::AlgorithmId::MIN_HOP_COUNT_PRED_NODE),
       "MinHopCountPredNode"},
  };

  try {
    // Display selected algorithm
    std::cout << "Algorithm ID: " << algorithmId
              << ", Algorithm Name: " << algorithmNames.at(algorithmId)
              << std::endl;

    // Run appropriate simulation based on algorithm ID
    switch (algorithmId) {
    case static_cast<int>(satnet::AlgorithmId::BASE_NODE):
      runSimulation<BaseNode>(configFileName);
      break;

    case static_cast<int>(satnet::AlgorithmId::DIJKSTRA_PRED_NODE):
      runSimulation<DijkstraPredNode>(configFileName);
      break;

    case static_cast<int>(satnet::AlgorithmId::MIN_HOP_COUNT_NODE):
      runSimulation<MinHopCountNode>(configFileName);
      break;

    case static_cast<int>(satnet::AlgorithmId::MIN_HOP_COUNT_PRED_NODE):
      runSimulation<MinHopCountPredNode>(configFileName);
      break;
    case static_cast<int>(satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE):
      runSimulation<DomainHeuristicNode<7, 10>>(configFileName);
      break;
    // Add other algorithm cases here
    default:
      std::cerr << "Invalid algorithm ID: " << algorithmId << std::endl;
      return EXIT_FAILURE;
    }
  } catch (const std::out_of_range &) {
    std::cerr << "Unknown algorithm ID: " << algorithmId << std::endl;
    return EXIT_FAILURE;
  } catch (const std::exception &e) {
    std::cerr << "Error: " << e.what() << std::endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}