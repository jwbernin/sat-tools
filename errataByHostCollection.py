#!/usr/bin/python


import json
import collections
from pyexcel_ods import save_data
import argparse
import xlsxwriter
from satellite import Satellite

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", help="Print debugging messages", action="count")
parser.add_argument("-o", "--outfmt", help="Output format", choices=['xlsx', 'ods'], default='ods')

args = parser.parse_args()

errataWorkbook = collections.OrderedDict()
listOfHostCollections = {}
listOfErrata = {}

def printDBG(level, message):
  if level>args.debug:
    return
  print(message)
              
with open('credentials.json') as credentialfile:
  credentials = json.load(credentialfile)
printDBG(3, "Satellite credentials loaded")

def collectData():
  printDBG(1, "Collecting data from Satellite")
  s = Satellite(credentials['hostname'])
  s.setUsername(credentials['username'])
  s.setPassword(credentials['password'])
  hcs=s.listHostCollections()
  for hc in hcs:
    printDBG(2, "Examining host collection "+hc['name'])
    hcInfo = s.getHostCollection(hc['id'])
    hcInfo['errata'] = {}
    hcInfo['errataRebootSuggested'] = False
    for hcID in hcInfo['host_ids']:
      printDBG(3, "Examining collection member host")
      errata = s.getHostErrata(str(hcID))
      for erratum in errata:
        hcInfo['errataRebootSuggested'] = hcInfo['errataRebootSuggested'] or erratum['reboot_suggested']
        erratumID = erratum['errata_id']
        if erratumID not in listOfErrata.keys():
          listOfErrata[erratumID] = erratum
        if erratumID not in hcInfo['errata'].keys():
          hcInfo['errata'][erratumID] = erratum
    if hcInfo['name'] not in listOfHostCollections.keys():
      listOfHostCollections[hcInfo['name']] = hcInfo

def generateODS():        
  topSheet = {"Host Collections Report":[]}
  
  for hcName in sorted(listOfHostCollections):
    hcErrata = listOfHostCollections[hcName]['errata']
    topSheet['Host Collections Report'].append([hcName, len(hcErrata), 'REBOOT' if listOfHostCollections[hcName]['errataRebootSuggested'] else '' ])
    hostSheet = [[ "Errata Name", "Errata Type", "Numer of packages", "Reboot Suggested?" ]]
    for errataName in sorted(hcErrata):
      errataInfo = hcErrata[errataName]
      hostSheet.append([errataName, errataInfo['type'], len(errataInfo['packages']), 'YES' if errataInfo['reboot_suggested'] else 'NO' ])
    errataWorkbook.update(topSheet)
    errataWorkbook.update({hcName:hostSheet})
    
  for errataName in sorted(listOfErrata):
    errata = listOfErrata[errataName]
    errataID = errata['errata_id'].replace(":", "-")
    errataSheet = []
    errataSheet.append(["ID:", errata['errata_id']])
    errataSheet.append(["Name:", errata['name']])
    errataSheet.append(["Type:", errata['type']])
    errataSheet.append(["Reboot Suggested?", 'YES' if errata['reboot_suggested'] else 'NO'])
    errataSheet.append(["Affected packages:"])
    for pkg in errata['packages']:
      errataSheet.append(["",pkg])
    errataWorkbook.update({errataID:errataSheet})
              
  save_data('erratacollectioninfo.ods', errataWorkbook)

def generateXLSX():
  printDBG(1, "Generating report in XLSX format")
  workbook = xlsxwriter.Workbook('errataByHostCollection.xlsx')
  topSheet = workbook.add_worksheet('Host Collections Report')
  topSheetRow = 0
  
  printDBG(2, "Generating host collection sheets")
  for hcName in sorted(listOfHostCollections):
    hcErrata = listOfHostCollections[hcName]['errata']
    thisSheet = workbook.add_worksheet(hcName)
    thisSheet.write(0, 0, "Errata Name")
    thisSheet.write(0, 1, "Errata Type")
    thisSheet.write(0, 2, "Number of packages")
    thisSheet.write(0, 3, "Reboot Suggested?")
    topSheet.write(topSheetRow, 0, hcName)
    topSheet.write(topSheetRow, 1, len(hcErrata))
    topSheet.write(topSheetRow, 2, 'REBOOT' if listOfHostCollections[hcName]['errataRebootSuggested'] else '')
    topSheetRow+=1
    hostSheetRow = 1
    for errataName in sorted(hcErrata):
      errataInfo = hcErrata[errataName]
      thisSheet.write(hostSheetRow, 0, errataName)
      thisSheet.write(hostSheetRow, 1, errataInfo['type'])
      thisSheet.write(hostSheetRow, 2, len(errataInfo['packages']))
      thisSheet.write(hostSheetRow, 3, 'REBOOT' if errataInfo['reboot_suggested'] else '')
      hostSheetRow+=1
        
  printDBG(2, "Generating errata sheets")
  for errataName in sorted(listOfErrata):
    errata = listOfErrata[errataName]
    errataID = errata['errata_id'].replace(":", "-")
    errataSheet = workbook.add_worksheet(errataID)
    errataSheet.write(0, 0, "ID:")
    errataSheet.write(0, 1, errata['errata_id'])
    errataSheet.write(1, 0, "Name:")
    errataSheet.write(1, 1, errata['name'])
    errataSheet.write(2, 0, "Type:")
    errataSheet.write(2, 1, errata['type'])
    errataSheet.write(3, 0, "Reboot suggested:")
    errataSheet.write(3, 1, 'YES' if errata['reboot_suggested'] else 'NO')
    errataSheet.write(4, 0, "Affected packages:")
    errataSheetRow = 5
    for pkg in errata['packages']:
      errataSheet.write(errataSheetRow, 1, pkg)
      errataSheetRow+=1
      
  printDBG(2, "Saving workbook")
  workbook.close()

              
if __name__ == '__main__':
  collectData()
  if args.outfmt == 'ods':
    generateODS()
  elif args.outfmt == 'xlsx':
    generateXLSX()