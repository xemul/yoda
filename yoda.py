#
# Yoda -- Yet Options Descriptor Another.
#
# An utility to generate command-line related things like options C parser,
# help text, man page bash completion, etc.
#
# * This program is licensed under the GNU General Public License v2 (you can
# find its text in the COPYING file). This program is distributed in the hope
# that it will be useful, but without any warranty; without even the implied 
# warranty of merchantability OR fitness for a particular purpose. See the GNU
# General Public License for more details.
#
# * Any file generated by this program (parser, help text, man page, anything
# else) is licenses under any license, the person who runs this program, wants.
#
# (C) Copyright  Pavel Emelyanov <xemul@sacred.ru>, 2013
#

import sys

opt_option = 1
opt_argument = 2

typ_boolean = 1
typ_integer = 2
typ_string = 3

class yoption:
	def __init__(self, otype):
		self.choice = []
		self.otype = otype
	pass

class ychoice:
	pass

# Read yoda file in

yfile = open(sys.argv[1])

yopts = []
yopt_name_len_max = 0
yopt_has_arg = None

short_h_busy = False

for l in yfile:
	if (l.startswith("#")):
		continue

	ls = l.strip().split(None, 1)
	if (not ls):
		continue

	if (ls[0] == "option"):
		yopt = yoption(opt_option)

		ln = ls[1].split("/")
		yopt.lname = ln[0]
		if (len(ln) == 2):
			yopt.sname = ln[1]
			if yopt.sname == "h":
				short_h_busy = True

		yopts.append(yopt)
		if (yopt_name_len_max < len(yopt.lname)):
			yopt_name_len_max = len(yopt.lname)
	elif (ls[0] == "arg"):
		yopt = yoption(opt_argument)

		yopt.lname = ls[1]

		yopts.append(yopt)
		if not yopt_has_arg:
			yopt_has_arg = yopt
	elif (ls[0] == "int"):
		yopt.atype = typ_integer
		yopt.summary = ls[1]
	elif (ls[0] == "bool"):
		yopt.atype = typ_boolean
		yopt.summary = ls[1]
	elif (ls[0] == "string"):
		yopt.atype = typ_string
		yopt.summary = ls[1]
	elif (ls[0] == "choice"):
		cs = ls[1].split(None, 1)
		yc = ychoice()
		yc.val = cs[0]
		yc.summary = cs[1]
		yopt.choice.append(yc)
	elif (ls[0] == "default"):
		yopt.defval = ls[1]
	elif (ls[0] == "req_for"):
		yopt.required_for = ls[1]
	else:
		print "Unknown keyword", ls[0]
		continue

yfile.close()

# Add standart help option

yopt = yoption(opt_option)
yopt.lname = "help"
yopt.atype = typ_boolean
yopt.summary = "show help text"
if not short_h_busy:
	yopt.sname = "h"

yopts.append(yopt)

##
#	
# Generate sources
#
##

yname = sys.argv[2];

ctypes = {
	typ_boolean:	"bool",
	typ_integer:	"int",
	typ_string:	"char *",
}

def opt_cname(yopt):
	if yopt.lname:
		return yopt.lname.replace("-", "_")
	else:
		return "opt_" + yopt.sname

def opt_pname(yopt):
	if yopt.otype == opt_option:
		if yopt.lname:
			return "--%s" % yopt.lname
		else:
			return "-%s" % yopt.sname
	else:
		if yopt.lname:
			return yopt.lname
		else:
			return yopt.sname

def opt_sname(yopt):
	return "%s_yopts.%s" % (yname, opt_cname(yopt))

#
# Generate the .h file
#

yinfile = open("yopts.h.in")
yincode = yinfile.read()
yincode = yincode.replace("${PROJ}", yname)

# Generate the yopts structure
yopt_str = ""
for yopt in yopts:
	yopt_str += "%s %s;\n\t" % (ctypes[yopt.atype], opt_cname(yopt))
	# For non ints with choice generate numerical constants
	# for faster comparisons in the code
	if len(yopt.choice) & (yopt.atype != typ_integer):
		yopt_str += "%s %s_code;\n\t" % (ctypes[typ_integer], opt_cname(yopt))

yincode = yincode.replace("${STRUCTURE}", yopt_str)

