import os

#attempt to include spotipy library
try:
    import spotipy
    from spotipy.util import util
#prompt os to install spotipy if not already installed, and then attempt import again
except ImportError:
    os.system("pip install spotipy --upgrade")
    import spotipy
    import spotipy.util as util

#this will provide the basic user-welcoming information and collect the username
def welcome():
    os.system("clear") #clear console
    print("Welcome to The Spotify Clean Converter".center(80, "="))
    print("This program will clean out your spotify playlists, replacing \nexplicit tracks with clean versions of those tracks.\n")
    
    username = input("Enter your Spotify username to begin the authentication process: ")
    return username

#this will contain the authorization process for the user and return the client to operate with
def authorization(username):
    scope = "playlist-modify-public"
    client_id = "2217f534748a4da6be509284ce89c8ed"
    client_secret = "395d2f7d03624f068b5356665fbec49b"
    redirect_uri = "https://google.com/"
    
    # Spotify authentication
    token = util.prompt_for_user_token(username,scope,client_id,client_secret,redirect_uri)
    sp = spotipy.Spotify(auth=token)
    return sp

def locateSongs(sp, username):
    print("Choose a playlist to clean".center(80, "-"))
    to_clean = sp.user_playlist_tracks(username, listPlaylists(sp, username))
    songs = to_clean["items"]
    while to_clean["next"]:
        to_clean = sp.next(to_clean)
        songs.extend(to_clean["items"])
    songNames = []
    i = 0
    for song in songs:
        songNames.append({"name":song["track"]["name"]})
        songNames[i]['artist'] = song['track']['artists'][0]['name']
        songNames[i]['album'] = song['track']['album']['name']
        songNames[i]['albumUri'] = song['track']['album']['uri']
        i += 1
    return songNames

def listPlaylists(sp, username):
    print("\nSelect playlist: ")
    playlists = sp.current_user_playlists()
    order = 1
    for playlist in playlists['items']:
        print('\t' + str(order) + ". " + playlist['name'])
        order += 1
    choice = input("——> ")
    while ((not choice.isnumeric() or int(choice) == 0 or int(choice) > len(playlists['items'])) and choice != 'n'):
        print("Your input must be a valid number\n")
        choice = input("Enter the number corresponding to your desired playlist to be cleaned: ")
    if choice == 'n':
        return None;
    else:
        for i in range(len(playlists['items'])):
            if int(choice) - 1 is i: #returns the playlist id of the selected playlist
                return playlists['items'][i]['id']
        
def cleanSongs(sp, songNames):
    cleanSongids = []
    failures = 0
    print("Cleaning in progress".center(80, " "))
    for song in songNames:
        results = sp.search(q="track:"+song['name'],type='track',limit=20)
        itemNum = 0
        for cleaning in results["tracks"]["items"]:
            if cleaning["explicit"] == True:
                itemNum += 1
            elif cleaning["explicit"] == False:
                if cleaning['artists'][0]['name'] == song['artist']:
                    if cleaning['name'].lower() == song['name'].lower():
                        if cleaning['album']['name'] == song['album']:
                            break
                itemNum += 1
        if itemNum >= len(results['tracks']['items']):
                checkAlbum = albumCleanSearch(sp,song)
                if checkAlbum != None:
                    cleanSongids.append(albumCleanSearch(sp,song))
                else:
                    failures += 1   # keep track of failures
        else:
            cleanSongids.append(results['tracks']['items'][itemNum]['uri']) 
            
    return cleanSongids,failures
    
def albumCleanSearch(sp, song):
    results = sp.search(q="album:"+song['album'],type='album',limit=10)
    found = False
    if results['albums']['items'] == []:
        return None
    for album in results['albums']['items']:
        if album['uri'] != song['albumUri']:
            if album['name'] == song['album']:
                if album['artists'][0]['name'] == song['artist']:
                    break
    items = sp.album_tracks(album['uri'], limit=50, offset=0)
    trackNum = 0
    for track in items['items']:
        if track['artists'][0]['name'] == song['artist']:
            if track['name'].lower() == song['name'].lower():
                if track['explicit'] == False:
                    found = True
                    break
    if found:
        return track['uri']
    else:
        return None
    
def replaceSongs(sp, songs, username):
    print('Overwrite a playlist with the generated clean version or type \'n\' to create a new playlist.')
    playlist_id = listPlaylists(sp,username)
    if playlist_id == None:
        print('A new playlist titled "Cleaned by SpotifyCleanConverter" will be created'.center(80,' '),end='\n\n\n')
        new_playlist = sp.user_playlist_create(username, 'Cleaned by SpotifyCleanConverter', public=True)
        playlist_id = new_playlist['id']
    leftover = len(songs)
    if leftover >= 100:
        sp.user_playlist_replace_tracks(username, playlist_id, songs[0:99])
        for i in range(1, leftover // 100):
            if 99 + 100 * i <= leftover:
                sp.user_playlist_add_tracks(username, playlist_id, songs[100 * i: 99 + 100 * i])
        if leftover - (i * 100 + 99) != 0:
            sp.user_playlist_add_tracks(username, playlist_id, songs[i * 100 + 99:])
    else:
        sp.user_playlist_replace_tracks(username, playlist_id, songs)
    
def closing(failures):
    print("Congrats, your playlist has been successfully cleaned!".center(80, " "))
    print("There were a total of " + str(failures) + " tracks that did not have a clean version on Spotify, so they were not added.")
    print("Hope to see you again soon!".center(80, " "))
    
def main(sp, username):
    songNames = locateSongs(sp, username)
    cleanSongids,failures = cleanSongs(sp, songNames)
    replaceSongs(sp,cleanSongids,username)
    closing(failures)

if __name__=="__main__":
    username = welcome()
    main(authorization(username), username)
    
