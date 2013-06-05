CFLAGS := -Wall -g

all: test

test_ret_yopts.c: test_ret.yoda
	python ../yoda -f test_ret.yoda -n test_ret -g cparser

test_ret_yopts.o: test_ret_yopts.c
test_ret.o: test_ret.c test_ret_yopts.c
test_ret: test_ret.o test_ret_yopts.o

clean:
	rm -f test_ret.o test_ret_yopts.o test_ret_yopts.c test_ret_yopts.h test_ret

FORCE:

test: FORCE test_ret
	bash -x test.sh
