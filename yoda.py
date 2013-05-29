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
		self.short_dups = []
		self.otype = otype
	pass

class ychoice:
	pass

# Read yoda file in

yfile = open(sys.argv[1])

yopts = []
yopt_name_len_max = 0

std_shorts = set(["v", "V", "h"])

def_for = None
def_req_for = None

def yopt_find_l(s):
	if not s:
		return None

	res = filter(lambda x: x.lname == s, yopts)
	if len(res):
		return res[0]
	else:
	 	return None

def yopt_find_s(s):
	res = filter(lambda x: getattr(x, "sname", None) == s, yopts)
	if len(res):
		return res[0]
	else:
	 	return None

def next_rover(rover):
	rover += 1
	while chr(rover).isalnum():
		rover += 1
	return rover

sopt_rover = next_rover(0)

for l in yfile:
	if (l.startswith("#")):
		continue

	ls = l.strip().split(None, 1)
	if (not ls):
		continue

	if (ls[0] == "option"):
		yopt = yoption(opt_option)
		ln = ls[1].split("/")

		yopt.lname = ln.pop(0)
		yex = yopt_find_l(yopt.lname)
		if yex:
			print "Duplicate option name %s\n" % yopt.lname
			assert(False)

		if len(ln):
			yopt.sname = ln.pop(0)
			yex = yopt_find_s(yopt.sname)
			if yex:
				yopt.short_dup = yex
				yex.short_dups.append(yopt)

			if yopt.sname in std_shorts:
				std_shorts.remove(yopt.sname)

		if len(ln):
			yopt.laliases = ln

		if not getattr(yopt, "sname", None):
			yopt.sname_nr = sopt_rover
			sopt_rover = next_rover(sopt_rover)

		if def_for:
			yopt.optional_for = def_for
		if def_req_for:
			yopt.required_for = def_req_for

		yopts.append(yopt)

		if (yopt_name_len_max < len(yopt.lname)):
			yopt_name_len_max = len(yopt.lname)
	elif (ls[0] == "arg"):
		yopt = yoption(opt_argument)

		yopt.lname = ls[1]

		yopts.append(yopt)
		if (yopt_name_len_max < len(yopt.lname)):
			yopt_name_len_max = len(yopt.lname)
	elif (ls[0] == "int"):
		yopt.atype = typ_integer
		if len(ls) == 2:
			yopt.summary = ls[1]
	elif (ls[0] == "bool"):
		yopt.atype = typ_boolean
		if len(ls) == 2:
			yopt.summary = ls[1]
	elif (ls[0] == "string"):
		yopt.atype = typ_string
		if len(ls) == 2:
			yopt.summary = ls[1]
		# else option is deprecated
	elif (ls[0] == "choice"):
		cs = ls[1].split(None, 1)
		yc = ychoice()
		css = cs[0].split("/")
		yc.val = css.pop(0)
		if len(css):
			yc.aliases = css
		if len(cs) > 1:
			yc.summary = cs[1]
		else:
			yc.summary = ""
		yopt.choice.append(yc)
	elif (ls[0] == "default"):
		yopt.defval = ls[1]
	elif (ls[0] == "req_for"):
		yopt.required_for = ls[1]
	elif (ls[0] == "for"):
		yopt.optional_for = ls[1]
	elif (ls[0] == "clash"):
	  	yopt.conflicts = ls[1]
	elif (ls[0] == "set"):
		ls = ls[1].split(None, 1)
		if ls[0] == "for":
			def_for = ls[1]
		elif ls[0] == "req_for":
			def_req_for = ls[1]
		else:
		 	print "Unknown set", ls[0]
	elif (ls[0] == "unset"):
		if ls[1] == "for":
			def_for = None
		elif ls[1] == "req_for":
			def_req_for = None
		else:
		 	print "Unknown unset", ls[0]
	else:
		print "Unknown keyword", ls[0]
		assert(False)

yfile.close()

# Add standart help option

yopt = yoption(opt_option)
yopt.lname = "help"
yopt.atype = typ_boolean
yopt.summary = "show help text"
if "h" in std_shorts:
	yopt.sname = "h"
