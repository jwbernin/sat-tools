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
listOfHosts = []

def printDBG(level, message):
  if level>args.debug:
    return
  print(message)
  
with open('credentials.json') as credentialfile:
  credentials = json.load(credentialfile)
printDBG(3, "Satellite credentials loaded.")

def collectData():
  hostItem = {}
  printDBG(1, "Collecting data from Satellite")
  s = Satellite(credentials['hostname'])
  s.setUsername(credentials['username'])
  s.setPassword(credentials['password'])
  h=s.listHosts()
  for host in h:
    hostItem['name']=host['name']
    hostItem['subs']=[]
    subItems=s.getHostSubscriptions(str(host['id']))
    if ( type(None) == type (subItems) ) :
      continue
    for item in subItems:
      si={}
      if ( item['name'] in [ 'EPEL', 'FPLInternal' ] ):
        continue
      si['accountNum'] = item['account_number']
      si['contractNum'] = item['contract_number']
      si['endDate'] = item['end_date']
      si['name'] = item['name']
      hostItem['subs'].append(si)
    listOfHosts.append(hostItem)
  import pprint
  pprint.pprint(listOfHosts)

## REDO OUPUT

def generateODS():
  printDBG(1, "Generating report in ODS format")
  sheet1 = {"Hosts Report":[]}
  
  printDBG(2, "Generating host sheets")
  for hostName in sorted(listOfHosts):
    hostErrata = listOfHosts[hostName]['errata']
    sheet1['Hosts Report'].append([hostName, len(listOfHosts[hostName]['errata']), 'REBOOT' if listOfHosts[hostName]['errata_reboot_suggested'] else '' ])
    hostSheet = [["Errata Name", "Errata Type", "Number of packages"]]
    for errataName in sorted(hostErrata):
      errataInfo = hostErrata[errataName]
      hostSheet.append([errataName, errataInfo['type'], len(errataInfo['packages']), 'REBOOT' if errataInfo['reboot_suggested'] else ''])
    errataWorkbook.update(sheet1)
    errataWorkbook.update({hostName:hostSheet})
  
  printDBG(2, "Generating errata sheets")
  for errataName in sorted(listOfErrata):
    errata = listOfErrata[errataName]
    errataID = errata['errata_id'].replace(":", "-")
    errataSheet = []
    errataSheet.append(["ID:", errata['errata_id']])
    errataSheet.append(["Name:", errata['name']])
    errataSheet.append(["Type:", errata['type']])
    errataSheet.append(["Reboot Suggested:", 'YES' if errata['reboot_suggested'] else 'NO'])
    errataSheet.append(["Affected packages:"])
    for pkg in errata['packages']:
      errataSheet.append(["",pkg])
    errataWorkbook.update({errataID:errataSheet})
    
  printDBG(2, "Saving workbook")
  save_data('erratainfo.ods', errataWorkbook)

def generateXLSX():
  printDBG(1, "Generating report in XLSX format")
  workbook = xlsxwriter.Workbook('errataByHost.xlsx')
  topSheet = workbook.add_worksheet('Hosts Report')
  topSheetRow = 0
  
  printDBG(2, "Generating host sheets")
  for hostName in sorted(listOfHosts):
    hostErrata = listOfHosts[hostName]['errata']
    thisSheet = workbook.add_worksheet(hostName)
    thisSheet.write(0, 0, "Errata Name")
    thisSheet.write(0, 1, "Errata Type")
    thisSheet.write(0, 2, "Number of packages")
    topSheet.write(topSheetRow, 0, hostName)
    topSheet.write(topSheetRow, 1, len(listOfHosts[hostName]['errata']))
    topSheet.write(topSheetRow, 2, 'REBOOT' if listOfHosts[hostName]['errata_reboot_suggested'] else '')
    topSheetRow+=1
    hostSheetRow = 1
    for errataName in sorted(hostErrata):
      errataInfo = hostErrata[errataName]
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
