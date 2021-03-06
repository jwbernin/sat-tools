#!/usr/bin/python

import json
import sys
import requests
import pprint
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Satellite(object):
  def __init__(self, host):
    self.sat_api = 'https://'+host
    self.username = ''
    self.password = ''
    self.forceSSL = False
    self.session = requests.Session()
    self.showResultsMeta = False

  def forceSSL(self, forceSSL=True):
    self.forceSSL = forceSSL

  def setUsername(self, username):
    self.username = username

  def setPassword(self, password):
    self.password = password

  def setResultsMeta(self, resultsMeta = False):
    self.showResultsMeta = resultsMeta

  def doGet(self, url):
    request = self.session.get(url, auth=(self.username, self.password), verify=False)
    if request.status_code != 200:
      pprint.pprint(request.text)
      print (request.url)
      return None
    return request.json()

  def doPost(self, url, data={}):
    request = self.session.post(url, auth=(self.username, self.password), data=data, verify=False)
    return request.json()

  def makeCall(self, location, data={}):
    if data == {}:
      return self.doGet(self.sat_api+location)
    else:
      return self.doPost(self.sat_api+location, data)

  def listHosts(self):
    data = self.makeCall('/api/v2/hosts?per_page=50000')
    if self.showResultsMeta:
      return data
    else:
      return data['results']

  def getHostErrata(self, hostID):
    location='/api/v2/hosts/'+hostID+'/errata'
    data = self.makeCall(location)
    if self.showResultsMeta:
      return data
    else:
      return data['results']

  def listHostCollections(self):
    data = self.makeCall('/katello/api/host_collections')
    if self.showResultsMeta:
      return data
    else:
      return data['results']

  def getHostCollection(self, id):
    data = self.makeCall('/katello/api/host_collections/'+str(id))
    return data

  def getHost(self, id):
    data = self.makeCall('/api/v2/hosts/'+str(id))
    return data

  def getSubscriptions(self, searchString):
    if searchString:
      data = self.makeCall('/katello/api/subscriptions?search='+searchString)
    else:
      data = self.makeCall('/katello/api/subscriptions')
    return data        
    
  def getCVHistory(self, cvID):
    data = self.makeCall('/katello/api/content_views/'+str(cvID)+'/history')
    return data

  def getErrata(self):
    data = self.makeCall('/katello/api/errata')
    return data  
    
  def getCVVersions(self):
    data = self.makeCall('/katello/api/content_view_versions')
    return data
    
  def getCVVer(self, id):
    data = self.makeCall('/katello/api/content_view_versions/'+str(id))
    return data
    
  def getHostSubscriptions(self, id):
    data = self.makeCall('/api/v2/hosts/'+str(id)+'/subscriptions')
    if ( type(None) == type(data) ):
      return None
    if self.showResultsMeta:
      return data
    else:
      return data['results']

  # THIS CALL IS NOT DOCUMENTED IN THE API DOC!!
  def getCVVerErrata(self, cvVerID):
    data = self.makeCall('/katello/api/v2/errata?content_view_version_id='+str(cvVerID)+'&per_page=50000')
    return data
