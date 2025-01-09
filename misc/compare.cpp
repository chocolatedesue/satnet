#include <cstdio>
#include <cstdlib>
#include <cassert>

double result[61][6];

int min(int a, int b)
{
	return a < b ? a : b;
}

double max(int a, int b)
{
	return a > b ? a : b;
}

int abs(int a)
{
	return a > 0 ? a : -a;
}

int hopcount(int s, int t)
{
	return min(abs(s / 60 - t / 60), 60 - abs(s / 60 - t / 60)) + min(abs(s % 60 - t % 60), 60 - abs(s % 60 - t % 60));
}

int main()
{
	FILE *fpDij = fopen("base.txt", "r");
	FILE *fpLoc = fopen("huawei.txt", "r");
	char tmp[60];
	for (int i = 1; i <= 9; i++)
	{
		fgets(tmp, 60, fpDij);
		fgets(tmp, 60, fpLoc);
	}
	/*
	route path [0, 1]
		latency: 2.922107
		failure rate: 0.000000
	*/
	char tmp2[30];
	int s, t;
	double lat0, lat1;
	while (fscanf(fpDij, "%[^\[][%d,%d]%[^:]:%lf", tmp, &s, &t, tmp2, &lat0) != EOF)
	{
		int ss = s, tt = t;
		fscanf(fpLoc, "%[^\[][%d,%d]%[^:]:%lf", tmp, &s, &t, tmp2, &lat1);
		assert(ss == s && tt == t);
		if(lat0 == 0) continue;
		int hop = hopcount(s, t);
		//printf("s = %d, t = %d, hopcount = %d\n", s, t, hop);
		double diff = lat1 - lat0, diffp = (lat1 - lat0) / lat0;
		/*
		if (diff > result[hop][0])
		{
			result[hop][0] = diff;
			result[hop][1] = s;
			result[hop][2] = t;
		}
		if (diffp > result[hop][3])
		{
			result[hop][3] = diffp;
			result[hop][4] = s;
			result[hop][5] = t;
		}
		*/

		result[hop][0] += lat0;
		result[hop][1] += lat1;
		result[hop][2] += 1;

	}
	FILE *fpRes = fopen("result.csv", "w");
	fprintf(fpRes, "k,avg_lat0,avg_lat1,avg_diff,extra_percent\n");
	for (int i = 1; i <= 60; i++) {
		double avg_lat0 = result[i][0] / result[i][2];
		double avg_lat1 = result[i][1] / result[i][2];
		double extra_percent = (avg_lat1 - avg_lat0) / avg_lat0 * 100;
		fprintf(fpRes, "%d,%.6lf,%.6lf,%.6lf,%6lf\n", i, avg_lat0, avg_lat1, avg_lat1 - avg_lat0, extra_percent);
	}
	/*
	for (int i = 1; i <= 60; i++)
		printf("%.6lf %d %d %.6lf %d %d\n",
			result[i][0], int(result[i][1]), int(result[i][2]),
			result[i][3], int(result[i][4]), int(result[i][5]));
	*/
	return 0;
}