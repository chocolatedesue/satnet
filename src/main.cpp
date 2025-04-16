#include <map>
#include <string>
#include <ostream>  // Include ostream explicitly for std::cerr
#include <iostream> // Use angle brackets for standard headers

#include "satnet/space.hpp"
#include "satnet/baseNode.hpp"

#define COMMA ,

#define CASE(id, NodeType)                                                     \
  case id:                                                                     \
    (SpaceSimulation<NodeType>(config_file_name)).run();                       \
    break;

static std::map<int, std::string> id2algorithmName;

static void init() {
  id2algorithmName[1000] = "BaseNode";
  id2algorithmName[2003] = "CoinFlipPredNode";
  id2algorithmName[3003] = "DijkstraPredNode";
  id2algorithmName[5001] = "MinHopCountNode";
  id2algorithmName[5100] = "DomainHeuristicNode<10 COMMA 10>";
}

int main(int argc, char **argv) {
  // assert(argc == 3);
  if (argc != 3) {
    std::cerr << "Usage: " << argv[0] << " <config_file> <algorithm_id>"
              << std::endl;
    return 1;
  }
  auto config_file_name = std::string(argv[1]);
  auto algorithm_id = atoi(argv[2]);
  init();
  std::cout << "Algorithm ID: " << algorithm_id
            << ", Algorithm Name: " << id2algorithmName[algorithm_id]
            << std::endl;

  switch (algorithm_id) {
    CASE(1000, BaseNode);

  default:
    std::cerr << "Invalid algorithm ID!" << std::endl;
  }

  return 0;
}