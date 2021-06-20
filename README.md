# SRB2 Map Corruptor
This program will randomly corrupt the linedef and/or sector tags and/or special values in a Doom-format map. I designed this for [Sonic Robo Blast 2](https://www.srb2.org), but it should at least in theory work with any iD Tech 1 game, though the results won't necessarily be as dramatic.

Note that this program is only compatible with WAD-format archives; there is currently no PK3 support.

## Usage

    python corruptor.py [option]... input.wad output.wad

* `-r seed`: Specifies a seed for the random number generator. If this is not specified, the script will not seed the RNG, and Python's default seed-generation behavior will take effect. The seed need not be numeric; any string should work.

* `-l probability`: Specifies the probability of randomizing a linedef's tag. All probability arguments, including this one, range from 0 to 1 inclusive, and default to 0 if not given.

* `-s probability`: Specifies the probability of randomizing a sector's tag.

* `-L probability`: Specifies the probability of randomizing a linedef's special value. Note that this can cause problems very quickly, so stick to low values if you use it at all.

* `-S probability`: Specifies the probability of randomizing a sector's special value.

* `-0 probability`: Specifies the probability of changing the tag of a linedef or sector whose tag is 0. This is only evaluated for linedefs/sectors that pass the `-l` or `-s` probability check, so the actual probability will be this multiplied by the argument to `-l` or `-s`.

* `-O probability`: Specifies the probability of changing the special of a linedef (not a sector) whose special is 0. Like -L, I recommend keeping this low if you use it at all, since it's likely to create lots of big FOF's that get in the way.