# Generate constants for choice-d options and arguments
yopt_str = ""
for yopt in yopts:
	if not len(yopt.choice):
		continue

	yopt_str += "enum {\n";
	yopt_str += "\tYOPT_%s_DEFAULT,\n" %(opt_cname(yopt).upper())
	for ch in yopt.choice:
		ch.ccode = "YOPT_%s_%s" % (opt_cname(yopt).upper(), ch.val.upper().replace("-", "_"))
		yopt_str += "\t%s,\n" % ch.ccode
	yopt_str += "};\n\n"

yincode = yincode.replace("${CHOICES}", yopt_str)

# Commit the code into .h file
youtfile = open(yname + "_yopts.h", "w")
youtfile.write(yincode)
yinfile.close()
youtfile.close()

#
# Generate the .c file
#

# Get the template in
yinfile = open("yopts.c.in")
yincode = yinfile.read()
yincode = yincode.replace("${PROJ}", yname)

# Generate and put short options array
yopt_str = ""
for yopt in yopts:
	if not getattr(yopt, "sname", None):
		continue

	yopt_str += yopt.sname
	if yopt.atype != typ_boolean:
		yopt_str += ":"

yincode = yincode.replace("${SOPTS}", yopt_str)

# Generate and put long options array
yopt_str = ""
sopt_rover = 50
for yopt in yopts:
	if yopt.otype != opt_option:
		continue
	if not getattr(yopt, "lname", None):
		continue

	if yopt_str:
		yopt_str += "\n\t\t"

	if yopt.atype != typ_boolean:
		yopt_rarg = "required_argument"
	else:
		yopt_rarg = "no_argument"

	if getattr(yopt, "sname", None):
		yopt_sopt = "'%s'" % yopt.sname
	else:
		yopt.sname_nr = sopt_rover
		sopt_rover += 1
		yopt_sopt = "%d" % yopt.sname_nr

	yopt_str += "{\"%s\", %s, 0, %s}," % (yopt.lname, yopt_rarg, yopt_sopt)

yincode = yincode.replace("${LOPTS}", yopt_str)

# Generate options assignment
yopt_str = ""
for yopt in yopts:
	if yopt.otype != opt_option:
		continue

	if yopt_str:
		yopt_str += "\n\t\t"

	if getattr(yopt, "sname", None):
		yopt_str += "case '%s':\n" % yopt.sname
	else:
		yopt_str += "case %d:\n" % yopt.sname_nr

	if yopt.atype == typ_boolean:
		yopt_assign = "true"
	elif yopt.atype == typ_string:
		yopt_assign = "optarg"
	elif yopt.atype == typ_integer:
		yopt_assign = "yopt_parse_int(optarg)"

	yopt_str += "\t\t\t%s = %s;\n" % (opt_sname(yopt), yopt_assign)
	yopt_str += "\t\t\tbreak;"

yincode = yincode.replace("${OPTS_ASSIGN}", yopt_str);

# Generate arguments (arg-s) parsing. The getopt_long puts leaves them at the end of argv array
yopt_str = ""
for yopt in yopts:
	if yopt.otype != opt_argument:
		continue

	yopt_str += "if (argc) {\n\t"
	yopt_str += "\t%s = *argv;\n\t" % opt_sname(yopt)
	yopt_str += "\tnext_arg();\n\t"

	if not getattr(yopt, "defval", None):
		yopt_str += "} else {\n\t"
		yopt_str += "\tprintf(\"No value for %s\\n\");\n\t" % opt_pname(yopt)
		yopt_str += "\tyopt_err = -1;\n\t"

	yopt_str += "}\n\t"

yincode = yincode.replace("${PARSE_ARGS}", yopt_str)

# Generate validation routine (choices)
yopt_str = ""
unknown_opt = "printf(\"Unknown %s value %s\\n\", %s);"
for yopt in yopts:
	if not len(yopt.choice):
		continue

	if yopt.atype == typ_string:
		for ch in yopt.choice:
			yopt_str += "if (!strcmp(%s, \"%s\")) {\n" % \
				     (opt_sname(yopt), ch.val)
			yopt_str += "\t\t%s_code = %s;\n" % (opt_sname(yopt), ch.ccode)
			yopt_str += "\t} else "

		yopt_str += "{\n\t\t" + unknown_opt % (opt_pname(yopt), "%s", opt_sname(yopt)) + "\n\t"
		yopt_str += "\tyopt_err = -1;\n\t}\n\n\t"
	elif yopt.atype == typ_integer:
		yopt_str += "switch (%s) {\n\t" % opt_sname(yopt)
		for ch in yopt.choice:
			yopt_str += "case %s:\n\t" % ch.val
		yopt_str += "\tbreak;\n\t"
		yopt_str += "default:\n\t"
		yopt_str += "\t" + unknown_opt % (opt_pname(yopt), "%d", opt_sname(yopt)) + "\n\t"
		yopt_str += "\tyopt_err = -1;\n\t"
		yopt_str += "\tbreak;\n\t"
		yopt_str += "}\n"

