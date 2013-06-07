#include <stdio.h>

#include "test_ret_yopts.h"

int main(int argc, char **argv)
{
	int ret;
	ret = test_ret_yopts_parse(argc, argv);
	printf("Parser returned %d (left %d(%s)... options)\n", ret, yopt_tail, argv[yopt_tail]);

	return ret ? : argc - yopt_tail;
}
