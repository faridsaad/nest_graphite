nest_graphite
=============

Script to send information exposed by your Nest Thermostat to a Graphite server.

Based on the pynest.py script from Scott M Baker found at https://github.com/smbaker/pynest

Usage: 
- Set up a Graphite instance if you don't have one (http://graphite.wikidot.com/quickstart-guide)
- Edit settings.cfg with your nest and graphite server information
- Cron the script (to match your graphite storage schema). I run it every minute with no problems so far.
