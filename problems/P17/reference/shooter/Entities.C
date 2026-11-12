// P17 弹幕射击（无终端仿真版）—— Entities.C
#include "Entities.h"
#include "Game.h"

void Player::update(Game& g) {
    char k = g.currentKey();
    if (k == 'a') {
        if (col > 0) --col;
    } else if (k == 'd') {
        if (col + 1 < g.width()) ++col;
    } else if (k == 's') {
        g.tryFire();
    }
}

void Tank::update(Game& g) {
    if (g.frame() % 2 != 1) return;          // 每两帧走一格
    int nc = col + dir_;
    if (nc < 0 || nc >= g.width()) {         // 撞墙：本帧原地掉头
        dir_ = -dir_;
        return;
    }
    col = nc;
}

void Tank::reset(int w) {
    row = 1;
    col = w / 2;
    hp_ = 1;
    dir_ = 1;
}

void Bullet::update(Game& g) {
    --row;
    if (row < 0) { dead_ = true; return; }
    if (row == g.tankRow() && col == g.tankCol()) {
        g.onBulletHitTank();
        dead_ = true;
    }
}

void Bomb::update(Game& g) {
    ++row;
    if (row >= g.height()) { dead_ = true; return; }
    if (row == g.playerRow() && col == g.playerCol()) {
        g.onBombHitPlayer();
        dead_ = true;
    }
}
