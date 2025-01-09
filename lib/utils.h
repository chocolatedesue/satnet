#ifndef UTILS_H_
#define UTILS_H_

struct World {
    std::vector<std::array<int, 5> > *cur_banned;
    std::vector<std::array<int, 5> > *futr_banned;
    std::vector<std::array<double, 3> > *sat_pos; // ICRS coordination (km)
    std::vector<std::array<double, 3> > *sat_lla; // Latitude, longitude, attitude (km)
    std::vector<double> *sat_vel; // Movement direction

    World(std::vector<std::array<int, 5> > *cur_banned,
        std::vector<std::array<int, 5> > *futr_banned,
        std::vector<std::array<double, 3> > *sat_pos,
        std::vector<std::array<double, 3> > *sat_lla,
        std::vector<double> *sat_vel) 
        : cur_banned(cur_banned), futr_banned(futr_banned),
        sat_pos(sat_pos), sat_lla(sat_lla), sat_vel(sat_vel) {}
};

#endif