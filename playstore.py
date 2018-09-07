from bs4 import BeautifulSoup
from HTMLParser import HTMLParser
import pdb
import os
import re
import requests

playstoreLink = None

class MyHTMLParser(HTMLParser):
	def handle_starttag(self, tag, attrs):
		urlPath = None
		hasHref = False
		hasClickTarget = False
		if playstoreLink is None:
			if 'a' == tag:
				for attr in attrs:
					if 'card-click-target' == attr[1]:
						hasClickTarget = True
					if 'href' in attr:
						hasHref = True
						urlPath = attr[1]
					if hasHref and hasClickTarget:
						if 'song' in urlPath:
							global playstoreLink 
							playstoreLink = 'https://play.google.com' + urlPath

def getPlaystoreLink(song, artist):
	parser = MyHTMLParser()
	payload = (('q', artist + ' ' + song), ('c','music'), ('hl','en'))
	r = requests.get("https://play.google.com/store/search?", params=payload)
	parser.feed(r.text)
	print(playstoreLink)
	print('/store/music/album?id=' in r.text)