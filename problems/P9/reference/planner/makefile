CXX = g++
CXXFLAGS = -std=c++20 -O2 -w -Wall
OBJ = main.o interval.o query.o
TARGET = planner

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJ)

main.o: main.C interval.h query.h
	$(CXX) $(CXXFLAGS) -c main.C

interval.o: interval.C interval.h
	$(CXX) $(CXXFLAGS) -c interval.C

query.o: query.C query.h interval.h
	$(CXX) $(CXXFLAGS) -c query.C

clean:
	rm -f $(OBJ) $(TARGET)

.PHONY: all clean
