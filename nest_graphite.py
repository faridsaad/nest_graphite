#!/usr/bin/python

# nest_to_graphite.py -- python script to interface with the Nest Thermostat
# and send obtained information to a graphite server
# by Farid Saad, faradio@gmail.com
#
# The hard work of interfacing with the Nest borrowed 
# from Scott M Baker's Python Nest interface: https://github.com/smbaker/pynest
#
#
# Licensing:
#    This is distributed unider the Creative Commons 3.0 Non-commecrial,
#    Attribution, Share-Alike license. You can use the code for noncommercial
#    purposes. You may NOT sell it. If you do use it, then you must make an
#    attribution to me (i.e. Include my name and thank me for the hours I spent
#    on this)
#
# Acknowledgements:
#    Scott Baker's pynest script does the hard work, which in turn acknowledges
#    Chris Burris's Siri Nest Proxy as being very helpful to learn the nest's
#    authentication and some bits of the protocol.

import urllib
import urllib2
import sys
import re
import socket
import time
import subprocess
import yaml

try:
   import json
except ImportError:
   try:
       import simplejson as json
   except ImportError:
       print "No json library available. I recommend installing either python-json"
       print "or simpejson."
       sys.exit(-1)

def is_number(v):
   try:
      float(v)
      return True
   except ValueError:
      return False

class Nest:
    def __init__(self, username, password, serial=None, index=0, units="F"):
        self.username = username
        self.password = password
        self.serial = serial
        self.units = units
        self.index = index

    def loads(self, res):
        if hasattr(json, "loads"):
            res = json.loads(res)
        else:
            res = json.read(res)
        return res

    def login(self):
        data = urllib.urlencode({"username": self.username, "password": self.password})

        req = urllib2.Request("https://home.nest.com/user/login",
                              data,
                              {"user-agent":"Nest/1.1.0.10 CFNetwork/548.0.4"})

        res = urllib2.urlopen(req).read()

        res = self.loads(res)

        self.transport_url = res["urls"]["transport_url"]
        self.access_token = res["access_token"]
        self.userid = res["userid"]

    def get_status(self):
        req = urllib2.Request(self.transport_url + "/v2/mobile/user." + self.userid,
                              headers={"user-agent":"Nest/1.1.0.10 CFNetwork/548.0.4",
                                       "Authorization":"Basic " + self.access_token,
                                       "X-nl-user-id": self.userid,
                                       "X-nl-protocol-version": "1"})

        res = urllib2.urlopen(req).read()

        res = self.loads(res)

        self.structure_id = res["structure"].keys()[0]

        if (self.serial is None):
            self.device_id = res["structure"][self.structure_id]["devices"][self.index]
            self.serial = self.device_id.split(".")[1]

        self.status = res


    def temp_conv(self, temp):
        if (self.units == "F"):
            return temp*1.8 + 32.0
        else:
            return temp

    def show_status(self):
        results = ""

        shared = self.status["shared"][self.serial]
        device = self.status["device"][self.serial]

        allvars = shared
        allvars.update(device)


        for k in sorted(allvars.keys()):
             results += k + ":" +  str(allvars[k]) + "\n"
        return results


def main():

    config = yaml.load(open('settings.cfg','r').read()) 

    n = Nest(config['user'], config['password'], config['serial'], config['index'], config['units'])
    n.login()
    n.get_status()

    data = n.show_status()

    #Open socket to graphite box
    s = socket.socket()
    s.connect((config['graphite_server'],config['graphite_port']))
    prefix = config['graphite_prefix']
    for line in data.split('\n'):
       match = re.split(':',line.rstrip(),maxsplit=1)
       if len(match)==2:
          label,value = match
          if (value == 'False'):
             value = 0
          if (value == 'True'):
             value = 1
          if is_number(value) and re.match("\w",label) is not None:
              if re.search("temp",label) is not None:
                  value = n.temp_conv(float(value))
              message = prefix + "." + label + " " + str(float(value)) + " " + str(int(time.time())) + "\n"
              #print message
              s.send(message)

    s.close()


if __name__=="__main__":
   main()