else:
	yopt.sname_nr = sopt_rover
	sopt_rover = next_rover(sopt_rover)

yopts.append(yopt)

# Add version option

yopt = yoption(opt_option)
yopt.lname = "version"
yopt.atype = typ_boolean
yopt.summary = "show version"
if "v" in std_shorts:
	yopt.sname = "v"
elif "V" in std_shorts:
	yopt.sname = "V"
else:
	yopt.sname_nr = sopt_rover
	sopt_rover = next_rover(sopt_rover)

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

# Name of yopts struct member
def opt_cname(yopt):
	if yopt.lname:
		return yopt.lname.replace("-", "_")
	else:
		return "opt_" + yopt.sname

# Name of option when printed on a screen
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

# Name of variable (with struct name)
def opt_sname(yopt):
	return "%s_yopts.%s" % (yname, opt_cname(yopt))

# Name of variable (short version, for duplicates)
def opt_ssname(yopt):
	return "%s_yopts.%s" % (yname, yopt.sname)

def opt_need_dup_trick(yopt):
	for dup in yopt.short_dups:
		if dup.atype != yopt.atype:
			return True
	return False

def opt_deprecated(yopt):
	return not getattr(yopt, "summary", None)

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
	if len(yopt.choice) and (yopt.atype != typ_integer):
		yopt_str += "%s %s_code;\n\t" % (ctypes[typ_integer], opt_cname(yopt))
	yopt.need_dup_trick = opt_need_dup_trick(yopt)
	if yopt.need_dup_trick:
		yopt_str += "%s %s_optarg;\n\t" % (ctypes[typ_string], yopt.sname)

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
	if getattr(yopt, "short_dup", None):
		continue

	yopt_str += yopt.sname
	if yopt.need_dup_trick:
		yopt_str += "::"
	elif yopt.atype != typ_boolean:
		yopt_str += ":"

yincode = yincode.replace("${SOPTS}", yopt_str)

# Generate and put long options array

def opt_cassign(yopt):
	if getattr(yopt, "sname", None):
		return "'%s'" % yopt.sname
	else:
		return "%d" % yopt.sname_nr

yopt_str = ""
for yopt in yopts:
	if yopt.otype != opt_option:
		continue
	if not getattr(yopt, "lname", None):
		continue

	if yopt.atype != typ_boolean:
		yopt_rarg = "required_argument"
	else:
		yopt_rarg = "no_argument"

	yopt_sopt = opt_cassign(yopt)
	lnames = getattr(yopt, "laliases", [])
	lnames.insert(0, yopt.lname)

	for lname in lnames:
		if yopt_str:
			yopt_str += "\n\t\t"

		yopt_str += "{\"%s\", %s, 0, %s}," % (lname, yopt_rarg, yopt_sopt)

yincode = yincode.replace("${LOPTS}", yopt_str)

# Generate options assignment
yopt_str = ""
for yopt in yopts:
	if yopt.otype != opt_option:
		continue
	if getattr(yopt, "short_dup", None):
		continue

	if yopt_str:
		yopt_str += "\n\t\t"

	yopt_str += "case %s:\n" % opt_cassign(yopt)
	yopt_vassign = opt_sname(yopt)
	if yopt.need_dup_trick:
		yopt_assign = "optarg ? : (char *)-1" # This means that the option was at least specified
		yopt_vassign = opt_ssname(yopt) + "_optarg"
	elif yopt.atype == typ_boolean:
		yopt_assign = "true"
	elif yopt.atype == typ_string:
		yopt_assign = "optarg"
	elif yopt.atype == typ_integer:
		yopt_assign = "yopt_parse_int(optarg)"

	yopt_str += "\t\t\t%s = %s;\n" % (yopt_vassign, yopt_assign)
	if not yopt.need_dup_trick:
		for dup in yopt.short_dups:
			yopt_str += "\t\t\t%s = %s;\n" % (opt_sname(dup), yopt_assign)
	yopt_str += "\t\t\tbreak;"

yincode = yincode.replace("${OPTS_ASSIGN}", yopt_str);

