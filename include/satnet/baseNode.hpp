#pragma once

#include <iostream>

class BaseNode {
    public:
    BaseNode() = default;
    virtual ~BaseNode() = default;
    
    // This function is called when the node is created.
    virtual void init() ;
    
    // This function is called when the node is destroyed.
    virtual void destroy() ;
    
    // This function is called to run the node.
    virtual void run() ;
};