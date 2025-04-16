#include "satnet/baseNode.hpp"
#include <iostream>

// Constructor and Destructor use the default implementations provided in the header.

void BaseNode::init() {
    // Basic initialization logic (e.g., printing a message)
    std::cout << "BaseNode initialized." << std::endl;
}

void BaseNode::destroy() {
    // Basic destruction logic (e.g., printing a message)
    std::cout << "BaseNode destroyed." << std::endl;
}

void BaseNode::run() {
    // Basic run logic (e.g., printing a message)
    std::cout << "BaseNode running." << std::endl;
}