# Generate arguments (arg-s) parsing. The getopt_long puts leaves them at the end of argv array
yopt_str = ""
for yopt in yopts:
	if yopt.otype != opt_argument:
		continue

	if yopt.atype == typ_string:
		arg_assign = "*argv"
	elif yopt.atype == typ_integer:
		arg_assign = "yopt_parse_int(*argv)"
	else:
		print "Wrong type for an argument\n"
		assert(False)

	yopt_str += "if (argc) {\n\t"
	yopt_str += "\t%s = %s;\n\t" % (opt_sname(yopt), arg_assign)
	yopt_str += "\tnext_arg();\n\t"

	if not getattr(yopt, "defval", None):
		yopt_str += "} else {\n\t"
		yopt_str += "\tyopt_print(\"No value for %s\\n\");\n\t" % opt_pname(yopt)
		yopt_str += "\tyopt_err = YOPTS_PARSE_ERR;\n\t"

	yopt_str += "}\n\t"

yincode = yincode.replace("${PARSE_ARGS}", yopt_str)

# Generate validation routine (choices)
yopt_str = ""
unknown_opt = "yopt_print(\"Unknown %s value %s\\n\", %s);"
for yopt in yopts:
	if not len(yopt.choice):
		continue

	if yopt.atype == typ_string:
		for ch in yopt.choice:
			yopt_str += "if (!strcmp(%s, \"%s\")" % (opt_sname(yopt), ch.val)
			if getattr(ch, "aliases", None):
				for al in ch.aliases:
					yopt_str += " || !strcmp(%s, \"%s\")" % (opt_sname(yopt), al)

			yopt_str += ") {\n"

			yopt_str += "\t\t%s_code = %s;\n" % (opt_sname(yopt), ch.ccode)
			yopt_str += "\t} else "

		yopt_str += "{\n\t\t" + unknown_opt % (opt_pname(yopt), "%s", opt_sname(yopt)) + "\n\t"
		yopt_str += "\tyopt_err = YOPTS_PARSE_ERR;\n\t}\n\n\t"
	elif yopt.atype == typ_integer:
		yopt_str += "switch (%s) {\n\t" % opt_sname(yopt)
		for ch in yopt.choice:
			yopt_str += "case %s:\n\t" % ch.val
		yopt_str += "\tbreak;\n\t"
		yopt_str += "default:\n\t"
		yopt_str += "\t" + unknown_opt % (opt_pname(yopt), "%d", opt_sname(yopt)) + "\n\t"
		yopt_str += "\tyopt_err = YOPTS_PARSE_ERR;\n\t"
		yopt_str += "\tbreak;\n\t"
		yopt_str += "}\n"

yincode = yincode.replace("${FIX_CHOICES}", yopt_str)

# Expressions generator

def yoda_gen_one_cexp(exp):
	parts = exp.partition("=")
	for yopt in yopts:
		if yopt.lname == parts[0].strip():
			break;

	if yopt.atype == typ_boolean:
		fixup = ""
		comp = ""
		cval = ""
	elif (yopt.atype == typ_string) and len(yopt.choice):
		fixup = "_code"
		comp = " == "
		for ch in yopt.choice:
			if ch.val == parts[2].strip():
				cval = ch.ccode
				break
		else:
			assert(False)
	elif yopt.atype == typ_integer:
		fixup = ""
		if parts[1]:
			comp = " == "
			cval = parts[2]
		else:
			comp = " != "
			cval = "0"
	else:
		print "No req check for %s\n" % opt_sname(yopt)
		assert(False) # FIXME

	return "%s%s%s%s" % (opt_sname(yopt), fixup, comp, cval)

def yoda_gen_cexpression(exp_str):
	exps = exp_str.partition("|")
	ret_str = yoda_gen_one_cexp(exps[0])
	if exps[1]:
		return ("(%s) || " % ret_str) + yoda_gen_cexpression(exps[2])
	else:
		return "(%s)" % ret_str

