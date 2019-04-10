from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from HTMLParser import HTMLParser
import praw
import pdb
import re
import os
import requests
import soundcloud
import config
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

client_credentials_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

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

class CommentError(Exception):
	def __init__(self, expression, message):
		self.expression = expression
		self.message = message

if not os.path.isfile("post_replied_to.txt"):
	post_replied_to = []
else:
	with open("post_replied_to.txt", "r") as f:
		post_replied_to = f.read()
		post_replied_to = post_replied_to.split("\n")
		post_replied_to = list(filter(None, post_replied_to))

reddit = praw.Reddit('bot1')

def isValidSong(title):
	if ' - ' in title:
		return True
	else:
		return False

def splitTitle(title):
	splitTitle = title.split(' - ')
	return splitTitle

def formatTitle(title):
	newTitle = re.sub(r"\[.*?\]", "", title)
	newTitle = re.sub(r"\(.*?\)", "", newTitle)
	return newTitle

def isResultCorrect(search, result):
	formattedResult = formatTitle(result)
	if(fuzz.ratio(search, formattedResult) > 40):
		return True
	else: 
		return False

def findOnSpotify(song, artist):
	spotifyJSON = sp.search(q=song + ' ' + artist, limit=1)
	if (len(spotifyJSON['tracks']['items']) > 0):
		spotifyArtist = spotifyJSON['tracks']['items'][0]['artists'][0]['name']
		spotifySong = spotifyJSON['tracks']['items'][0]['name']
		if(isResultCorrect(song + artist, spotifySong + spotifyArtist)):
			return spotifyJSON['tracks']['items'][0]['external_urls']['spotify']
		else:
			return 'Could Not Find Track'
	else:
		return 'Could Not Find Track'

def findOniTunes(song, artist):
	payload = (('term', song + ' ' + artist), ('country', 'US'), ('media', 'music'), ('entity', 'musicTrack'), ('limit', '1'))
	r = requests.get("https://itunes.apple.com/search?", params=payload)
	iTunesJSON = r.json()
	if(len(iTunesJSON['results']) > 0):
		iTunesArtist = iTunesJSON['results'][0]['artistName']
		iTunesSong = iTunesJSON['results'][0]['trackName']
		if(isResultCorrect(song + artist, iTunesSong + iTunesArtist)):
			return iTunesJSON['results'][0]['trackViewUrl']
		else:
			return 'Could Not Find Track'
	else:
		return 'Could Not Find Track'

def findOnYoutube(song, artist):
	payload = (('key', config.YOUTUBE_API_KEY), ('part', 'snippet' ), ('q', song + ' ' + artist), ('type', 'video'), ('topicId', '/m/04rlf'), ('maxResults', '1'))
	r = requests.get("https://www.googleapis.com/youtube/v3/search", params=payload)
	youtubeJSON = r.json()
	if(len(youtubeJSON['items']) > 0):
		youtubeResult = youtubeJSON['items'][0]['snippet']['title']
		if(isResultCorrect(song + artist, youtubeResult)):
			return "https://www.youtube.com/watch?v=" + youtubeJSON['items'][0]['id']['videoId']
		else:
			return 'Could Not Find Track'
	else:
		return 'Could Not Find Track'
	
def findOnYoutubeMusic(song, artist):
	payload = (('key', config.YOUTUBE_API_KEY), ('part', 'snippet' ), ('q', song + ' ' + artist), ('type', 'video'), ('topicId', '/m/04rlf'), ('maxResults', '1'))
	r = requests.get("https://www.googleapis.com/youtube/v3/search", params=payload)
	youtubeJSON = r.json()
	if(len(youtubeJSON['items']) > 0):
		youtubeResult = youtubeJSON['items'][0]['snippet']['title']
		if(isResultCorrect(song + artist, youtubeResult)):
			return "https://music.youtube.com/watch?v=" + youtubeJSON['items'][0]['id']['videoId']
		else:
			return 'Could Not Find Track'
	else:
		return 'Could Not Find Track'


def findOnGooglePlay(song, artist):
	parser = MyHTMLParser()
	payload = (('q', artist + ' ' + song), ('c','music'), ('hl','en'))
	r = requests.get("https://play.google.com/store/search?", params=payload)
	parser.feed(r.text)
	if playstoreLink is None:
		return 'Could Not Find Track'
	else:
		return playstoreLink

