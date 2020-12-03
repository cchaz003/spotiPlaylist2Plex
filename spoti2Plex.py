import sys, os, spotipy, argparse
from signal import signal, SIGINT
from spotiLib import *
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from plexapi.myplex import MyPlexAccount


VERSION = "1.0"
spotifyID = 'YOUR SPOTIFY ID'
spotifySecret = 'YOUR SPOTIFY SECRET'

plexUsername = 'YOUR PLEX USERNAME'
plexPassword = 'YOUR PLEX PASSWORD'
plexServer = 'YOUR PLEX SERVER NAME'

fuzzyThreshold = 83









def clearLine():
	rows, columns = os.popen('stty size', 'r').read().split()
	print('\r' + ' '*int(columns), end='\r')


def clearWindow():
	rows, columns = os.popen('stty size', 'r').read().split()
	placeCursor(0,0)
	for row in range(int(rows)):
		print('\r' + ' '*int(columns))
	placeCursor(0,0)

def placeCursor(r, c):
	print('\033[' + str(r) + ';' + str(c) +'H')

def moveCursor (vert = 0, horiz = 0):

	# 	- Move the cursor up N lines:
	#   \033[<N>A
	if(vert > 0):
		print('\033[' + str(vert) + 'A')

	# 	- Move the cursor down N lines:
	#   \033[<N>B
	elif(vert < 0):
		print('\033[' + str(vert) + 'B')


	# 	- Move the cursor forward N columns:
	#   \033[<N>C
	if(horiz > 0):
		print('\033[' + str(horiz) + 'C')

	# 	- Move the cursor backward N columns:
	#   \033[<N>D
	elif(horiz < 0):
		print('\033[' + str(horiz) + 'D')


def parseID(plexID):
	itemType = plexID[:plexID.find(':')]
	itemID = plexID[plexID.find(':') + 1:]
	itemName = itemID[itemID.find(':')+1:]
	itemID = itemID[:itemID.find(':')]

	return {'type': itemType, 'id': itemID, 'name': itemName}

def plexSongLookup(plexLib, trackData, ignoreAlbum = False):
	artists = plexLib.search()
	foundArtist = None
	foundAlbum = None
	# print(artists[0].originalTitle)
	#find the artist
	for artist in artists:
		if(fuzz.partial_ratio(artist.title.lower(), trackData['artist'].lower()) > fuzzyThreshold):
				foundArtist = artist
				break

	#if we didnt find it before, try this other search where we lookup the song and match the artist
	if(foundArtist == None):
		lookup = plexLib.search(libtype = 'track', **{'track.title':trackData['trackTitle']})
		if(lookup != []):
			for track in lookup:
				if( (track.originalTitle != None and fuzz.partial_ratio(track.originalTitle.lower(), trackData['artist'].lower()) > fuzzyThreshold) or
					(track.originalTitle != None and fuzz.partial_ratio(track.originalTitle.lower(), trackData['albumArtist'].lower()) > fuzzyThreshold) or
					(track.grandparentTitle != None and fuzz.partial_ratio(track.grandparentTitle.lower(), trackData['artist'].lower()) > fuzzyThreshold) or
					(track.grandparentTitle != None and fuzz.partial_ratio(track.grandparentTitle.lower(), trackData['albumArtist'].lower()) > fuzzyThreshold)):
					return track


	#lookup song via the correct album
	if(ignoreAlbum == False):


		if(foundArtist != None):

			#find the correct album
			albums = foundArtist.albums()
			for album in albums:
				if(fuzz.partial_ratio(album.title.lower(), trackData['album'].lower()) > fuzzyThreshold):
					foundAlbum = album
					break

		#as long as the album has been found, find the song and return
		if(foundAlbum != None):
			for song in foundAlbum:
				if(fuzz.partial_ratio(song.title.lower(), trackData['trackTitle'].lower()) > fuzzyThreshold):
					return song


	#lookup without matching the song to the correct album (useful for singles that are on albums and vise versa)
	elif(foundArtist != None):
		for song in foundArtist.tracks():
			if(fuzz.partial_ratio(song.title.lower(), trackData['trackTitle'].lower()) > fuzzyThreshold):
					return song



