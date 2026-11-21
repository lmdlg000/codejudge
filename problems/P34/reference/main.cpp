// P36 迷宫最短通道 —— 情境拓展（趣味数学 7.8 迷宫最短通道）
// 输入 n m 与 n 行迷宫：'.' 空地、'#' 墙、'S' 起点、'T' 终点。
// 每步可上下左右移动一格，输出从 S 到 T 的最少步数；不可达输出 -1。
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, m;
    if (!(cin >> n >> m)) return 0;
    vector<string> g(n);
    int sr = -1, sc = -1, tr = -1, tc = -1;
    for (int i = 0; i < n; ++i) {
        cin >> g[i];
        for (int j = 0; j < m; ++j) {
            if (g[i][j] == 'S') { sr = i; sc = j; }
            if (g[i][j] == 'T') { tr = i; tc = j; }
        }
    }
    vector<vector<int>> dist(n, vector<int>(m, -1));
    queue<pair<int,int>> q;
    dist[sr][sc] = 0;
    q.push({sr, sc});
    int dr[4] = {1, -1, 0, 0}, dc[4] = {0, 0, 1, -1};
    while (!q.empty()) {
        auto [r, c] = q.front(); q.pop();
        if (r == tr && c == tc) break;
        for (int k = 0; k < 4; ++k) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nr >= n || nc < 0 || nc >= m) continue;
            if (g[nr][nc] == '#' || dist[nr][nc] != -1) continue;
            dist[nr][nc] = dist[r][c] + 1;
            q.push({nr, nc});
        }
    }
    cout << dist[tr][tc] << '\n';
    return 0;
}
