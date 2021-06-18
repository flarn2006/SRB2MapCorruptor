#!/usr/bin/python3
import sys
import random
from getopt import getopt
import wad

linedef_special_pool = []
with open('linedefs.txt', 'r') as f:
	for line in f:
		line = line.strip()
		if line != '' and line[0] != '#':
			linedef_special_pool.append(int(line))

(opts, args) = getopt(sys.argv[1:], 'lsn:L:S:0:')

if len(args) != 2:
	print(f'Usage: {sys.argv[0]} [-ls] [-n seed] [-L probability] [-S probability] [-0 probability] input.wad output.wad', file=sys.stderr)
	print()
	print('  -l\t\trandomize linedef tags')
	print('  -s\t\trandomize sector tags')
	print('  -n\t\tspecify a seed for the random number generator')
	print("  -L\t\tspecify probability of randomizing a linedef's special")
	print("  -S\t\tspecify probability of randomizing a sector's special")
	print('  -0\t\tspecify probability of changing the tag of a linedef or sector with tag 0')
	print()
	print('All probabilities are zero by default. Specifying no options will make no changes (and is therefore pointless.)')

	exit(255)

input_filename = args[0]
output_filename = args[1]

def parse_probability_arg(arg: str) -> float:
	try:
		prob = float(arg)
	except ValueError:
		print(f'Cannot parse probability "{arg}" as a floating-point value.', file=sys.stderr)
		exit(255)
	if 0 <= prob <= 1:
		return prob
	else:
		print('Probability must be between 0 and 1, inclusive.', file=sys.stderr)
		exit(255)

def chance(probability: float) -> bool:
	if probability == 0:
		return False
	elif probability == 1:
		return True
	else:
		return random.uniform(0,1) < probability

opt_linedef_tags = ('-l', '') in opts
opt_sector_tags = ('-s', '') in opts
opt_applyto0_prob = 0.
opt_linedef_special_prob = 0.
opt_sector_special_prob = 0.
for (opt, arg) in opts:
	if opt == '-n':
		random.seed(arg)
	if opt == '-0':
		opt_applyto0_prob = parse_probability_arg(arg)
	elif opt == '-L':
		opt_linedef_special_prob = parse_probability_arg(arg)
	elif opt == '-S':
		opt_sector_special_prob = parse_probability_arg(arg)

try:
	lumps = wad.load(input_filename)
except FileNotFoundError:
	print(f'{sys.argv[0]}: {input_filename}: file not found', file=sys.stderr)
	exit(2)
except wad.WADError as ex:
	print(ex.args[0], file=sys.stderr)
	exit(1)

def tagslice_st(i: int) -> slice:  # Sector tag
	return slice(26*i+24, 26*i+26)
def tagslice_ss(i: int) -> slice:  # Sector special
	return slice(26*i+22, 26*i+24)
def tagslice_lt(i: int) -> slice:  # Linedef tag
	return slice(14*i+8, 14*i+10)
def tagslice_ls(i: int) -> slice:  # Linedef special
	return slice(14*i+6, 14*i+8)

# Find all used tags

tagpools = {}
tags = None
for (name, data) in lumps:
	if name[:3] == b'MAP' and len(name) == 5:
		tags = tagpools[name] = []
	elif tags is None:
		continue
	elif name == b'SECTORS':
		n_sectors = len(data) // 26
		for i in range(n_sectors):
			tag = int.from_bytes(data[tagslice_st(i)], 'little')
			if tag not in (0, 65535):
				tags.append(tag)
	elif name == b'LINEDEFS':
		n_lines = len(data) // 14
		for i in range(n_lines):
			tag = int.from_bytes(data[tagslice_lt(i)], 'little')
			if tag not in (0, 65535):
				tags.append(tag)

# Modify maps

for i in range(len(lumps)):
	(name, data) = lumps[i]
	if name[:3] == b'MAP' and len(name) == 5:
		print(f'Processing {name.decode("ascii")}...')
		tags = tagpools[name]
	elif tags is None:
		continue
	elif name == b'SECTORS':
		sectors = bytearray(data)
		n_sectors = len(data) // 26
		for j in range(n_sectors):
			if opt_sector_tags:
				if sectors[tagslice_st(j)] != b'\0\0' or chance(opt_applyto0_prob):
					sectors[tagslice_st(j)] = random.choice(tags).to_bytes(2, 'little')
			if chance(opt_sector_special_prob):
				sectors[tagslice_ss(j)] = random.randint(0, 65535).to_bytes(2, 'little')
		lumps[i] = (name, sectors)
	elif name == b'LINEDEFS':
		linedefs = bytearray(data)
		n_lines = len(data) // 14
		for j in range(n_lines):
			if opt_linedef_tags:
				current_tag = int.from_bytes(linedefs[tagslice_lt(j)], 'little', signed=False)
				current_special = int.from_bytes(linedefs[tagslice_ls(j)], 'little', signed=False)
				dont_touch_specials = (704, 705, 714, 715)
				if current_special not in dont_touch_specials and (current_tag != 0 or chance(opt_applyto0_prob)):
					linedefs[tagslice_lt(j)] = random.choice(tags).to_bytes(2, 'little')
			if chance(opt_linedef_special_prob):
				linedefs[tagslice_ls(j)] = random.choice(linedef_special_pool).to_bytes(2, 'little')
		lumps[i] = (name, linedefs)

wad.save(output_filename, lumps)
