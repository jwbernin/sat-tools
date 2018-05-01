#!/usr/bin/python

import sys
import pprint
import json

from satellite import Satellite

with open('credentials.json') as credentialfile:
  credentials = json.load(credentialfile)


s = Satellite(credentials['hostname'])
s.setUsername(credentials['username'])
s.setPassword(credentials['password'])
#h=s.listHosts()
#pprint.pprint(h)
#s.setResultsMeta(True)
h=s.listHosts()
#pprint.pprint(h)
#sys.exit(0)
for host in h:
  errata = s.getHostErrata(str(host['id']))
  if len(errata) == 0:
    pass
  else:
    print ("There are "+str(len(errata))+" errata available for host "+host['name'])
    print ("They are:")
    for erratum in errata:
      print ("- Errata ID "+erratum['errata_id']+" with affected packages:")
      for pkg in erratum['packages']:
        print ("  - "+pkg)
