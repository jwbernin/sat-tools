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
    object['cvID'] = ver['content_view_id']
    object['secErrata'] = ver['errata_counts']['security']
    object['bugErrata'] = ver['errata_counts']['bugfix']
    object['enhErrata'] = ver['errata_counts']['enhancement']
    if type(object['secErrata']) == type(None):
      object['secErrata'] = 0
    if type(object['bugErrata']) == type(None):
      object['bugErrata'] = 0
    if type(object['enhErrata']) == type(None):
      object['enhErrata'] = 0
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

  for revName in cVVObjects.keys().sort(reverse=True):
    print revName
        
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
  printDBG(1, 'Generating output in XLSX format')
  workbook = xlsxwriter.Workbook('CVVersionsErrata.xlsx')
  topSheet = workbook.add_worksheet('CV Version Errata Report')
  topSheet.write(0, 0, 'Content View Name & Version')
  topSheet.write(0, 1, 'Initial publication date')
  topSheet.write(0, 2, 'Security errata')
  topSheet.write(0, 3, 'Bugfix errata')
  topSheet.write(0, 4, 'Enhancement errata')
  topSheet.write(0, 5, 'Total errata')
  sheetRow = 1
  for name in cVVObjects.keys():
    cvv = cVVObjects[name]
    thisSheet = workbook.add_worksheet(name)
    thisSheet.write(0, 0, "Errata Identifier")
    thisSheet.write(0, 1, "Errata Name")
    thisSheet.write(0, 2, "Type")
    thisSheet.write(0, 3, "Issue date")
    thisSheet.write(0, 4, "CVEs")
    thisSheetRow = 1
    topSheet.write(sheetRow, 0, name)
    topSheet.write(sheetRow, 1, cvv['created'])
    topSheet.write(sheetRow, 2, cvv['secErrata'])
    topSheet.write(sheetRow, 3, cvv['bugErrata'])
    topSheet.write(sheetRow, 4, cvv['enhErrata'])
    topSheet.write(sheetRow, 5, cvv['secErrata']+cvv['bugErrata']+cvv['enhErrata'])
    for eID in cvv['errata'].keys():
      eo = cvv['errata'][eID]
      thisSheet.write(thisSheetRow, 0, eID)
      thisSheet.write(thisSheetRow, 1, eo['name'])
      thisSheet.write(thisSheetRow, 2, eo['type'])
      thisSheet.write(thisSheetRow, 3, eo['issued'])
      thisSheet.write(thisSheetRow, 4, ','.join(eo['cves']))
      thisSheetRow+=1
    sheetRow+=1
  
  printDBG(2, 'Saving XLSX workbook')
  workbook.close()
  
    
if __name__ == '__main__':
  collectData()
  if args.outfmt == 'ods':
    generateODS()
  elif args.outfmt == 'xlsx':
    generateXLSX()
    