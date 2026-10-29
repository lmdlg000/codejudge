CXX = g++
CXXFLAGS = -std=c++20 -O2 -w -Wall
OBJ = main.o graph.o paths.o
TARGET = router

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJ)

main.o: main.C graph.h paths.h
	$(CXX) $(CXXFLAGS) -c main.C

graph.o: graph.C graph.h
	$(CXX) $(CXXFLAGS) -c graph.C

paths.o: paths.C paths.h graph.h
	$(CXX) $(CXXFLAGS) -c paths.C

clean:
	rm -f $(OBJ) $(TARGET)

.PHONY: all clean
