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
        
def generateODS():
  printDBG(1, "Generating report in ODS format")
  sheet1 = {"Hosts Report":[]}
  sheet1['Hosts Report'].append(["Host Name", "IP Address", "Lifecycle Environment", 
      "Content View", "Security errata count", "Bugfix errata count", 
      "Enhancement errata count", "Upgradeable package count",
      "Subscription status", "Last boot time"])
  for key in hostObjects.keys():
    hostItem = hostObjects[key]
    sheet1['Hosts Report'].append([key, hostItem['ip'], hostItem['lifecycleEnvironment'],
        hostItem['contentView'], hostItem['secErrata'], hostItem['bugErrata'],
        hostItem['enhErrata'], hostItem['pkgUpdates'], hostItem['subStatus'],
        hostItem['uptime']])
  printDBG(2, "Saving host report")
  hostWorkbook.update(sheet1)
  save_data('basicHostInfo.ods', hostWorkbook)

  
def generateXLSX():
  pass
  
def generateCSV():
  f = open('basicHostInfo.csv', 'w')
  f.write("Host name,IP Address,Lifecycle Environment,Content View,# security errata,# bugfix errata,# enhancement errata,# upgradeable packages,Subscription status\n")
  for key in hostObjects.keys():
    host = hostObjects[key]
    pprint.pprint(host)
    f.write(','.join([key, host['ip'], host['lifecycleEnvironment'], host['contentView'], host['secErrata'], host['bugErrata'], host['enhErrata'], host['pkgUpdates'], host['subStatus']]))
    f.write('\n')
  f.close()
  printDBG(2, "Done writing CSV file")      
    
if __name__ == '__main__':
  collectData()
  pprint.pprint(hostObjects)
  if args.outfmt == 'ods':
    generateODS()
  elif args.outfmt == 'xlsx':
    generateXLSX()
  elif args.outfmt == 'csv':
    generateCSV()
    