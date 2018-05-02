#!/usr/bin/python

import sys
import pprint
import json
import collections
from pyexcel_ods import save_data

from satellite import Satellite

errataWorkbook = collections.OrderedDict()
listOfHostCollections = {}
listOfErrata = {}

with open('credentials.json') as credentialfile:
  credentials = json.load(credentialfile)


def collectData():
  s = Satellite(credentials['hostname'])
  s.setUsername(credentials['username'])
  s.setPassword(credentials['password'])
  hcs=s.listHostCollections()
  for hc in hcs:
    hcInfo = s.getHostCollection(hc['id'])
    hcInfo['errata'] = {}
    for id in hcInfo['host_ids']:
      errata = s.getHostErrata(str(id))
      for erratum in errata:
        erratumID = erratum['errata_id']
        if erratumID not in listOfErrata.keys():
          listOfErrata[erratumID] = erratum
        if erratumID not in hcInfo['errata'].keys():
          hcInfo['errata'][erratumID] = erratum
    if hcInfo['name'] not in listOfHostCollections.keys():
      listOfHostCollections[hcInfo['name']] = hcInfo

def generateODS():        
  topSheet = {"Host Collections Report":[]}
  serverSheets = {}
  
  for hcName in sorted(listOfHostCollections):
    hcErrata = listOfHostCollections[hcName]['errata']
    topSheet['Host Collections Report'].append([hcName, len(hcErrata)])
    hostSheet = [[ "Errata Name", "Errata Type", "Numer of packages" ]]
    for errataName in sorted(hcErrata):
      errataInfo = hcErrata[errataName]
      hostSheet.append([errataName, errataInfo['type'], len(errataInfo['packages'])])
    errataWorkbook.update(topSheet)
    errataWorkbook.update({hcName:hostSheet})
    
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
              
  save_data('erratacollectioninfo.ods', errataWorkbook)
              
if __name__ == '__main__':
  collectData()
  generateODS()

