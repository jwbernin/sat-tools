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
    data = self.makeCall('/api/v2/hosts')
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

  def getSubscriptions(self):
    data = self.makeCall('/katello/api/subscriptions')
    return data        
    
        