def yoda_get_group_desc(exp_str):
	gacts = {}
	exps = exp_str.split("|")
	for exp in exps:
		parts = map(lambda a: a.strip(), exp.split("="))

		if len(parts) == 1:
			parts = ['option', parts[0]]

		if not gacts.has_key(parts[0]):
			gacts[parts[0]] = []
		gacts[parts[0]].append(parts[1])

	gstr = ""
	for t in gacts:
		if gstr:
			gstr += " or "
		gstr += "for "
		gstr += " or ".join(gacts[t])
		gstr += " %s" % t
		if len(gacts[t]) > 1:
			gstr += "s"

	return gstr.capitalize()


# Generate dups fixups
yopt_str = ""

def gen_short_trick(dup, yopt, with_cexp):
	yopt_sub_str = ""
	if (with_cexp):
		yopt_sub_str = "if (%s) " % yoda_gen_cexpression(dup.optional_for)

	if dup.atype == typ_boolean:
		yopt_assign = "(%s_optarg == (char *)-1)"
	elif dup.atype == typ_integer:
		yopt_assign = "yopt_parse_int(%s_optarg)"
	elif dup.atype == typ_string:
		yopt_assign = "%s_optarg"

	yopt_assign %= opt_ssname(yopt)
	yopt_sub_str += "{\n\t\t%s = %s;\n\t}" % (opt_sname(dup), yopt_assign)
	if with_cexp:
		yopt_sub_str += " else "
	return yopt_sub_str


for yopt in yopts:
	if getattr(yopt, "short_dup", None):
		continue
	if not yopt.need_dup_trick:
		continue

	yopt.short_dups.append(yopt)
	last = None
	for dup in yopt.short_dups:
		if getattr(dup, "optional_for", None):
			yopt_str += gen_short_trick(dup, yopt, True)
		else:
			assert(not last)
			last = dup

	if last:
		yopt_str += gen_short_trick(last, yopt, False)

	yopt.short_dups.pop()


yincode = yincode.replace("${FIX_DUPS}", yopt_str)

# Generate requirements checks (req_for-s and clash-es)

yopt_str = ""
for yopt in yopts:
	if getattr(yopt, "required_for", None):
		yopt_str += "if (%s) {\n\t\t" % yoda_gen_cexpression(yopt.required_for)
		yopt_str += "if (!%s) {\n\t\t" % opt_sname(yopt)
		yopt_str += "\tyopt_err = YOPTS_PARSE_ERR;\n\t\t"
		yopt_str += "\tyopt_print(\"Option %s required\\n\");\n\t\t" % opt_pname(yopt)
		yopt_str += "}\n\t"
		if getattr(yopt, "optional_for", None):
			yopt_str += "} else "
		else:
			yopt_str += "}\n\n\t"

	if getattr(yopt, "optional_for", None):
		yopt_str += "if (%s && !(%s))\n\t" % (opt_sname(yopt), yoda_gen_cexpression(yopt.optional_for))
		yopt_str += "\tyopt_print(\"Option %s is useless\\n\");\n\n\t" % opt_pname(yopt)

	if getattr(yopt, "conflicts", None):
		yopt_str += "if (%s && (%s)) {\n\t\t" % (opt_sname(yopt), yoda_gen_cexpression(yopt.conflicts))
		yopt_str += "yopt_err = YOPTS_PARSE_ERR;\n\t\t"
		yopt_str += "yopt_print(\"Option %s conflict\\n\");\n\t" % opt_pname(yopt)
		yopt_str += "}\n\t"

yincode = yincode.replace("${CHECK_REQS}", yopt_str)

# Generate usage text
yopt_str = ""
yopt_align = "\t       "
yopt_indent = "     "
yopt_el = yopt_align + "\"\\n\"\n"

yopt_str += yopt_align + "\"" + yopt_indent + yname
for yopt in yopts:
	if yopt.otype != opt_argument:
		continue
	if opt_deprecated(yopt):
		continue

	yopt_str += " <%s>" % yopt.lname

yopt_str += " [<options>]\\n\"\n"
yopt_str += yopt_el