def matchSongs(plexLib, trackList, ignoreAlbum = False):

	found = []
	notFound = []
	count = 0
	# clearWindow()
	#lookup songs from the spotify lib and match them with plex songs (separate found & not found tracks)
	for track in trackList:
		clearLine()
		print("Processing track " + str(count) + '/' + str(len(trackList)) + '  ' + track['trackTitle'])
		print("Matched Tracks: " + str(len(found)), end='\r')
		moveCursor(vert = 2)
		lookup = plexSongLookup(plexLib, track, ignoreAlbum)
		if(lookup != None):
			found += [lookup]
		else:
			notFound += [track]
		count+=1

	clearLine()
	print("Matched " + str(len(found)) + '/' + str(len(trackList)) + " tracks")
	print()

	#if there are tracks that we didnt find, let the user know and ask them if they want to re-check without matching album names
	if(len(notFound) > 0):
		showMissing = input('List missing tracks? (y/N): ')

		# print out the missing tracks
		if(showMissing.lower() == 'y'):
			print()
			for item in notFound:
				print(item['trackTitle'] + " By " + item['artist'] + ' on ' + item['album'])
			print()

		#assuming they have not already re-run the matching without albums, prompt for that and re-run if needed
		if(ignoreAlbum == False):
			checkNoAlbum = input("\nWould you like to re-lookup the unmatched songs without matching the album? (y/N): ")
			if(checkNoAlbum.lower() != 'y'):
				return [found, notFound]
			else:
				rematch = matchSongs(plexLib, notFound, ignoreAlbum = True)
				return [found + rematch[0], rematch[1]]

		#otherwise this execution of matchSongs has been done the matching without albums so return what we got
		else:
			return [found, notFound]

	#if everything was found, return without any extra prompts
	return [found, notFound]



def addToPlaylist(plexServer, trackList, libName, playlistName):
	matchedPlaylist = None
	# print(playlistName)
	
	for playlist in plexServer.playlists():
		if playlist.title == playlistName:
			print("Playlist already exists. Updating items in playlist")
			matchedPlaylist = playlist
			break
	# print(trackList)

	# print(type(matched))
	if matchedPlaylist == None:
		print("Playlist does not exist, creating new.")
		plexServer.createPlaylist(playlistName, trackList, libName)
		print("Created new playlist called '" + playlistName + "' with " + str(len(trackList)) + " tracks")
	else:
		uniqueSongs = []

		#first pass matches song IDs but this does not handle songs that are the same name but on a different album or something like that
		for song in trackList:
			if(song not in matchedPlaylist.items()):
				uniqueSongs += [song]

		#SO... we also match against the names of songs in the playlist
		for song in trackList:
			for playlistSong in matchedPlaylist.items():
				if (fuzz.partial_ratio(song.title.lower(), playlistSong.title.lower()) > 90 and song in uniqueSongs):
					del uniqueSongs[uniqueSongs.index(song)]

		if(len(uniqueSongs) > 0):
			matchedPlaylist.addItems(uniqueSongs)
			print("Added " + str(len(uniqueSongs)) + " songs to " + playlistName)

		else:
			print("No new songs to add. Playlist is unchanged.")

				



	# 


def makePlaylist(trackList, libName, playlistName):

	print("Matching songs from Spotify playlist with songs in Plex")
	account = MyPlexAccount(plexUsername, plexPassword)
	plex = account.resource(plexServer).connect()  # returns a PlexServer instance

	plexMusic = plex.library.section(libName)

	found, notFound = matchSongs(plexMusic, trackList)
	print()
	print("Generating Plex playlist from matched songs")
	addToPlaylist(plex, found, libName, playlistName)
	
	return notFound



def writeLinksToFile(filename, trackList):
	with open( filename, 'w') as file:
		for track in trackList:
			file.write(track['uri'] + '\n')



def main():
	print('\n')

	print(f"Welcome to the Spotify --> Plex playlist generator {VERSION}\n\n")
	print("Please wait while the session data is loaded from Spotify...")

	setClientData(spotifyID, spotifySecret)
	disableArtworkFetch()


	#parse the command line inputs
	parser = argparse.ArgumentParser(description='Spotify Recorder')
	parser.add_argument('-c','--compilation', action='store_true',
                    help='mark the item as a compilation and store the files in a single album folder rather than artist/album folders')
	parser.add_argument('-u','--url', metavar='<URL>', type=str, required = True,
                    help='spotify share url for a track, album, or playlist')
	parser.add_argument('-p','--playlist', metavar='<playlist>', type=str, required = True,
                    help='Name of Plex playlist to create (or update if it already exists)')
	parser.add_argument('-l','--library', metavar='<library>', type=str,
                    help='Name of Plex library to match against. If library is not specified, the default libray will be "Music"')
	args = parser.parse_args()



	account = MyPlexAccount(plexUsername, plexPassword)
	plex = account.resource(plexServer).connect()  # returns a PlexServer instance

	
	uri, uriType = processResource(args.url)
	rawData = getSpotifyRaw(uri)
	trackList = processSpotifyData(rawData, uriType)

	print("Spotify session loaded.")
	print()
	notFound = []
	if(args.library == None):
		notFound = makePlaylist(trackList, "Music", args.playlist)
	else:
		notFound = makePlaylist(trackList, args.library, args.playlist)


	print()
	print("Playlist import complete")
	print('\n\n\n')

	

def handler(signal_received, frame):
	# Handle any cleanup here
	print('\nSIGINT or CTRL-C detected. Exiting gracefully')
	print("Done.")
	exit(0)


if __name__ == '__main__':
	# Tell Python to run the handler() function when SIGINT is recieved
	signal(SIGINT, handler)

	#redirect logging to log_stream. Hides the LAME tagging crc errors on new files
	log_stream = io.StringIO()
	logging.basicConfig(stream=log_stream, level=logging.INFO)

	main()

