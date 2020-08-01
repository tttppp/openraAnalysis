# OpenRA Analysis Python Script

A script to extract data from [OpenRA](https://openra.net) replay files.  In particular this was written to analyse
[RAGL](https://www.openra.net/news/ragl-announcement/) 1v1 matches and I've used this script to perform analysis of what
units are built the most and how they affect win rates:
* Comparison of Seasons 1-9: https://forum.openra.net/viewtopic.php?f=85&t=21224
* Season 9 Summary: https://forum.openra.net/viewtopic.php?p=311915#p311915

This is intended to work with Python 2 and 3, but if there's an error with one then try the other.

The tool uses the fingerprint endpoint at `https://forum.openra.net/openra/info/[fingerprint]` to try to group players by their forum id.
Earlier seasons of RAGL do not use this, so automated player identification is much harder.

## Alternatives

If you're interested in this then you might want to check out the following projects too:

### AMHOL's Ruby parser: https://github.com/AMHOL/openra-ruby

A tool to parse and extract data from replay files. This is reasonably comprehensive and works with many players and more than just the RA mod.

### dragunoff's visualisation tool for use with the output of the Ruby parser: https://dragunoff.github.io/OpenRA-replay-analytics/

A UI to produce easily digestible diagrams showing the build order with timing information.

### Netnazgul's C++ parser: https://github.com/netnazgul/openra-replay-parser

A tool to get some basic stats from the metadata at the end of the replay file, but using a UI.
