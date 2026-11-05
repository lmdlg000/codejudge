CXX = g++
CXXFLAGS = -std=c++17 -O2 -w -Wall
OBJ = main.o slot.o
TARGET = freeslot

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJ)

main.o: main.cpp slot.h
	$(CXX) $(CXXFLAGS) -c main.cpp

slot.o: slot.cpp slot.h
	$(CXX) $(CXXFLAGS) -c slot.cpp

clean:
	rm -f $(OBJ) $(TARGET)

.PHONY: all clean