yincode = yincode.replace("${FIX_CHOICES}", yopt_str)

# Generate requirements checks (req_for-s)

def yoda_gen_one_cexp(exp):
	parts = exp.partition("=")
	for yopt in yopts:
		if yopt.lname == parts[0].strip():
			break;

	if yopt.atype == typ_boolean:
		fixup = ""
		comp = ""
		cval = ""
	elif (yopt.atype == typ_string) & len(yopt.choice):
		fixup = "_code"
		comp = "=="
		for ch in yopt.choice:
			if ch.val == parts[2].strip():
				cval = ch.ccode
				break
	elif yopt.atype == typ_integer:
		fixup = ""
		if parts[1]:
		  	comp = "=="
			cval = parts[2]
		else:
		  	comp = "!="
		  	cval = "0"
	else:
		assert(False) # FIXME

	return "%s%s %s %s" % (opt_sname(yopt), fixup, comp, cval)

def yoda_gen_cexpression(exp_str):
	exps = exp_str.partition("|")
	ret_str = yoda_gen_one_cexp(exps[0])
	if exps[1]:
		return ("(%s) || " % ret_str) + yoda_gen_cexpression(exps[2])
	else:
		return "(%s)" % ret_str

yopt_str = ""
for yopt in yopts:
	if not getattr(yopt, "required_for", None):
		continue

	yopt_str += "if (!%s && (%s)) {\n\t" % (opt_sname(yopt), yoda_gen_cexpression(yopt.required_for))
	yopt_str += "\tyopt_err = -1;\n\t"
	yopt_str += "\tprintf(\"Option %s required\\n\");\n\t" % opt_pname(yopt)
	yopt_str += "}\n\n\t"

yincode = yincode.replace("${CHECK_REQS}", yopt_str)

# Generate usage text
yopt_str = ""
yopt_align = "\t       "
yopt_indent = "     "
yopt_el = yopt_align + "\"\\n\"\n"

yopt_str += yopt_align + "\"" + yopt_indent + yname
if yopt_has_arg:
	yopt_str += " <%s>" % yopt_has_arg.lname
yopt_str += " [<options>]\\n\"\n"
yopt_str += yopt_el

# "Arguments" block
if yopt_has_arg:
	for yopt in yopts:
		if (yopt.otype != opt_argument):
			continue

		yopt_str += yopt_align + "\"%s: %s\\n\"\n" % (yopt.lname.capitalize(), yopt.summary)
		if len(yopt.choice) > 0:
			for ch in yopt.choice:
				yopt_str += yopt_align + "\"" + yopt_indent + \
					    ch.val.ljust(10 + yopt_name_len_max) + \
					    ch.summary + "\\n\"\n"

yopt_str += yopt_el

# "Options" block
yopt_str += yopt_align + "\"Options:\\n\"\n"
for yopt in yopts:
	if yopt.otype != opt_option:
		continue

	opts = set()
	if getattr(yopt, "sname", None):
		opts.add("-%s" % yopt.sname)
	if getattr(yopt, "lname", None):
		opts.add("--%s" % yopt.lname)

	yopt_sub_str = "|".join(opts)

	if yopt.atype == typ_integer:
		yopt_sub_str += " [NUM]"
	elif yopt.atype == typ_string:
		yopt_sub_str += " [STR]"

	yopt_str += yopt_align + "\"" + yopt_indent + \
		    yopt_sub_str.ljust(10 + yopt_name_len_max) + \
		    yopt.summary + "\\n\"" + "\n"

	if len(yopt.choice) > 0:
		for ch in yopt.choice:
			yopt_sub_str = "%s - %s" % (ch.val, ch.summary)
			yopt_str += yopt_align + "\"" + yopt_indent + \
				    "".ljust(10 + yopt_name_len_max) + \
				    yopt_indent + yopt_sub_str + "\\n\"\n"

yincode = yincode.replace("${USAGE}", yopt_str)

# Commit the code into .c file
youtfile = open(yname + "_yopts.c", "w")
youtfile.write(yincode)

yinfile.close()
youtfile.close()
