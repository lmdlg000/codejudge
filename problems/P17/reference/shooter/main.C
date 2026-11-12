// P17 弹幕射击（无终端仿真版）—— main.C
// 只负责：读棋盘尺寸与按键序列 → 逐帧驱动 Game → 打印结算。
#include <iostream>

#include "Game.h"

using namespace std;

int main() {
    int H, W, F;
    if (!(cin >> H >> W >> F)) return 0;

    Game game(H, W);
    for (int i = 0; i < F; i++) {
        char key = '.';
        if (!(cin >> key)) break;
        if (game.over()) break;   // 已经结束就不再处理、也不再输出后续帧
        game.tick(key);
    }
    game.summary();
    return 0;
}