def findOnSoundCloud(song, artist):
	payload = (('client_id', config.SOUNDCLOUD_API_KEY),('q', song + ' ' + artist), ('limit', '1'))
	r = requests.get("https://api.soundcloud.com/tracks?", params=payload)
	soundcloudJSON = r.json()
	if(len(soundcloudJSON) > 0):
		soundcloudResult = soundcloudJSON[0]['title']
		if(isResultCorrect(song + artist, soundcloudResult) and not('cover' in soundcloudResult)):
			return soundcloudJSON[0]['permalink_url']
		else:
			return 'Could Not Find Track'
	else:
		return 'Could Not Find Track'

def findOnTidal(song, artist):
	payload = (('limit', '1'), ('query', song + ' ' + artist), ('countryCode', 'US'))
	r = requests.get("https://api.tidal.com/v1/search/tracks?", params=payload, headers={'X-Tidal-Token': 'wdgaB1CilGA-S_s2'})
	tidalJSON = r.json()
	if(len(tidalJSON['items']) > 0):
		tidalSong = tidalJSON['items'][0]['title']
		tidalArtist = tidalJSON['items'][0]['artist']['name']
		if(isResultCorrect(song + artist, tidalSong + ' ' + tidalArtist)):
			return tidalJSON['items'][0]['url']
		else:
			return 'Could Not Find Track'
	else:
		return 'Could Not Find Track'


def createComment(links):
	errors = 0
	comment = 'Beep Boop... I am a bot. I tried finding this song on other streaming platforms. Here is what I found \n\n'
	for index in range(len(links)):
		currentObject = links[index]
		currentKey = currentObject.keys()
		if 'Could Not Find Track' in currentObject[currentKey[0]]:
			comment += "I didn't find it on " + currentKey[0] + '\n\n'
			print("Didn't find " + currentKey[0] + '\n')
			errors+=1
		else:
			comment += "[" + currentKey[0] + "](" + currentObject[currentKey[0]] + ")\n\n"
	comment += "*If I've made a mistake please downvote me. I'll try better next time*\n"
	if(errors > 2):
		raise CommentError('Not enough', 'links')
	else:
		return comment
	

def writeCommentToSubreddit(subreddit):
	for submission in reddit.subreddit(subreddit).rising():
		links = []
		if submission.id not in post_replied_to:
			if not(submission.is_self):
				try:
					global playstoreLink
					playstoreLink = None
					parsedTitle = ''
					parsedTitle = formatTitle(submission.title)
					if isValidSong(parsedTitle):
						parsedTitle = splitTitle(parsedTitle)
						spotifyLink = findOnSpotify(parsedTitle[1], parsedTitle[0])
						iTunesLink = findOniTunes(parsedTitle[1], parsedTitle[0])
						youtubeLink = findOnYoutube(parsedTitle[1], parsedTitle[0])
						youtubeMusicLink = findOnYoutubeMusic(parsedTitle[1], parsedTitle[0])
						soundcloudLink = findOnSoundCloud(parsedTitle[1], parsedTitle[0])
						tidalLink = findOnTidal(parsedTitle[1], parsedTitle[0])
						googlePlayLink = findOnGooglePlay(parsedTitle[1], parsedTitle[0])
						links.append({'Spotify': spotifyLink})
						links.append({'iTunes': iTunesLink})
						links.append({'YouTube': youtubeLink})
						links.append({'Youtube Music': youtubeMusicLink})
						links.append({'Soundcloud': soundcloudLink})
						links.append({'Tidal': tidalLink})
						links.append({'Google Play': googlePlayLink})
						print(subreddit + ' Replying to ' + submission.title)
						try:
							print('Commented on post')
						except CommentError:
							print("Didn't comment")
				except Exception as message:
					print('The Error is: ')
					print message
					print('Some Error')

def deleteBadComments():
	for comment in reddit.user.me().comments.new(limit=25):
		if(comment.score < 1):
			comment.delete()

writeCommentToSubreddit('hiphopheads')
writeCommentToSubreddit('classicalmusic')
writeCommentToSubreddit('DnB')
writeCommentToSubreddit('DubStep')
writeCommentToSubreddit('electrohouse')
writeCommentToSubreddit('futurebeats')
writeCommentToSubreddit('idm')
writeCommentToSubreddit('Outrun')
writeCommentToSubreddit('DickgirlsRadio')
writeCommentToSubreddit('ModernRockMusic')
writeCommentToSubreddit('punk')
writeCommentToSubreddit('jazz')
writeCommentToSubreddit('indieheads')
writeCommentToSubreddit('OctobersVeryOwn')
writeCommentToSubreddit('trap')
writeCommentToSubreddit('listeningHeads')
writeCommentToSubreddit('BeatsNRhymes')

deleteBadComments()

with open("post_replied_to.txt", "w") as f:
	for post_id in post_replied_to:
		f.write(post_id + "\n")
