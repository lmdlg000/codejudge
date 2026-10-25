# examples/P1_make/Makefile —— make 多文件构建链路演示（target=inspector）
# 对照 P6 的 build 配置：{"command":"make","target":"inspector","output":"inspector"}
CXX ?= g++
CXXFLAGS ?= -O2 -std=c++17

inspector: inspector.cpp util.h
	$(CXX) $(CXXFLAGS) -o inspector inspector.cpp

.PHONY: clean
clean:
	rm -f inspector inspector.exe
