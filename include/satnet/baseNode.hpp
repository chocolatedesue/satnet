#pragma once

#include <iostream>

class BaseNode {
    public:
    int id;
    BaseNode(int id) : id(id) {
        // Constructor logic (if any)
    }
    virtual ~BaseNode() = default;

    virtual int move(int id, int dir);

    virtual void compute();
    
    // This function is called when the node is created.
    virtual void init() ;
    
    // This function is called when the node is destroyed.
    virtual void destroy() ;
    

};