#!/usr/bin/python

import json
import sys
import requests

class Satellite(object):
  def __init__(self, host):
    self.sat_api = 'https://'+host+'/api/v2/'
    self.username = ''
    self.password = ''
    self.forceSSL = False
    self.session = requests.Session()

  def forceSSL(self, forceSSL=True):
    self.forceSSL = forceSSL

  def setUsername(self, username):
    self.username = username

  def setPassword(self, password):
    self.password = password

  def doGet(self, url):
    request = self.session.get(url, auth=(self.username, self.password))
    return request.json()

  def doPost(self, url, data={}):
    request = self.session.post(url, auth=(self.username, self.password), data=data)
    return request.json()

  def makeCall(self, location, data={}):
    if data == {}:
      return self.doGet(self.sat_api+location)
    else:
      return self.doPost(self.sat_api+location, data)

  def listHosts(self):
    results = self.makeCall('hosts')
    return results
