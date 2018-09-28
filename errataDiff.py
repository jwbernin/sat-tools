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
parser.add_argument("-i", "--initial", help="Baseline CVVID")
parser.add_argument("-f", "--final", help="Final CVVID")
args = parser.parse_args()

contentViewVersionsWorkbook = collections.OrderedDict()
finalList = []

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
  printDBG(2, "Getting initial (baseline) content view version errata")
  cvve1 = s.getCVVerErrata(args.initial)
  baselineErrata = cvve1['total']
  printDBG(2, "Getting target content view version errata")
  cvve2 = s.getCVVerErrata(args.final)
  targetErrata = cvve2['total']
  list1 = []
  for cve in cvve1['results']:
    list1.append(cve['id'])
  for cve in cvve2['results']:
    if cve['id'] not in list1:
      finalList.append(cve)
  if not len(finalList) == targetErrata-baselineErrata:
    printDBG(1, "Errata mis-count - length not equal to difference in sizes!")
  printDBG(2, "Data gathered, differential list processed")
  
def generateODS():
  printDBG(1, "Generating report in ODS format")
  sheet1 = {"CV Version Errata Differential Report":[]}
  sheet1['CV Version Errata Differential Report'].append(["Errata ID", 
         "Type", "Errata last modified", "Errata Title" ])
  for cve in finalList:
    sheet1['CV Version Errata Differential Report'].append([ cve['errata_id'],
           cve['type'], cve['updated'], cve['title'] ])
    name = cve['errata_id']
    cvvSheet=[]
    cvvSheet.append(['Errata ID', name])
    cvvSheet.append(['Type', cve['type']])
    cvvSheet.append(['Originally issued', cve['issued']])
    cvvSheet.append(['Last modified', cve['updated']])
    cvvSheet.append(['Description', cve['description']])
    cvvSheet.append(['CVEs'])
    for entry in cve['cves']:
      cvvSheet.append(['', entry['cve_id']])
    cvvSheet.append(['Packages affected'])
    for entry in cve['packages']:
      cvvSheet.append(['', entry])
    contentViewVersionsWorkbook.update(sheet1)
    contentViewVersionsWorkbook.update({name.replace(':', '-'):cvvSheet})
  
  printDBG(2, "Saving CV errata report")
  save_data('CVVersionsErrataDifferential.ods', contentViewVersionsWorkbook)

  
def generateXLSX():
  printDBG(1, 'Generating output in XLSX format')
  workbook = xlsxwriter.Workbook('CVVersionsErrataDiff.xlsx')
  topSheet = workbook.add_worksheet('CV Ver Errata Diff Report')
  topSheet.write(0, 0, "Errata ID")
  topSheet.write(0, 1, "Type")
  topSheet.write(0, 2, "Errata Last modified")
  topSheet.write(0, 3, "Errata Title")
  sheetRow = 1
  for cve in finalList:
    topSheet.write(sheetRow, 0, cve['errata_id'])
    topSheet.write(sheetRow, 1, cve['type'])
    topSheet.write(sheetRow, 2, cve['updated'])
    topSheet.write(sheetRow, 3, cve['title'])
    cveSheet = workbook.add_worksheet(cve['errata_id'].replace(':', '-'))
    cveSheetRow = 0
    cveSheet.write(0, 0, "Errata ID")
    cveSheet.write(0, 1, cve['errata_id'])
    cveSheet.write(1, 0, 'Type')
    cveSheet.write(1, 1, cve['type'])
    cveSheet.write(2, 0, 'Originally Issued')
    cveSheet.write(2, 1, cve['issued'])
    cveSheet.write(3, 0, "Last modified")
    cveSheet.write(3, 1, cve['updated'])
    cveSheet.write(4, 0, "Description")
    cveSheet.write(4, 1, cve['description'])
    cveSheet.write(5, 0, "CVEs")
    cveSheetRow=6
    for entry in cve['cves']:
      cveSheet.write(cveSheetRow, 1, entry['cve_id'])
      cveSheetRow+=1
    cveSheet.write(cveSheetRow, 0, 'Packages affected')
    cveSheetRow+=1
    for entry in cve['packages']:
      cveSheet.write(cveSheetRow, 1, entry)
      cveSheetRow+=1
    sheetRow+=1
    
  printDBG(2, 'Saving XLSX workbook')
  workbook.close()
  
def usage():
  print "Incorrect parameters. Please use -h for parameter specification"
  
def verifyParams():
  if type(args.initial) == type(None):
    usage()
    sys.exit(0)
  if type(args.final) == type(None):
    usage()
    sys.exit(0)
    
if __name__ == '__main__':
  verifyParams()
  collectData()
  if args.outfmt == 'ods':
    generateODS()
  elif args.outfmt == 'xlsx':
    generateXLSX()
    