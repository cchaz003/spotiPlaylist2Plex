# spotiPlaylist2Plex
A script to match spotify playlists with songs in your Plex library to create Plex Playlists


I made this script out of my own necessity. Plex is notorious for poor music management so I often rely upon Spotify for playlist management but I have better quality tracks on Plex. This script will take a spotify playlist url (or uri) and will attempt to match them up with tracks in your Plex library to build a playlist from. It's not perfect and sometimes doesnt match or matches incorrectly but it has already saved me a bunch of time manually syncing Spotify playlists to Plex (or just creating playlists in Plex for that matter). Anyways, it's here for anyone else who finds themselves wanting this sort of playlist sync feature. 

In order to use this script you will need to sign up for a Spotify developer account. This will allow you to generate the unique __*Spotify ID*__ and __*Spotify Secret*__ that are required by their API. You will also need your Plex __*username*__, __*password*__, and __*server name*__.

**The 5 pieces of data above will need to be entered into the spoti2plex.py file before it will work**

Example usage:
```
python3 spoti2Plex.py -u "SPOTIFY PLAYLIST URL/URI" -p "PLEX PLAYLIST NAME"
```
