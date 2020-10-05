# Playlist Preview

Quickly and passively listen through a Spotify playlist in <i>preview mode</i>.  Preview mode plays snippets at the start of the song, the climax of the song, and 
optionally at the end before moving onto the next song and doing the same.  

## Overview

The Python script requires your Spotify username and appropriate permissions to fetch your current playlist and change playback, authenticated through Spotify's secure 
authorization flow.  

The script uses Spotify's APIs to control playback but also to fetch the current song's audio analysis to find the segment of the song that is loudest on average.  This segment
is used in the preview.  

Preview mode stops when you pause playback or at the end of the playlist.  

This Python implementation takes advantage of the <a href='https://spotipy.readthedocs.io/'>`Spotipy`</a> client for interacting with Spotify's APIs.

Though not required, the intended flow is to use <a href='IFTTT.com'>IFTTT</a> to trigger an http request through a Google Assistant device.  This request will trigger a Google Cloud Platform <i>Cloud Function</i> to execute `main.py` and the `playlist_preview` function.  This let's us set a phrase such as "Hey Google, start playlist preview" to enter preview mode.

## Installation
Install the required libraries locally:

```pip install -r requirements.txt```

### Other Setup

#### Spotify side:
Go to <a href='developer.spotify.com'>developer.spotify.com</a> and sign up.  Create a web app and grab the Client ID and Client Secret.

[Maybe I'll deploy a server for this in the future to make this skippable.]

#### Local:
Set local env variables for Spotipy authentication using OAuth from the preview step.  Use a localhost redirect URL as well as your own Spotify username.  This could be a local 
env yaml file `.env.yml` making the next GCP steps easy:
```
SPOTIPY_CLIENT_ID: [...]
SPOTIPY_CLIENT_SECRET: [...]
SPOTIPY_REDIRECT_URI: http://localhost:8888/callback
USERNAME=[...]
```

At this point, you can simply run the script locally to begin preview mode:

```python main.py```

The first time, a prompt should open on your web browser to give the script the listed permissions.

---- Further steps are for voice activation ----
#### Google Cloud Platform:
Log in/Sign up for a GCP account at <a href='https://console.cloud.google.com/'>https://console.cloud.google.com/</a>.  Enable billing (you might have to pay a tiny amount to run Cloud Functions after a free trial!).  Find steps to install the gcloud CLI tools.  (I'll assume some user knowledge here as I don't recall all the steps.)

Deploy the `playlist_preview` function in `main.py` as a GCP Cloud Function:
```gcloud functions deploy playlist_preview --allow-unauthenticated --env-vars-file=.env.yaml --timeout=540s```

Note the httpsTrigger url.  Test it out with a Spotify Playlist running, visit that url.  The longest preview mode can run is 9 minutes, limited by max GCP Cloud Function runtime.  

#### IFTTT:
Visit <a href='ifttt.com'>ifttt.com</a> and sign up/log in.  `Create` --> `Applets`.  Click `If This` and search for Google Assistant --> `Say a simple phrase`.  Give your preferred phrase such as "Start playlist preview" that will act as a trigger.  Under the `url` put your GCP Cloud Function httpsTrigger url.  Use Method=POST.  

That should about do it!  Test it out by using your new phrase on a Google Assistant device such as a nest.  Your playback should switch into preview mode after about 5 seconds.  Simply stop playback to end preview mode.
