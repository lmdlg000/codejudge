// P17 弹幕射击（无终端仿真版）—— Entity.h
// 抽象基类：所有场上对象都继承它，update 由 Game 按固定顺序调用，paint 把自己画到画布上。
#ifndef ENTITY_H
#define ENTITY_H

class Game;

class Entity {
public:
    Entity(int r, int c) : row(r), col(c) {}
    virtual ~Entity() {}                       // 多态删除必须虚析构
    virtual void update(Game& g) = 0;          // 每帧推进一次
    virtual char symbol() const = 0;           // 在画布上显示成什么字符
    virtual bool dead() const { return false; } // 该不该从容器里摘掉
    int row;
    int col;
};

#endif
