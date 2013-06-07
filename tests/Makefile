CFLAGS := -Wall -g -Werror

all: test

test_ret_yopts.c: test_ret.yoda
	python ../yoda -f test_ret.yoda -n test_ret -g cparser

test_show_yopts.c: test_show.yoda
	python ../yoda -f test_show.yoda -n test_show -g cparser

test_ret_yopts.o: test_ret_yopts.c
test_ret.o: test_ret.c test_ret_yopts.c
test_ret: test_ret.o test_ret_yopts.o

test_show_yopts.o: test_show_yopts.c
test_show.o: test_show.c test_show_yopts.c
test_show: test_show.o test_show_yopts.o

clean:
	rm -f test_ret.o test_ret_yopts.* test_ret test_show test_show.o test_show_yopts.*

FORCE:

test: FORCE test_ret test_show
	bash -x test.sh
