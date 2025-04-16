#include "satnet/baseNode.hpp"
#include "satnet/utils.hpp" // 包含对应的头文件
#include <iostream>

// Constructor and Destructor use the default implementations provided in the
// header.

int BaseNode::move(int id, int dir) {
  using namespace GlobalConfig;
  int x = id / Q;
  int y = id % Q;
  if (dir == 1) {
    y = (y - 1 + Q) % Q;
  } else if (dir == 2) {
    if (x == P - 1) {
      x = 0;
      y = (y + F) % Q;
    } else {
      x = x + 1;
    }
  } else if (dir == 3) {
    y = (y + 1) % Q;
  } else if (dir == 4) {
    if (x == 0) {
      x = P - 1;
      y = (y - F + Q) % Q;
    } else {
      x = x - 1;
    }
  } else {
    // do nothing
  }
  return x * Q + y;
}

void BaseNode::init() {
  // Basic initialization logic (e.g., printing a message)
  std::cout << "BaseNode initialized." << std::endl;
}

void BaseNode::destroy() {
  // Basic destruction logic (e.g., printing a message)
  std::cout << "BaseNode destroyed." << std::endl;
}

void BaseNode::compute() {
  // Basic run logic (e.g., printing a message)
  std::cout << "BaseNode running." << std::endl;
}