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
  printDBG(1, "Collecting data from Satellite")
  s = Satellite(credentials['hostname'])
  s.setUsername(credentials['username'])
  s.setPassword(credentials['password'])
  h=s.listHosts()
  for host in h:
    hostItem = {}
    hostItem['name']=host['name']
    hostItem['subs']=[]
    subItems=s.getHostSubscriptions(str(host['id']))
    if ( type(None) == type (subItems) ) :
      continue
    for item in subItems:
      si={}
      if ( 'name' not in item):
        continue
      if ( item['name'] in [ 'EPEL', 'FPLInternal' ] ):
        continue
      si['accountNum'] = item['account_number']
      si['contractNum'] = item['contract_number']
      si['endDate'] = item['end_date']
      si['name'] = item['name']
      hostItem['subs'].append(si)
    listOfHosts.append(hostItem)

## REDO OUPUT

def generateODS():
  printDBG(1, "Generating report in ODS format")
  sheet1 = {"Hosts Report":[]}
  
  sheet1['Hosts Report'].append(["HOSTNAME"])
  sheet1['Hosts Report'].append(["Account number", "Contract number", "End Date", "Subscription Name"])
  printDBG(2, "Generating host sheets")
  for host in sorted(listOfHosts):
    sheet1['Hosts Report'].append(["Host name "+host['name']])
    for sub in host['subs']:
      sheet1['Hosts Report'].append([ sub['accountNum'], sub['contractNum'], sub['endDate'], sub['name'] ] )
      errataWorkbook.update(sheet1)
    errataWorkbook.update(sheet1)
    
  printDBG(2, "Saving workbook")
  save_data('subscriptioninfo.ods', errataWorkbook)

def generateXLSX():
  printDBG(1, "Generating report in XLSX format")
  workbook = xlsxwriter.Workbook('subscriptioninfo.xlsx')
  topSheet = workbook.add_worksheet('Hosts Report')
  topSheetRow = 0
  
  printDBG(2, "Generating host sheets")
  for hostName in sorted(listOfHosts):
    topSheet.write(0, 0, "HOSTNAME")
    topSheet.write(1, 0, "Account Number")
    topSheet.write(1, 1, "Contract Number")
    topSheet.write(1, 2, "End date")
    topSheet.write(1, 3, "Subscription name")
    topSheetRow = 2
    for host in sorted(listOfHosts):
      topSheet.write(topSheetRow, 0, host['name'])
      topSheetRow+=1
      for sub in host['subs']:
        topSheet.write(topSheetRow, 0, sub['accountNum'])
        topSheet.write(topSheetRow, 1, sub['contractNum'])
        topSheet.write(topSheetRow, 2, sub['endDate'])
        topSheet.write(topSheetRow, 3, sub['name'])
        topSheetRow+=1
      
  printDBG(2, "Saving workbook")
  workbook.close()

if __name__ == '__main__':
  collectData()
  if args.outfmt == 'ods':
    generateODS()
  elif args.outfmt == 'xlsx':
    generateXLSX()
