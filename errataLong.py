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
parser.add_argument("-o", "--outfmt", help="Output format", choices=['xlsx', 'ods'], default='ods')

args = parser.parse_args()

contentViewVersionsWorkbook = collections.OrderedDict()
cVVObjects = {}

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
  printDBG(2, "Getting all content view versions")
  
  cvvs = s.getCVVersions()
  for ver in cvvs['results']:
    name = ver['name']
    cVVObjects[name] = {}
    object = cVVObjects[name]
    object['id'] = ver['id']
    object['secErrata'] = ver['errata_counts']['security']
    object['bugErrata'] = ver['errata_counts']['bugfix']
    object['enhErrata'] = ver['errata_counts']['enhancement']
    object['created'] = ver['created_at']
    object['errata'] = {}
    printDBG(3, 'Getting errata for CV Ver '+name)
    errata = s.getCVVerErrata(object['id'])
    for erratum in errata['results']:
      eo = {}
      eo['id'] = erratum['id']
      eo['name'] = erratum['name']
      eo['type'] = erratum['type']
      eo['issued'] = erratum['issued']
      eo['cves'] = []
      for cve in erratum['cves']:
        eo['cves'].append(cve['cve_id'])
      object['errata'][erratum['errata_id']] = eo
        
def generateODS():
  printDBG(1, "Generating report in ODS format")
  sheet1 = {"CV Version Errata Report":[]}
  sheet1['CV Version Errata Report'].append(["Content View Name & Version", "Initial publication date","Security Errata", "Bugfix errata", "Enhancement errata", "Total Errata"])
  for name in cVVObjects.keys():
    cvv = cVVObjects[name]
    sheet1['CV Version Errata Report'].append([name, cvv['created'], 
                                               cvv['secErrata'], 
                                               cvv['bugErrata'], 
                                               cvv['enhErrata'], 
                                               cvv['secErrata']+cvv['bugErrata']+cvv['enhErrata']])
    cvvSheet = [["Errata Identifier", "Errata Name", "Type", "Issue date", "CVEs"]]
    list = []
    for ei in cvv['errata'].keys():
      eo = cvv['errata'][ei]
      list.append(ei)
      list.append(eo['name'])
      list.append(eo['type'])
      list.append(eo['issued'])
      list.append(','.join(eo['cves']))
      cvvSheet.append(list)
      list=[]
    contentViewVersionsWorkbook.update(sheet1)
    contentViewVersionsWorkbook.update({name.replace(':', '-'):cvvSheet})
  
  printDBG(2, "Saving CV errata report")
  save_data('CVVersionsErrata.ods', contentViewVersionsWorkbook)

  
def generateXLSX():
  print "XLSX OUTPUT NOT YET IMPLEMENTED"
  printDBG(1, 'Generating output in XLSX format')
  workbook = xlsxwriter.Workbook('basicHostInfo.xlsx')
  topSheet = workbook.add_worksheet('Hosts Report')
  printDBG(2, 'Saving XLSX workbook')
  workbook.close()
  
def generateCSV():
  f = open('basicHostInfo.csv', 'w')
  f.write("Host name,IP Address,Lifecycle Environment,Content View,# security errata,# bugfix errata,# enhancement errata,# upgradeable packages,Subscription status\n")
  for key in hostObjects.keys():
    host = hostObjects[key]
    f.write(','.join([key, host['ip'], host['lifecycleEnvironment'], host['contentView'], host['secErrata'], host['bugErrata'], host['enhErrata'], host['pkgUpdates'], host['subStatus']]))
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
    