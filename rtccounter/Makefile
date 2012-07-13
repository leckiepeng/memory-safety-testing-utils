AR       = ar
CXX      = clang++
CXXFLAGS = -O2

SRC = RuntimeCheckCounter.cpp
OBJ = $(SRC:.cpp=.o)
OUT = librtccounter.a

all: $(OUT) clean

.cpp.o:
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(OUT): $(OBJ)
	$(AR) rcs $(OUT) $(OBJ)

.PHONY: clean

clean:
	rm *.o
