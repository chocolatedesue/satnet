#include "lib/space.hpp"
#include "map"
#define COMMA ,

#define CASE(id, NodeType) \
    case id: \
        (SpaceSimulation< NodeType >(config_file_name)).run(); \
        break;


std::map<int, std::string > id2algorithmName;


void init () {
    id2algorithmName[1000] = "BaseNode";
    id2algorithmName[2003] = "CoinFlipPredNode";
    id2algorithmName[3003] = "DijkstraPredNode";
    id2algorithmName[5001] = "MinHopCountNode";
    id2algorithmName[5100] = "DomainHeuristicNode<10 COMMA 10>";
}
    

int main(int argc, char **argv) {
    assert(argc == 3);
    auto config_file_name = std::string(argv[1]);
    auto algorithm_id = atoi(argv[2]);
    init();
    std::cout << "Algorithm ID: " << algorithm_id << " Algorithm Name: " << id2algorithmName[algorithm_id] << std::endl;

    switch(algorithm_id) {
        // CASE(1000, BaseNode);

        // CASE(1001, DisCoRouteNode)
        // CASE(1002, DisCoRouteProbeNode)
        // CASE(1003, DisCoRoutePredNode)

        // CASE(2001, CoinFlipNode)
        // CASE(2002, CoinFlipProbeNode)
        CASE(2003, CoinFlipPredNode)
        
        // CASE(3001, DijkstraNode)
        // CASE(3002, DijkstraProbeNode)
        CASE(3003, DijkstraPredNode)
        
        // CASE(4001, DagShortNode)
        // CASE(4002, DagShortProbeNode)
        // CASE(4003, DagShortPredNode)
        // CASE(4011, DagShortNormNode<1>)
        // CASE(4012, DagShortNormNode<2>)
        // CASE(4013, DagShortNormNode<3>)
        // CASE(4014, DagShortNormNode<4>)
        // CASE(4015, DagShortNormNode<5>)
        // CASE(4016, DagShortNormNode<6>)
        // CASE(4017, DagShortNormNode<7>)
        // CASE(4018, DagShortNormNode<8>)

        CASE(5001, MinHopCountNode)
        CASE(5100, DomainHeuristicNode<10 COMMA 10>)

       

        // CASE(5002, LbpNode)

        // CASE(6001, DomainRoutingNode<1>)
        // CASE(6002, DomainRoutingNode<3>)
        // CASE(6003, DomainRoutingNode<4>)
        // CASE(6004, DomainRoutingNode<6>)
        // CASE(6005, DomainRoutingNode<12>)
        // CASE(6006, DomainRoutingNode<20>)
        // CASE(6007, DomainRoutingNode<30>)
        // CASE(6008, DomainRoutingNode<60>)

        // CASE(7001, DomainDagShortNode<1>)
        // CASE(7002, DomainDagShortNode<3>)
        // CASE(7003, DomainDagShortNode<4>)
        // CASE(7004, DomainDagShortNode<6>)
        // CASE(7005, DomainDagShortNode<12>)
        // CASE(7006, DomainDagShortNode<20>)
        // CASE(7007, DomainDagShortNode<30>)
        // CASE(7008, DomainDagShortNode<60>)

        // CASE(9001, DomainBridgeNode<1 COMMA 0>)
        // CASE(9002, DomainBridgeNode<3 COMMA 0>)
        // CASE(9003, DomainBridgeNode<4 COMMA 0>)
        // CASE(9004, DomainBridgeNode<6 COMMA 0>)
        // CASE(9005, DomainBridgeNode<12 COMMA 0>)
        // CASE(9006, DomainBridgeNode<20 COMMA 0>)
        // CASE(9007, DomainBridgeNode<30 COMMA 0>)
        // CASE(9008, DomainBridgeNode<60 COMMA 0>)

        // CASE(9011, DomainBridgeNode<1 COMMA 1>)
        // CASE(9012, DomainBridgeNode<3 COMMA 1>)
        // CASE(9013, DomainBridgeNode<4 COMMA 1>)
        // CASE(9014, DomainBridgeNode<6 COMMA 1>)
        // CASE(9015, DomainBridgeNode<12 COMMA 1>)
        // CASE(9016, DomainBridgeNode<20 COMMA 1>)
        // CASE(9017, DomainBridgeNode<30 COMMA 1>)
        // CASE(9018, DomainBridgeNode<60 COMMA 1>)

        // CASE(9021, DomainBridgeNode<1 COMMA 2>)
        // CASE(9022, DomainBridgeNode<3 COMMA 2>)
        // CASE(9023, DomainBridgeNode<4 COMMA 2>)
        // CASE(9024, DomainBridgeNode<6 COMMA 2>)
        // CASE(9025, DomainBridgeNode<12 COMMA 2>)
        // CASE(9026, DomainBridgeNode<20 COMMA 2>)
        // CASE(9027, DomainBridgeNode<30 COMMA 2>)
        // CASE(9028, DomainBridgeNode<60 COMMA 2>)        

        // CASE(9100, NgDomainBridge<1 COMMA 1>)
        // CASE(9110, NgDomainBridge<5 COMMA 1>)
        // CASE(9111, NgDomainBridge<5 COMMA 5>)
        // CASE(9112, NgDomainBridge<5 COMMA 10>)
        // CASE(9113, NgDomainBridge<5 COMMA 15>)
        // CASE(9114, NgDomainBridge<5 COMMA 20>)
        // CASE(9210, NgDomainBridge<10 COMMA 1>)
        // CASE(9211, NgDomainBridge<10 COMMA 5>)
        // CASE(9212, NgDomainBridge<10 COMMA 10>)
        // CASE(9213, NgDomainBridge<10 COMMA 15>)
        // CASE(9214, NgDomainBridge<10 COMMA 20>)
        // CASE(9310, NgDomainBridge<15 COMMA 1>)
        // CASE(9311, NgDomainBridge<15 COMMA 5>)
        // CASE(9312, NgDomainBridge<15 COMMA 10>)
        // CASE(9313, NgDomainBridge<15 COMMA 15>)
        // CASE(9314, NgDomainBridge<15 COMMA 20>)
        // CASE(9411, DiffDomainBridge<1 COMMA 1>)
        // CASE(9412, DiffDomainBridge<1 COMMA 2>)
        // CASE(9413, DiffDomainBridge<1 COMMA 3>)
        // CASE(9414, DiffDomainBridge<1 COMMA 4>)
        // CASE(9415, DiffDomainBridge<1 COMMA 5>)
        // CASE(9421, DiffDomainBridge<8 COMMA 1>)
        // CASE(9422, DiffDomainBridge<8 COMMA 2>)
        // CASE(9423, DiffDomainBridge<8 COMMA 3>)
        // CASE(9424, DiffDomainBridge<8 COMMA 4>)
        // CASE(9425, DiffDomainBridge<8 COMMA 5>)
        // CASE(9431, DiffDomainBridge<10 COMMA 1>)
        // CASE(9432, DiffDomainBridge<10 COMMA 2>)
        // CASE(9433, DiffDomainBridge<10 COMMA 3>)
        // CASE(9434, DiffDomainBridge<10 COMMA 4>)
        // CASE(9435, DiffDomainBridge<10 COMMA 5>)
        // CASE(9441, DiffDomainBridge<15 COMMA 1>)
        // CASE(9442, DiffDomainBridge<15 COMMA 2>)
        // CASE(9443, DiffDomainBridge<15 COMMA 3>)
        // CASE(9444, DiffDomainBridge<15 COMMA 4>)
        // CASE(9445, DiffDomainBridge<15 COMMA 5>)
        // CASE(9451, DiffDomainBridge<20 COMMA 1>)
        // CASE(9452, DiffDomainBridge<20 COMMA 2>)
        // CASE(9453, DiffDomainBridge<20 COMMA 3>)
        // CASE(9454, DiffDomainBridge<20 COMMA 4>)
        // CASE(9455, DiffDomainBridge<20 COMMA 5>)
        // CASE(9511, LocalDomainBridge<1 COMMA 1>)
        // CASE(9512, LocalDomainBridge<1 COMMA 2>)
        // CASE(9513, LocalDomainBridge<1 COMMA 3>)
        // CASE(9514, LocalDomainBridge<1 COMMA 4>)
        // CASE(9515, LocalDomainBridge<1 COMMA 5>)
        // CASE(9521, LocalDomainBridge<8 COMMA 1>)
        // CASE(9522, LocalDomainBridge<8 COMMA 2>)
        // CASE(9523, LocalDomainBridge<8 COMMA 3>)
        // CASE(9524, LocalDomainBridge<8 COMMA 4>)
        // CASE(9525, LocalDomainBridge<8 COMMA 5>)
        // CASE(9531, LocalDomainBridge<10 COMMA 1>)
        // CASE(9532, LocalDomainBridge<10 COMMA 2>)
        // CASE(9533, LocalDomainBridge<10 COMMA 3>)
        // CASE(9534, LocalDomainBridge<10 COMMA 4>)
        // CASE(9535, LocalDomainBridge<10 COMMA 5>)
        // CASE(9541, LocalDomainBridge<15 COMMA 1>)
        // CASE(9542, LocalDomainBridge<15 COMMA 2>)
        // CASE(9543, LocalDomainBridge<15 COMMA 3>)
        // CASE(9544, LocalDomainBridge<15 COMMA 4>)
        // CASE(9545, LocalDomainBridge<15 COMMA 5>)
        // CASE(9551, LocalDomainBridge<20 COMMA 1>)
        // CASE(9552, LocalDomainBridge<20 COMMA 2>)
        // CASE(9553, LocalDomainBridge<20 COMMA 3>)
        // CASE(9554, LocalDomainBridge<20 COMMA 4>)
        // CASE(9555, LocalDomainBridge<20 COMMA 5>)

        default:
            std::cerr << "Invalid algorithm ID!" << std::endl;
    }

    return 0;
}