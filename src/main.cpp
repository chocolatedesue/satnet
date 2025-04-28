#include <functional> // For std::function
#include <iostream>
#include <stdexcept>
#include <string>

#include <unordered_map>

// --- Include all your algorithm headers here ---
#include "satnet/base.hpp"
#include "satnet/dijkstra.hpp"
#include "satnet/domain_heuristic.hpp"
#include "satnet/minhopcount.hpp"
#include "satnet/space.hpp"
#include "satnet/utils.hpp"
// #include "spdlog/spdlog.h" // 假设 setup_logger() 在 utils.hpp 或其他地方定义
// #include "path/to/your/new_algorithm.hpp" // Example for a new algorithm

// Define algorithm IDs as enum class for type safety (Keep this)
namespace satnet {
enum class AlgorithmId {
  // --- 1. 添加新的 Enum 值 ---
  BASE_NODE = 1,
  COIN_FLIP_PRED_NODE = 2, // 假设你有 CoinFlipPredNode.hpp
  DIJKSTRA_PROBE_NODE = 100,
  DIJKSTRA_PRED_NODE = 101,
  MIN_HOP_COUNT_NODE = 150,
  MIN_HOP_COUNT_PRED_NODE = 151,
  DOMAIN_HEURISTIC_NODE_7_10 = 200,
  DOMAIN_HEURISTIC_NODE_4_10 = 201,
  DOMAIN_HEURISTIC_NODE_7_20 = 202,
  DOMAIN_HEURISTIC_NODE_4_20 = 203,
  DOMAIN_HEURISTIC_NODE_4_2 = 204,
  DOMAIN_HEURISTIC_NODE_2_2 = 205,
  DOMAIN_HEURISTIC_NODE_14_60 = 206,
  DOMAIN_HEURISTIC_NODE_1_2 = 207,
  DOMAIN_HEURISTIC_NODE_2_1 = 208,
  DOMAIN_HEURISTIC_NODE_1_1 = 209,

  // {AlgorithmId::NEW_ALGORITHM_NODE, {"NewAlgorithm", runNewAlgorithm}},
  // Add more algorithms as needed
  // Example for a new algorithm:
  // {AlgorithmId::NEW_ALGORITHM_NODE, {"NewAlgorithm", runNewAlgorithm}},
  // NEW_ALGORITHM_NODE = 6000, // Example for a new algorithm
};
} // namespace satnet

// Template function to run simulation with specific node type (Keep this)
template <typename NodeType> void runSimulation(const std::string &configFile) {
  // 假设 SpaceSimulation 和 run() 定义在 satnet/space.hpp 或类似文件中
  SpaceSimulation<NodeType>(configFile).run();
}

// Structure to hold algorithm information (Name and execution function)
struct AlgorithmInfo {
  std::string name;
  std::function<void(const std::string &)>
      runFunc; // Function takes config file path
};