# "Arguments" block
for yopt in yopts:
	if (yopt.otype != opt_argument):
		continue
	if opt_deprecated(yopt):
		continue

	yopt_str += yopt_align + "\"%s: %s\\n\"\n" % (yopt.lname.capitalize(), yopt.summary)
	if len(yopt.choice) > 0:
		for ch in yopt.choice:
			yopt_str += yopt_align + "\"" + yopt_indent + \
				    ch.val.ljust(10 + yopt_name_len_max) + \
				    ch.summary + "\\n\"\n"
	yopt_str += yopt_el

# "Options" block
def yopt_argname(yopt, dflt):
	# Remove all but UPPERCASE letters
	s = filter(lambda x: x.isupper(), yopt.summary)
	return len(s) and s or dflt

yopt_str += yopt_align + "\"Options:\\n\"\n"

yopts_groups = {}
yopts_default = []
yopts_generic = []

# Classify options
for yopt in yopts:
	if yopt.otype != opt_option:
		continue
	if opt_deprecated(yopt):
		continue

	for_expr = []

	if getattr(yopt, "required_for", None):
		for_expr.append(yopt.required_for)
	if getattr(yopt, "optional_for", None):
		for_expr.append(yopt.optional_for)

	if not for_expr:
		yopts_generic.append(yopt)
		continue

	for_expr = " | ".join(for_expr)

	if yopts_groups.has_key(for_expr):
		yopts_groups[for_expr].append(yopt)
	else:
		yopts_groups[for_expr] = [yopt]

# convert dict to list and sort it
yopts_groups = map(lambda k: (k, yopts_groups[k]), yopts_groups)
yopts_groups.sort(lambda a, b: len(a[1]) < len(b[1]) and 1 or -1)

i = 0
ygroup_merge_thresh = 3
while i < len(yopts_groups):
	yopt = yopts_groups[i];
	if len(yopt[1]) >= ygroup_merge_thresh:
		i += 1
		continue
	# merge a group, which contains less than three options
	yopts_groups.remove(yopt)
	for g in yopts_groups:
		if set(yopt[0].split(" | ")).issubset(set(g[0].split(" | "))):
			g[1].extend(yopt[1])
			break
	else:
		yopts_default.extend(yopt[1])

yopts_groups = map(lambda k: (yoda_get_group_desc(k[0]), k[1]), yopts_groups)
yopts_groups.insert(0, ("Generic", yopts_generic))
yopts_groups.append(("Other", yopts_default))

for group in yopts_groups:
	yopt_str += yopt_align + "\"\\n\"\n"
	yopt_str += yopt_align + "\"* %s:\\n\"\n" % group[0]
	for yopt in group[1]:
		if yopt.otype != opt_option:
			continue

		delim = False
		if getattr(yopt, "sname", None):
			yopt_sub_str = "-%s" % yopt.sname
			delim = True
		else:
			yopt_sub_str = "  "
		if getattr(yopt, "lname", None):
			yopt_sub_str += (delim and ", " or "  ")
			yopt_sub_str += "--%s" % yopt.lname

		if yopt.atype == typ_integer:
			yopt_sub_str += " " + yopt_argname(yopt, "NUM")
		elif yopt.atype == typ_string:
			yopt_sub_str += " " + yopt_argname(yopt, "STR")

		yopt_str += yopt_align + "\"" + yopt_indent + \
			    yopt_sub_str.ljust(10 + yopt_name_len_max) + \
			    yopt.summary.lower() + "\\n\"" + "\n"

		if len(yopt.choice) > 0:
			for ch in yopt.choice:
				if len(ch.summary):
					yopt_sub_str = "%s - %s" % (ch.val, ch.summary)
				else:
					yopt_sub_str = "%s" % ch.val
				yopt_str += yopt_align + "\"" + yopt_indent + \
					    "".ljust(10 + yopt_name_len_max) + \
					    yopt_indent + yopt_sub_str + "\\n\"\n"

yincode = yincode.replace("${USAGE}", yopt_str)

# Commit the code into .c file
youtfile = open(yname + "_yopts.c", "w")
youtfile.write(yincode)

yinfile.close()
youtfile.close()
