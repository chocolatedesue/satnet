#include <bits/stdc++.h>

const int move[][2] = {{0, -1}, {0, 1}, {-1, 0}, {1, 0}};

double pos[3600][3];
double cost[3600][4];
int next[3600][4];
bool flag[3600];
double dist[3600];
int from[3600];

int dm_id[3600][3600];
int banned[3600][3600];

double rdist[3600];
bool rflag[3600];

int getNeigh(int x, int d) {    
    return (x / 60 + move[d][0] + 60) % 60 * 60 + (x % 60 + move[d][1] + 60) % 60;
}

double getLatency(int u,int v) {
    double dist = 0;
    for(int i = 0; i < 3; i++) {
        dist += (pos[u][i] - pos[v][i]) * (pos[u][i] - pos[v][i]);
    }
    return sqrt(dist) * 1000 / 299792458 * 1000;
}

double getDomainLatency(int s,int t,int match_id, bool flag[], double dist[]) {
    std::priority_queue<std::pair<double,int> > pq;
    for(int i = 0; i < 3600; i++) {
        flag[i] = false;
        dist[i] = 1e18;
    }
    dist[s] = 0;
    pq.push(std::make_pair(-double(0), s));
    while(!pq.empty()) {
        int u = pq.top().second;
        pq.pop();
        if(u == t) return dist[t];
        if(flag[u]) continue;
        flag[u] = true;
        for(int i = 0; i < 4; i++) {
            int v = getNeigh(u, i);
            if(dm_id[u][v] != match_id) continue;
            if(banned[u][v]) continue;
            if(dist[u] + cost[u][i] < dist[v]) {
                dist[v] = dist[u] + cost[u][i];
                pq.push(std::make_pair(-dist[v], v));
            }
        }
    }
    return -1;
}
int main() {
    freopen("/home/phye/leo-celestial-model/testcase-config/test3/sat-geocentric-position/0.csv", "r", stdin);
    for(int i = 0; i < 3600; i++) {
        for(int j = 0; j < 3; j++) {
            scanf("%lf", &pos[i][j]);
        }
    }
    fclose(stdin);

    freopen("failure_links.txt", "r", stdin);
    int num_failures;
    scanf("%d", &num_failures);
    for(int i = 0; i < num_failures; i++) {
        int u, v;
        scanf("%d%d", &u, &v);
        banned[u][v] = banned[v][u] = 1;
    }
    fclose(stdin);

    freopen("domains.txt", "r", stdin);
    int num_dms;
    scanf("%d", &num_dms);
    for(int i = 1; i <= num_dms; i++) {
        int num_edges;
        scanf("%d", &num_edges);
        for(int j = 0; j < num_edges; j++) {
            int u, v;
            scanf("%d%d", &u, &v);
            dm_id[u][v] = dm_id[v][u] = i;
        }
    }
    fclose(stdin);


    for(int u = 0; u < 3600; u++) {
        for(int i = 0; i < 4; i++) {
            int v = getNeigh(u, i);
            cost[u][i] = getLatency(u, v) ;
        }
    }

    for(int i = 0; i < 9; i++) {
        printf("\n");
    }

    int s = 0, t = 1830;
    //for(int s = 0; s < 3600; s++) 
    {
        std::priority_queue<std::pair<double,int> > pq;
        memset(flag, false, sizeof(flag));
        memset(from, -1, sizeof(from));
        for(int i = 0; i < 3600; i++) {
            dist[i] = 1e18;
        }
        dist[s] = 0;
        pq.push(std::make_pair(-double(0), s));
        while(!pq.empty()) {
            int u = pq.top().second;
            pq.pop();
            if(flag[u]) continue;
            flag[u] = true;
            for(int i = 0; i < 4; i++) {
                int v = getNeigh(u, i);
                if(dist[u] + cost[u][i] < dist[v]) {
                    dist[v] = dist[u] + cost[u][i];
                    from[v] = u;
                    pq.push(std::make_pair(-dist[v], v));
                }
            }
        }
//        for(int t = 0; t < 3600; t++) 
        {
//            if(t == s) continue;
            std::vector<int> path;
            int x = t;
            while(x != s) {
                path.push_back(x);
                x = from[x];
            }
            path.push_back(s);

            double real_latency = dist[t];
            bool ok = true;

            for(int i = 0, j = 0; i + 1 < path.size(); i = j) {
                int match_id = dm_id[path[i]][path[i + 1]];
                while(j + 1 < path.size() && dm_id[path[j]][path[j + 1]] == match_id) j++;
                if(match_id != 0) {
                    double alter_latency = (path[i], path[j], match_id, rflag, rdist);
                    if(alter_latency < 0) {
                        ok = false;
                        break;
                    }
                    double orginal_latency = 0;
                    for(int k = i; k < j; k++) {
                        orginal_latency += getLatency(path[k], path[k + 1]);
                    }
                    real_latency += alter_latency - orginal_latency;
                }
            }
            assert(real_latency >= dist[t]);
            printf("route path [%d, %d]\n", s, t);
            printf("latency: %.6lf\n", (ok ? real_latency : 0));
            printf("failure rate: %.6lf\n", (ok ? 0.0 : 1.0));
            /*
            printf("route path [%d, %d]\n", s, t);
            printf("latency: %.6lf\n", (ok ? dist[t] : 0));
            printf("failure rate: %.6lf\n", 0.0);
            */
        }
    }

    return 0;
}
