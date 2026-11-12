// P17 弹幕射击（无终端仿真版）—— Game.h
// 一帧七步、画布渲染、计分与生命周期都在这里；实体通过 Game 暴露的接口回填事件。
#ifndef GAME_H
#define GAME_H

#include <list>
#include <string>
#include <vector>

#include "Entities.h"

class Game {
public:
    Game(int h, int w);
    ~Game();

    void tick(char key);
    void dump() const;
    void summary() const;
    bool over() const { return over_; }
    int frame() const { return frame_; }

    // 实体在这几个接口上读写局面
    int height() const { return h_; }
    int width() const { return w_; }
    char currentKey() const { return key_; }
    int playerRow() const;
    int playerCol() const;
    int tankRow() const;
    int tankCol() const;
    int bulletCount() const { return (int)bullets_.size(); }

    void tryFire();
    void addBomb(int r, int c);
    void onBulletHitTank();
    void onBombHitPlayer();

private:
    Game(const Game&);
    Game& operator=(const Game&);

    int h_, w_;
    int frame_ = 0;
    int score_ = 0;
    int hits_ = 0;
    int kills_ = 0;
    int taken_ = 0;
    int cooldown_ = 0;
    bool over_ = false;
    char key_ = '.';
    void paintAt(std::vector<std::string>& canvas, int r, int c, char ch) const;

    Player* player_;
    Tank* tank_;
    std::list<Entity*> bullets_;   // 多态容器：存的是基类指针
    std::list<Entity*> bombs_;
};

#endif
