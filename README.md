# qidi-plus4-configs
Derived from stew675's Beacon config, merged with factory QIDI Box config.

I'm running firmware v1.7.3, and a Beacon H v2.1.0.

Also included are configs from my other QIDI Plus 4 that doesn't have a Box installed.

Other things of note:
 * CPU Fan temp range is tweaked to make it less noisy. I upgraded my rear case fan to an 80mm whilst I was taking the back off the printer anyway.
 * Added Cold Unload macros if you need to force the QIDI Box to retract filaments (only do this if the filament has been cut from the hot-end) - you will need to include this in the `printer.cfg` if you want to add those macros in.
 * The Box and Beacon device IDs have to be updated if you use this. Search for "update for your machine" in `printer.cfg` and `box.cfg`
 * Do not increase the stock QIDI webcam resolution - you will have issues with the CPU slowing down and the printer will panic. Keep the webcam at default resolution, or replace it with a better webcam that doesn't use so much compute.
 * There's a tweak to let the nozzle cool for a bit - this was added in as a fix when I had a gcode failure when starting a print immediately after one finished - if you start a print and the printer seems to be idle for a while, this is why. It'll let itself cool a bit before it scans the bed again.
 * There's an optional manual tramming gcode file, if you need it.
 * I had to apply the patch to probe.py `wget -O /home/mks/klipper/klippy/extras/probe.py https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/bed-scanning-probes/Beacon3D/RevH-Normal/probe.py`
 * I've increased purge amount to 200mm (`G1 E200 F300`) as the 80mm seemed to not be enough - too much of the previous filament was still in the nozzle.
