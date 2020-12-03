import sys, os, time, shutil, eyed3, spotipy, time, datetime, logging, io
from urllib.request import urlopen
from spotipy.oauth2 import SpotifyClientCredentials

clientID = ''
clientSecret = ''

IGNORE_ARTWORK = False

def setClientData(ID, secret):
	global clientID
	global clientSecret

	clientID = ID
	clientSecret = secret

def disableArtworkFetch():
	global IGNORE_ARTWORK
	IGNORE_ARTWORK = True

def enableArtworkFetch():
	global IGNORE_ARTWORK
	IGNORE_ARTWORK = False

def getArtwork(artworkURL):
	global IGNORE_ARTWORK

	if(not IGNORE_ARTWORK):
		artworkData = urlopen(artworkURL).read()
		return artworkData
	else:
		return ''


def newTrack():
	return {
	'uri': None,
	'artist': None,
	'album': None,
	'albumArtist': None,
	'trackTitle': None,
	'trackNumber': None,
	'diskNumber': None,
	'year': None,
	'artwork': None,
	'duration': None,
	'filenaming': None,
	'compilation': None,
	}


def parseSpotifyData(rawData, uriType):
	trackList = []


	if(uriType == 'track'):
		track = newTrack()
		track['uri'] = rawData['uri']
		track['artist'] = rawData['artists'][0]['name']
		track['album'] = rawData['album']['name']
		track['albumArtist'] = rawData['album']['artists'][0]['name']
		track['trackTitle'] = rawData['name']
		track['trackNumber'] = rawData['track_number']
		track['diskNumber'] = rawData['disc_number']
		track['year'] = rawData['album']['release_date'][:4]
		track['artwork'] = getArtwork(rawData['album']['images'][0]['url'])
		track['duration'] = str(int(rawData['duration_ms']) // 1000)
		trackList.append(track)


	elif(uriType == 'playlist'):
		for item in rawData:
			rawTrack = item['track']
			track = newTrack()
			track['uri'] = rawTrack['uri']
			track['artist'] = rawTrack['artists'][0]['name']
			track['album'] = rawTrack['album']['name']
			track['albumArtist'] = rawTrack['album']['artists'][0]['name']
			track['trackTitle'] = rawTrack['name']
			track['trackNumber'] = rawTrack['track_number']
			track['diskNumber'] = rawTrack['disc_number']
			track['year'] = rawTrack['album']['release_date'][:4]
			track['artwork'] = getArtwork(rawTrack['album']['images'][0]['url'])
			track['duration'] = str(int(rawTrack['duration_ms']) // 1000)
			trackList.append(track)


	elif(uriType == 'album'):
		artwork = getArtwork(rawData['images'][0]['url'])
		for rawTrack in rawData['tracks']['items']:
			track = newTrack()
			track['uri'] = rawTrack['uri']
			track['artist'] = rawTrack['artists'][0]['name']
			track['album'] = rawData['name']
			track['albumArtist'] = rawData['artists'][0]['name']
			track['trackTitle'] = rawTrack['name']
			track['trackNumber'] = rawTrack['track_number']
			track['diskNumber'] = rawTrack['disc_number']
			track['year'] = rawData['release_date'][:4]
			track['artwork'] = artwork
			track['duration'] = str(int(rawTrack['duration_ms']) // 1000)
			trackList.append(track)

	return trackList



def processSpotifyData(rawData, uriType, overrides = None):
	trackList = parseSpotifyData(rawData, uriType)
	if(overrides != None):
		for track in trackList:
			for override in overrides:
				if overrides[override] != None:
					track[override] = overrides[override]

	return trackList


def getPlaylistTracks(spotify,uri):
    results = spotify.playlist_tracks(uri)
    tracks = results['items']
    while results['next']:
        results = spotify.next(results)
        tracks.extend(results['items'])
    return tracks


def getSpotifyRaw(uri):
	global clientID
	global clientSecret
	# print("clientSecret: " + clientSecret)
	spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(clientID, clientSecret))


	#grab the raw data from spotify
	if(':playlist:' in uri):
		# print(getPlaylistTracks(uri))
		return getPlaylistTracks(spotify, uri)
		# return spotify.playlist_tracks(uri)['items']
	elif(':album:' in uri):
		# return spotify.album_tracks(uri)['items']
		return spotify.album(uri)
	elif(':track:' in uri):
		return spotify.track(uri)



'''
parses an ID (track, album, etc) from a given spotify "share" url

params:
	url: str - raw spotify url
	start: str - portion of the url that can be used as a marker for where to find the 
	length: int - expected size of the ID (seems to always be 22 but leaving this param because why not)

returns: str - parsed spotify ID string
'''
def getID(url, start, length):
	startIndex = url.find(start) + len(start)
	endIndex = startIndex + length
	return url[startIndex : endIndex]



def generateURN(urlStr, urlType):
	if urlType == 'playlist':
		return 'spotify:playlist:' + getID(urlStr, '/playlist/', 22)
	elif urlType == 'album':
		return 'spotify:album:' + getID(urlStr, '/album/', 22)
	elif urlType == 'track':
		return 'spotify:track:' + getID(urlStr, '/track/', 22)


def getURNType(urlStr):
	if 'playlist' in urlStr:
		return 'playlist'
	elif 'album' in urlStr:
		return 'album'
	elif 'track' in urlStr:
		return 'track'


def processResource(resourceStr):
	uriType = getURNType(resourceStr)

	#parse "share" url vs uri
	if('open.spotify.com' in resourceStr):
		uri = generateURN(resourceStr, uriType)
		return uri, uriType
	
	return resourceStr, uriType


def printTrack(trackData):
	temp = trackData.copy()
	temp['artwork'] = "THERE IS SOME ART"
	for item in temp:
		print(item + ': ' + str(temp[item]))
	# pprint(temp)


def calculateDuration(trackList):
	duration = 0
	for track in trackList:
		duration += int(track['duration'])
	return duration

def printETA(duration):
	#convert to seconds
	print("Duration: " + str(datetime.timedelta(seconds = duration)))

	t = datetime.datetime.now()
	t += datetime.timedelta(seconds=duration)

	print("ETA: " + t.strftime("%H:%M:%S"))

def supress_stdout():
    '''Supresses print statements until enable_stdOut() is called'''
    sys.stdout =  open(os.devnull, 'w')

def enable_stdOut():
    '''Restores stdout to the system default.  (To be called after supress_stdout)'''
    sys.stdout = sys.__stdout__
