CCC     = clang++
CCFLAGS = -O2

SRC = RuntimeCheckCounter.cpp
OBJ = $(SRC:.cpp=.o)
OUT = librtccounter.a

all: $(OUT) clean

.cpp.o:
	$(CCC) $(CCFLAGS) -c $< -o $@

$(OUT): $(OBJ)
	ar rcs $(OUT) $(OBJ)

.PHONY: clean

clean:
	rm *.o
