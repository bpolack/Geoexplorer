from urllib.request import urlopen
from lxml import etree
from time import sleep
import json
import re

class FoursquareSearch():
   
   # SERVICE RULES
   service = {
      'authentication':{
         'REQUIRED'    : False
      },
      'response': {
         'MAX_RESULTS' : 30
      },
      'box': {
         'MAX_X_DISTANCE' : 280000,  # max width  in real m.
         'MAX_Y_DISTANCE' : 280000,  # max height in real m.
      }
   }

   keyword = None

   def __init__(self, keyword):
      self.keyword=keyword

   def search(self, box, logger):
      # Send request
      requester=FoursquareRequester(logger)
      location=str(box.center[0])+","+str(box.center[1])
      req= {'ne': box.NE,
            'sw': box.WS,
            'q' : self.keyword}
      response = requester.send_request(req, 0, 0)
      resp = ResponseParser(response, logger)
      logger.log_scan(str(box.bounds())+" : "+ str(resp.resultsN) +" results")
      
      # Get markers from response
      markers=[]
      for result in resp.results:
         markers.append(result[1])
         logger.log_result(result[0]+" : "+str(result[1]))

      return markers


# results: [ (Name, (lat, lng), Address, Country), .. ]
class ResponseParser():
   
   results  = None
   resultsN = 0

   # Returns status of response
   def __init__(self, response, logger):
      self.results = []
      root = etree.HTML(response)
      
      try:
         script  = root.find("body//script").text
         pattern = r"(fourSq.config.explore.response = {)(.*?)(};)"
         obj     = '{' + re.search(pattern, script).group(2) + '}'
      except ValueError:
         print("Could not locate script tag in response. Will log response to scan.")
         logger.log_scan("Response was: "+str(response))
      except:
         print("Could not parse response properly. Will log response to scan.")
         logger.log_scan("Response was: "+str(response))
         logger.log_scan("Script extracted from response: "+script) 
         

      for item in json.loads(obj)['groups'][0]['items']:
         venue    = item['venue']
         name     = venue['name']
         lat      = venue['location']['lat']
         lng      = venue['location']['lng']
         address  = venue['location']['address'] if 'address' in venue['location'] else ""
         country  = venue['location']['country'] if 'country' in venue['location'] else ""
         self.results.append((name, (lat, lng), address, country))
         self.resultsN+=1

      '''for venue in root.findall("body//div[@class='venueBlock']"):
         index   = venue.find(".//span[@class='venueIndex']").text
         name    = venue.find(".//div[@class='venueName']/a").text
         address = venue.find(".//div[@class='venueAddress']").text
         print(index, name, address)
      '''


class FoursquareRequester():
   
   logger = None

   # Returns status of response
   def __init__(self, logger):
      self.logger=logger

   def send_request(self, request, maxRetries, retryInterval):
      logger=self.logger
      
      ne = request['ne']
      sw = request['sw']
      q = request['q']

      retries = -1

      # Send the request
      url = "https://foursquare.com/explore?mode=url" +\
            "&ne=" + str(ne[0]) + "%2C" + str(ne[1]) +\
            "&sw=" + str(sw[0]) + "%2C" + str(sw[1]) +\
            "&q=" + q

      while (retries!=maxRetries):
         retries+=1
         try:
            return urlopen(url).read()
         except HTTPError:
            print("404: Is the link correct?")
            return None
         except URLError:
            print("Domain in URL doesn't exist")
            return None
         if (retries == maxRetries):
            print("Query limit exceeded for today. Scanning stopped.")
