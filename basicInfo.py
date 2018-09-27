#!/usr/bin/python

import json
import collections
from pyexcel_ods import save_data
import argparse
import xlsxwriter
from satellite import Satellite
import pprint
import os

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", help="Print debugging messages", action="count")
parser.add_argument("-o", "--outfmt", help="Output format", choices=['xlsx', 'ods', 'csv'], default='ods')

args = parser.parse_args()

hostWorkbook = collections.OrderedDict()
hostObjects = {}

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
  for name in h:
    hostDetail = s.getHost(name['id'])
    if hostDetail['ip'] == None:
      continue
    if not hostObjects.has_key(hostDetail['name']):
      hostObjects[hostDetail['name']] = {}
    hostName = hostDetail['name']
    printDBG(2, "Processing host %s" % (hostName,))
    hostObjects[hostName]['ip'] = hostDetail['ip']
    if hostDetail.has_key('content_facet_attributes'):
      hostObjects[hostName]['lifecycleEnvironment'] = hostDetail['content_facet_attributes']['lifecycle_environment_name']
      hostObjects[hostName]['contentView'] = hostDetail['content_facet_attributes']['content_view_name']
      hostObjects[hostName]['secErrata'] = str(hostDetail['content_facet_attributes']['errata_counts']['security'])
      hostObjects[hostName]['bugErrata'] = str(hostDetail['content_facet_attributes']['errata_counts']['bugfix'])
      hostObjects[hostName]['enhErrata'] = str(hostDetail['content_facet_attributes']['errata_counts']['enhancement'])
      hostObjects[hostName]['pkgUpdates'] = str(hostDetail['content_facet_attributes']['upgradable_package_count'])
    else:
      hostObjects[hostName]['lifecycleEnvironment'] = 'NO DATA'
      hostObjects[hostName]['contentView'] = 'NO DATA'
      hostObjects[hostName]['secErrata'] = 'NO DATA'
      hostObjects[hostName]['bugErrata'] = 'NO DATA'
      hostObjects[hostName]['enhErrata'] = 'NO DATA'
      hostObjects[hostName]['pkgUpdates'] = 'NO DATA'
    
    if hostDetail.has_key('subscription_status_label'):
      hostObjects[hostName]['subStatus'] = hostDetail['subscription_status_label']
    else:
      hostObjects[hostName]['subStatus'] = 'NO DATA'
    # Get uptime direct from host
    # Assumption: the user we are running as can SSH into all the boxes
    #   w/o a password.    
    cmd = "ssh root@"+hostName+" who -b"
    lastboot = os.popen(cmd).read()
    hostObjects[hostName]['uptime'] = ' '.join(lastboot.strip().split()[2:4])
    printDBG(2, lastboot)
    # Get last update time from host - not the same assumption as above applies
    cmd = "ssh root@"+hostName+" yum -q history"
    yumhist = os.popen(cmd).read()
    patchDate = ' '.join(yumhist.split('\n')[2].split()[5:6])
    hostObjects[hostName]['lastUpdate'] = patchDate

        
def generateODS():
  printDBG(1, "Generating report in ODS format")
  sheet1 = {"Hosts Report":[]}
  sheet1['Hosts Report'].append(["Host Name", "IP Address", "Lifecycle Environment", 
      "Content View", "Security errata count", "Bugfix errata count", 
      "Enhancement errata count", "Upgradeable package count",
      "Subscription status", "Last boot time", "Last package update time"])
  for key in hostObjects.keys():
    hostItem = hostObjects[key]
    sheet1['Hosts Report'].append([key, hostItem['ip'], hostItem['lifecycleEnvironment'],
        hostItem['contentView'], hostItem['secErrata'], hostItem['bugErrata'],
        hostItem['enhErrata'], hostItem['pkgUpdates'], hostItem['subStatus'],
        hostItem['uptime'], hostItem['lastUpdate']])
  printDBG(2, "Saving host report")
  hostWorkbook.update(sheet1)
  save_data('basicHostInfo.ods', hostWorkbook)

  
def generateXLSX():
  printDBG(1, 'Generating output in XLSX format')
  workbook = xlsxwriter.Workbook('basicHostInfo.xlsx')
  topSheet = workbook.add_worksheet('Hosts Report')
  sheetRow = 1;
  topSheet.write(0, 0, 'Host Name')
  topSheet.write(0, 1, 'IP Address')
  topSheet.write(0, 2, 'Lifecycle Environment')
  topSheet.write(0, 3, 'Content View')
  topSheet.write(0, 4, 'Security Errata count')
  topSheet.write(0, 5, 'Bugfix errata count')
  topSheet.write(0, 6, 'Enhancement errata count')
  topSheet.write(0, 7, 'Upgradeable package count')
  topSheet.write(0, 8, 'Subscription Status')
  topSheet.write(0, 9, 'Uptime')
  topSheet.write(0,10, 'Last Update')
  for key in hostObjects.keys():
    thisHost = hostObjects[key]
    topSheet.write(sheetRow, 0, key)
    topSheet.write(sheetRow, 1, thisHost['ip'])
    topSheet.write(sheetRow, 2, thisHost['lifecycleEnvironment'])
    topSheet.write(sheetRow, 3, thisHost['contentView'])
    topSheet.write(sheetRow, 4, thisHost['secErrata'])
    topSheet.write(sheetRow, 5, thisHost['bugErrata'])
    topSheet.write(sheetRow, 6, thisHost['enhErrata'])
    topSheet.write(sheetRow, 7, thisHost['pkgUpdates'])
    topSheet.write(sheetRow, 8, thisHost['subStatus'])
    topSheet.write(sheetRow, 9, thisHost['uptime'])
    topSheet.write(sheetRow,10, thisHost['lastUpdate'])
    sheetRow+=1
  printDBG(2, 'Saving XLSX workbook')
  workbook.close()
  
def generateCSV():
  f = open('basicHostInfo.csv', 'w')
  f.write("Host name,IP Address,Lifecycle Environment,Content View,# security errata,# bugfix errata,# enhancement errata,# upgradeable packages,Subscription status\n")
  for key in hostObjects.keys():
    host = hostObjects[key]
    f.write(','.join([key, host['ip'], host['lifecycleEnvironment'], host['contentView'], host['secErrata'], host['bugErrata'], host['enhErrata'], host['pkgUpdates'], host['subStatus'], host['lastUpdate']]))
    f.write('\n')
  f.close()
  printDBG(2, "Done writing CSV file")      
    
if __name__ == '__main__':
  collectData()
  if args.outfmt == 'ods':
    generateODS()
  elif args.outfmt == 'xlsx':
    generateXLSX()
  elif args.outfmt == 'csv':
    generateCSV()
    