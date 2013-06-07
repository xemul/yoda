#include <stdio.h>

#include "test_show_yopts.h"

int main(int argc, char **argv)
{
	int ret, i;

	ret = test_show_yopts_parse(argc, argv);

	if (test_show_yopts.action)
		printf("%s\n", test_show_yopts.action);

	printf("%d\n", test_show_yopts.opt_int);

	if (test_show_yopts.opt_string)
		printf("%s\n", test_show_yopts.opt_string);

	printf("%s\n", test_show_yopts.opt_bool ? "true" : "false");

	for (i = 0; i < test_show_yopts.opt_pile_nr; i++)
		printf("%s\n", test_show_yopts.opt_pile[i]);

	return ret ? : argc - yopt_tail;
}
