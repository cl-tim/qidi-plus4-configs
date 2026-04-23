# qidi-plus4-configs
Derived from stew675's Beacon config, merged with factory QIDI Box config.

I'm running firmware v1.7.3, and a Beacon H v2.1.0

Other things of note:
 * CPU Fan temp range is tweaked to make it less noisy.
 * Added Cold Unload macros if you need to force the QIDI Box to retract filaments (only do this if the filament has been cut from the hot-end) - you will need to include this in the `printer.cfg` if you want to add those macros in.
 * The Box and Beacon device IDs have to be updated if you use this. Search for "update for your machine" in `printer.cfg` and `box.cfg`
 