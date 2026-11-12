// P17 弹幕射击（无终端仿真版）—— Game.C
#include "Game.h"

#include <algorithm>
#include <iostream>

Game::Game(int h, int w) : h_(h), w_(w) {
    player_ = new Player(h - 2, w / 2);
    tank_ = new Tank(1, w / 2);
}

Game::~Game() {
    delete player_;
    delete tank_;
    for (Entity* e : bullets_) delete e;
    for (Entity* e : bombs_) delete e;
}

int Game::playerRow() const { return player_->row; }
int Game::playerCol() const { return player_->col; }
int Game::tankRow() const { return tank_->row; }
int Game::tankCol() const { return tank_->col; }

void Game::tryFire() {
    if (cooldown_ > 0) return;          // 还在冷却
    if (bulletCount() >= 3) return;     // 场上子弹已达上限
    bullets_.push_back(new Bullet(player_->row - 1, player_->col));
    cooldown_ = 3;
}

void Game::addBomb(int r, int c) { bombs_.push_back(new Bomb(r, c)); }

void Game::onBulletHitTank() {
    tank_->damage();
    score_ += 10;
    ++hits_;
}

void Game::onBombHitPlayer() {
    player_->damage();
    score_ = std::max(0, score_ - 20);
    ++taken_;
}

void Game::tick(char key) {
    if (over_) return;
    key_ = key;

    if (cooldown_ > 0) --cooldown_;     // ① 冷却递减
    player_->update(*this);             // ② 玩家移动 / 开火
    for (auto it = bullets_.begin(); it != bullets_.end(); ) {   // ③ 子弹推进 + 命中
        (*it)->update(*this);
        if ((*it)->dead()) { delete *it; it = bullets_.erase(it); } else ++it;
    }
    if (tank_->hp() <= 0) {             // ④ 坦克被击毁 → 重生 + 奖励
        tank_->reset(w_);
        score_ += 50;
        ++kills_;
    }
    tank_->update(*this);               // ⑤ 坦克移动（含撞墙掉头）
    if (frame_ % 4 == 2) addBomb(tank_->row + 1, tank_->col);   // ⑥ 投弹
    for (auto it = bombs_.begin(); it != bombs_.end(); ) {      // ⑦ 炸弹推进 + 命中
        (*it)->update(*this);
        if ((*it)->dead()) { delete *it; it = bombs_.erase(it); } else ++it;
    }
    if (player_->lives() <= 0) over_ = true;   // ⑧ 结束判定

    dump();
    ++frame_;
}

void Game::paintAt(std::vector<std::string>& canvas, int r, int c, char ch) const {
    if (r < 0 || r >= h_ || c < 0 || c >= w_) return;
    canvas[r][c] = ch;
}

void Game::dump() const {
    std::vector<std::string> canvas(h_, std::string(w_, ' '));
    for (Entity* e : bombs_) paintAt(canvas, e->row, e->col, e->symbol());
    for (Entity* e : bullets_) paintAt(canvas, e->row, e->col, e->symbol());
    paintAt(canvas, tank_->row, tank_->col, tank_->symbol());
    paintAt(canvas, player_->row, player_->col, player_->symbol());
    for (const std::string& line : canvas) {
        std::string::size_type end = line.find_last_not_of(' ');
        std::cout << (end == std::string::npos ? std::string() : line.substr(0, end + 1)) << "\n";
    }
}

void Game::summary() const {
    std::cout << "SCORE " << score_ << " HITS " << hits_ << " KILLS " << kills_
              << " TAKEN " << taken_ << " LIVES " << player_->lives() << "\n";
}
