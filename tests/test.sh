#!/bin/bash

function yoda_exec
{
	local ret=$1
	shift
	"$@"
	[ "$?" -eq "$ret" ] || { echo FAIL: "$@"; exit 1; }
}

yoda_exec 255 ./test_ret
yoda_exec 255 ./test_ret something
yoda_exec 0   ./test_ret start

yoda_exec 255 ./test_ret start --something
yoda_exec 0   ./test_ret start --id 100
yoda_exec 0   ./test_ret start   -i 100
yoda_exec 0   ./test_ret start --id 0x100
yoda_exec 255 ./test_ret start --id
yoda_exec 255 ./test_ret start --id 123a
yoda_exec 255 ./test_ret start --id a123
yoda_exec 0   ./test_ret start --id 1 --id 2

yoda_exec 0   ./test_ret start -s "something about someone"
yoda_exec 0   ./test_ret start --str "something about someone"
yoda_exec 255 ./test_ret start -s

yoda_exec 255 ./test_ret start --yes
yoda_exec 0   ./test_ret start -y
yoda_exec 1   ./test_ret start -y 1
yoda_exec 1   ./test_ret start -y unknown

yoda_exec 0   ./test_ret stop --stop-opt --opt-for-stop-opt
yoda_exec 255 ./test_ret start --stop-opt --opt-for-stop-opt
yoda_exec 255 ./test_ret stop --stop-opt
yoda_exec 255 ./test_ret stop --opt-for-stop-opt

echo PASS
