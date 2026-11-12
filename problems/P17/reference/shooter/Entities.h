// P17 弹幕射击（无终端仿真版）—— Entities.h
// Player / Tank / Bullet / Bomb 四个具体实体。它们只描述「我怎么动、我长什么样」，
// 计分、生灭、容器管理都交给 Game。
#ifndef ENTITIES_H
#define ENTITIES_H

#include "Entity.h"

class Player : public Entity {
public:
    Player(int r, int c) : Entity(r, c) {}
    void update(Game& g) override;
    char symbol() const override { return 'M'; }
    int lives() const { return lives_; }
    void damage() { if (lives_ > 0) --lives_; }
private:
    int lives_ = 3;
};

class Tank : public Entity {
public:
    Tank(int r, int c) : Entity(r, c) {}
    void update(Game& g) override;
    char symbol() const override { return 'T'; }
    int hp() const { return hp_; }
    void damage() { if (hp_ > 0) --hp_; }
    void reset(int w);   // 被击毁后回到 (1, w/2)，方向朝右、血量恢复
private:
    int hp_ = 1;
    int dir_ = 1;   // +1 向右，-1 向左
};

class Bullet : public Entity {
public:
    Bullet(int r, int c) : Entity(r, c) {}
    void update(Game& g) override;
    char symbol() const override { return '^'; }
    bool dead() const override { return dead_; }
private:
    bool dead_ = false;
};

class Bomb : public Entity {
public:
    Bomb(int r, int c) : Entity(r, c) {}
    void update(Game& g) override;
    char symbol() const override { return '*'; }
    bool dead() const override { return dead_; }
private:
    bool dead_ = false;
};

#endif
