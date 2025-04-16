#pragma once

// #include <iostream>
#include <array>
#include <vector>
#include <string>

class BaseNode {
    public:
    int id;
    std::vector<int> route_table;
    std::vector<std::array<int, 5> > *cur_banned;
    std::vector<std::array<int, 5> > *futr_banned;
    std::vector<std::array<double, 3> > *sat_pos;
    std::vector<std::array<double, 3> > *sat_lla;

    BaseNode(int id) ;
    virtual ~BaseNode() = default;

    virtual int move(int id, int dir);

    virtual void compute();


    virtual std::string getName();
    // This function is called when the node is created.
    virtual void init() ;
    
   
    

};