// Function to get the central algorithm registry
// Using a static map inside a function ensures safe initialization (Meyers'
// Singleton)
const std::unordered_map<satnet::AlgorithmId, AlgorithmInfo> &
getAlgorithmRegistry() {
  // --- 2. 在这里添加新算法的注册信息 ---
  static const std::unordered_map<satnet::AlgorithmId, AlgorithmInfo> registry =
      {
          {satnet::AlgorithmId::BASE_NODE,
           {
               "BaseNode", // Display Name
               [](const std::string &cfg) {
                 runSimulation<BaseNode>(cfg);
               } // Lambda calling runSimulation
           }},
          //   {satnet::AlgorithmId::COIN_FLIP_PRED_NODE,
          //    {"CoinFlipPredNode",
          //     [](const std::string &cfg) {
          //       // runSimulation<CoinFlipPredNode>(cfg); // 假设存在
          //       // CoinFlipPredNode 类型
          //     }}},
          {satnet::AlgorithmId::DIJKSTRA_PROBE_NODE,
           {"DijkstraProbeNode",
            [](const std::string &cfg) {
              runSimulation<DijkstraProbeNode>(cfg);
            }}},
          {satnet::AlgorithmId::DIJKSTRA_PRED_NODE,
           {"DijkstraPredNode",
            [](const std::string &cfg) {
              runSimulation<DijkstraPredNode>(cfg);
            }}},
          {satnet::AlgorithmId::MIN_HOP_COUNT_NODE,
           {"MinHopCountNode",
            [](const std::string &cfg) {
              runSimulation<MinHopCountNode>(cfg);
            }}},
          {satnet::AlgorithmId::MIN_HOP_COUNT_PRED_NODE,
           {"MinHopCountPredNode",
            [](const std::string &cfg) {
              runSimulation<MinHopCountPredNode>(cfg);
            }}},
          {satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE_7_10,
           {"DomainHeuristicNode<7, 10>",
            [](const std::string &cfg) {
              runSimulation<DomainHeuristicNode<7, 10>>(cfg);
            }}},
          {satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE_4_10,
           {"DomainHeuristicNode<4, 10>",
            [](const std::string &cfg) {
              runSimulation<DomainHeuristicNode<4, 10>>(cfg);
            }}},
          {satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE_7_20,
           {"DomainHeuristicNode<7, 20>",
            [](const std::string &cfg) {
              runSimulation<DomainHeuristicNode<7, 20>>(cfg);
            }}},
          {satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE_4_20,
           {

               "DomainHeuristicNode<4, 20>",
               [](const std::string &cfg) {
                 runSimulation<DomainHeuristicNode<4, 20>>(cfg);
               }

           }},
          {satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE_4_2,
           {"DomainHeuristicNode<4, 2>",
            [](const std::string &cfg) {
              runSimulation<DomainHeuristicNode<4, 2>>(cfg);
            }}},
          {satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE_2_2,
           {"DomainHeuristicNode<2, 2>",
            [](const std::string &cfg) {
              runSimulation<DomainHeuristicNode<2, 2>>(cfg);
            }}},
          {satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE_14_60,
           {"DomainHeuristicNode<14, 60>",
            [](const std::string &cfg) {
              runSimulation<DomainHeuristicNode<14, 60>>(cfg);
            }}},

          {satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE_1_2,

           {"DomainHeuristicNode<1, 2>",
            [](const std::string &cfg) {
              runSimulation<DomainHeuristicNode<1, 2>>(cfg);
            }}},

          {
              satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE_2_1,
              {"DomainHeuristicNode<2, 1>",
                [](const std::string &cfg) {
                  runSimulation<DomainHeuristicNode<2, 1>>(cfg);
                }},
          },
          {satnet::AlgorithmId::DOMAIN_HEURISTIC_NODE_1_1,
           {"DomainHeuristicNode<1, 1>",
            [](const std::string &cfg) {
              runSimulation<DomainHeuristicNode<1, 1>>(cfg);
            }}},

          /* Example for adding a new algorithm:
          {satnet::AlgorithmId::NEW_ALGORITHM_NODE,
           {"NewAlgorithmDisplayName",
            [](const std::string& cfg){ runSimulation<NewAlgorithmNode>(cfg); }
           }},
          */
      };
  return registry;
}

int main(int argc, char **argv) {
  // Validate command-line arguments
  if (argc != 3) {
    std::cerr << "Usage: " << argv[0] << " <config_file> <algorithm_id>"
              << std::endl;
    return EXIT_FAILURE;
  }

  setup_logger(); // Make sure this function is defined and available

  // Parse command-line arguments
  const std::string configFileName(argv[1]);
  int algorithmIdInt = 0;
  try {
    algorithmIdInt = std::stoi(argv[2]);
  } catch (const std::invalid_argument &e) {
    std::cerr << "Error: Invalid algorithm ID format '" << argv[2]
              << "'. Must be an integer." << std::endl;
    return EXIT_FAILURE;
  } catch (const std::out_of_range &e) {
    std::cerr << "Error: Algorithm ID '" << argv[2]
              << "' is out of range for integer." << std::endl;
    return EXIT_FAILURE;
  }

  // Cast the integer ID to the enum type for map lookup
  const auto algorithmId = static_cast<satnet::AlgorithmId>(algorithmIdInt);
  const auto &registry = getAlgorithmRegistry();

  try {
    // Find the algorithm in the registry
    auto it = registry.find(algorithmId);

    // Check if the algorithm ID exists in the registry
    if (it == registry.end()) {
      // Use the original integer ID for the error message as the enum cast
      // might be invalid
      throw std::out_of_range("Unknown or invalid algorithm ID: " +
                              std::to_string(algorithmIdInt));
    }

    // Get the AlgorithmInfo (name and run function)
    const auto &info = it->second;

    // Display selected algorithm
    std::cout << "Algorithm ID: " << algorithmIdInt
              << ", Algorithm Name: " << info.name << std::endl;

    // --- 3. 无需修改这里 ---
    // Run the appropriate simulation using the stored function object
    info.runFunc(configFileName);

  } catch (
      const std::out_of_range &e) { // Catches map::at or our thrown exception
    std::cerr << "Error: " << e.what() << std::endl;
    // Optionally print available algorithms
    std::cerr << "Available algorithm IDs:" << std::endl;
    for (const auto &pair : registry) {
      std::cerr << "  " << static_cast<int>(pair.first) << ": "
                << pair.second.name << std::endl;
    }
    return EXIT_FAILURE;
  } catch (const std::exception &e) {
    std::cerr << "Runtime Error: " << e.what() << std::endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}