TARGET = scheduler
CXX = g++
CXXFLAGS = -std=c++20 -O2 -w -Wall

all: $(TARGET)

$(TARGET): main.o topo.o critical.o
	$(CXX) $(CXXFLAGS) -o $(TARGET) main.o topo.o critical.o

main.o: main.C topo.h critical.h
	$(CXX) $(CXXFLAGS) -c main.C -o main.o

topo.o: topo.C topo.h
	$(CXX) $(CXXFLAGS) -c topo.C -o topo.o

critical.o: critical.C critical.h
	$(CXX) $(CXXFLAGS) -c critical.C -o critical.o

clean:
	rm -f *.o $(TARGET) $(TARGET).exe

.PHONY: all clean
