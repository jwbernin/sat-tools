#!/usr/bin/python

import sys
import pprint
import json
import collections
from pyexcel_ods import save_data

from satellite import Satellite

errataWorkbook = collections.OrderedDict()
listOfHosts = {}
listOfErrata = {}

with open('credentials.json') as credentialfile:
  credentials = json.load(credentialfile)

s = Satellite(credentials['hostname'])
s.setUsername(credentials['username'])
s.setPassword(credentials['password'])
h=s.listHosts()
for host in h:
  errata = s.getHostErrata(str(host['id']))
  if len(errata) == 0:
    pass
  else:
    listOfHosts[host['name']] = host
    listOfHosts[host['name']]['errata'] = {}
    # print ("There are "+str(len(errata))+" errata available for host "+host['name'])
    # print ("They are:")
    for erratum in errata:
      erratumID = erratum['errata_id']
      if erratumID in listOfErrata:
        pass
      else:
        listOfErrata[erratumID] = erratum
      listOfHosts[host['name']]['errata'][erratumID] = erratum
      # print ("- Errata ID "+erratum['errata_id']+" with affected packages:")
      # for pkg in erratum['packages']:
        # print ("  - "+pkg)

sheet1 = {"Hosts Report":[]}
serverSheets = {}

for hostName in sorted(listOfHosts):
  hostErrata = listOfHosts[hostName]['errata']
  sheet1['Hosts Report'].append([hostName, len(listOfHosts[hostName]['errata'])])
  hostSheet = [["Errata Name", "Errata Type", "Number of packages"]]
  for errataName in sorted(hostErrata):
    errataInfo = hostErrata[errataName]
    hostSheet.append([errataName, errataInfo['type'], len(errataInfo['packages'])])
  errataWorkbook.update(sheet1)
  errataWorkbook.update({hostName:hostSheet})

for errataName in sorted(listOfErrata):
  errata = listOfErrata[errataName]
  errataID = errata['errata_id'].replace(":", "-")
  errataSheet = []
  errataSheet.append(["ID:", errata['errata_id']])
  errataSheet.append(["Name:", errata['name']])
  errataSheet.append(["Type:", errata['type']])
  errataSheet.append(["Affected packages:"])
  for pkg in errata['packages']:
    errataSheet.append(["",pkg])
  errataWorkbook.update({errataID:errataSheet})
  
save_data('erratainfo.ods', errataWorkbook)
#print (json.dumps(errataWorkbook))


