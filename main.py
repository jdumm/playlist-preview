import shutil
from time import sleep
import os

import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def get_initial_volume(sp):
    """Find current volume in active device
       params:
         sp = Spotify API Client to get input device volume
    """
    devs = sp.devices()
    vol = 0
    for device in devs['devices']:
        if device['is_active']:
            vol = device['volume_percent']
    return vol


def fade(sp_client, max_vol=50, fade_out=True, fade_time=2.):
    """Fade in/out from the current volume
       params:
         max_vol = the initial volume before any fading
         fade_out = True to decrease volume to 0 else volume increases from 0 to max_vol
         fade_time = the duration of the fade effect in seconds
    """
    nsteps = 3
    vols = list(range(max_vol // 2, max_vol, max_vol // nsteps)) + [max_vol]
    if fade_out:
        vols = vols[::-1]
    for vol in vols[1:]:
        try:
            sp_client.volume(vol)
        except requests.HTTPError as e:
            print('HTTP ERROR {} occurred'.format(e.errno))
            print(e)
        sleep(fade_time / (nsteps + 1))


def playlist_preview(request):
    """ Start Playlist Preview mode where songs play a snippet at beginning, climax (loudest), and end.
        Must be executed locally once for user authentication in the browser.  Then auth cache can be
        deployed to GCP Cloud Functions for use with IFTTT.com to send http trigger with voice/Google Assistant.
        params:
          request = GCP Cloud Functions require a request argument, but here it's just a dummy to trigger execution
    """

    username = os.environ['USERNAME']
    duration = 18  # seconds per song
    outro = True

    # Copy existing auth file to writeable /tmp directory for GCP Cloud Functions
    cloud_func_mode = True
    if cloud_func_mode:
        shutil.copyfile('.cache-'+username, '/tmp/.cache-'+username)

    # Authenticate with proper scopes
    scope = "user-read-playback-state,user-modify-playback-state"

    sp = spotipy.Spotify(
        client_credentials_manager=SpotifyOAuth(scope=scope, cache_path='/tmp/.cache-'+username, username=username))

    initial_volume = get_initial_volume(sp)

    # After first local execution, authorization file must be copied to pwd for bundling into GCP deployment
    try:
        shutil.copyfile('/tmp/.cache-'+username, '.cache-'+username)
    except (shutil.Error, OSError) as e:
        print(e)

    # The loop over tracks in the current playlist
    while True:
        sleep(0.5)  # Need a small buffer to register when playback stopped from previous loop
        cur_play = sp.currently_playing()
        track_uri = cur_play['item']['uri']
        if not cur_play['is_playing']:
            break

        # Do some initial audio analysis
        max_loudness = -9999
        max_start_seconds = cur_play['item']['duration_ms'] / 1000 * 1 / 2  # mid-point as default
        max_duration = duration / 3
        try:
            aa = sp.audio_analysis(track_uri)
            for section in aa['sections']:
                if section['loudness'] > max_loudness:
                    max_loudness = section['loudness']
                    max_start_seconds = section['start']
                    max_duration = section['duration']
        except requests.exceptions.ReadTimeout as e:
            print('ReadTimeout ERROR {} occurred'.format(e.errno))
            print(e)

        # Play a bit at the start of the track
        sleep(duration / 3 * 29 / 30)
        if not sp.currently_playing()['is_playing']:
            break

        # Play a bit at the loudest part of the track
        if max_duration > 0:
            # If the loud section of the song is very short, don't play the whole preview duration
            loud_duration = min(max_duration, duration / 3)
            seek_pos = int(max_start_seconds * 1000)
            if seek_pos > sp.currently_playing()['progress_ms']:  # Never seek backwards, just move on
                fade(sp, initial_volume, fade_out=True, fade_time=loud_duration * 1 / 30)
                sp.seek_track(position_ms=int(max_start_seconds * 1000))
                fade(sp, initial_volume, fade_out=False, fade_time=loud_duration * 1 / 30)
                sleep(loud_duration * 28 / 30)
            if not sp.currently_playing()['is_playing']:
                break

        # Play a bit at the end of the track if outro is True
        if outro:
            end_pos = int(cur_play['item']['duration_ms'] - 2000 - duration * 1000 / 3)
            if end_pos > sp.currently_playing()['progress_ms']:
                fade(sp, initial_volume, fade_out=True, fade_time=duration / 3 * 1 / 30)
                sp.seek_track(position_ms=end_pos)
                fade(sp, initial_volume, fade_out=False, fade_time=duration / 3 * 1 / 30)
                sleep(duration / 3 * 20 / 30)  # Cut this one a bit short, usually cuts out silence
            if not sp.currently_playing()['is_playing']:
                break
        sp.next_track()


if __name__ == '__main__':
    playlist_preview(None)
