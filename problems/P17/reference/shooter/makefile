CXX = g++
CXXFLAGS = -std=c++17 -O2 -w -Wall
OBJ = main.o Game.o Entities.o
TARGET = shooter

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJ)

main.o: main.C Game.h Entities.h Entity.h
	$(CXX) $(CXXFLAGS) -c main.C

Game.o: Game.C Game.h Entities.h Entity.h
	$(CXX) $(CXXFLAGS) -c Game.C

Entities.o: Entities.C Entities.h Entity.h Game.h
	$(CXX) $(CXXFLAGS) -c Entities.C

clean:
	rm -f $(OBJ) $(TARGET)

.PHONY: all clean
