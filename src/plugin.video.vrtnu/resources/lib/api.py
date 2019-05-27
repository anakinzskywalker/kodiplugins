import hashlib
import time
import re
import xbmc
import json
import requests
from collections import OrderedDict

from matthuisman import userdata, inputstream, plugin
from matthuisman.session import Session
from matthuisman.log import log
from matthuisman.exceptions import Error
from matthuisman.cache import cached

from .constants import HEADERS, VRT_PLAYER_TOKEN_URL, CANVAS_STREAM_URL, EEN_STREAM_URL, KETNET_STREAM_URL, VUPLAY_API_URL, PASSWORD_KEY, CHANNEL_EXPIRY, CHANNELS_CACHE_KEY
from .language import _


class APIError(Error):
    pass


def sorted_nicely(l, key):
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda x: [convert(c) for c in re.split('([0-9]+)', x[key].replace(' ', '').strip().lower())]
    return sorted(l, key=alphanum_key)


class API(object):
    def new_session(self):
        #self._logged_in = False
        self._session = Session(HEADERS)
        #self._set_access_token(userdata.get('access_token'))

    '''
    def _set_access_token(self, token):
        if not token:
            return

        self._session.headers.update({'sky-x-access-token': token})
        self._logged_in = True

    @property
    def logged_in(self):
        return self._logged_in

    def content(self):
        content = OrderedDict()

        rows = self._session.get(CONTENT_URL).json()['data']
        for row in sorted_nicely(rows, 'title'):
            content[row['id']] = row

        return content
    '''

    @cached(expires=CHANNEL_EXPIRY, key=CHANNELS_CACHE_KEY)
    def channels(self):
        channels = OrderedDict()

        # data = self._session.get(CHANNELS_URL).json()

        channels['Een'] = {
            'title': 'Een',
            'description': 'Een',
            'url': EEN_STREAM_URL,
            'image': ''
        }

        channels['Canvas'] = {
            'title': 'Canvas',
            'description': 'Canvas',
            'url': CANVAS_STREAM_URL,
            'image': ''
        }

        #
        # for row in sorted_nicely(data['entries'], 'title'):
        #    image = row['media$thumbnails'][0]['plfile$url'] if row['media$thumbnails'] else None
        #    data = {'title': row['title'], 'description': row['description'], 'url': '', 'image': image}
        #    for item in row['media$content']:
        #        if 'SkyGoStream' in item['plfile$assetTypes']:
        #            data['url'] = item['plfile$url']
        #            break

        #            channels[row['title']] = data

        return channels

    def login(self, username, password):
        device_id = hashlib.md5(username).hexdigest()

        data = {
            "deviceDetails": "test",
            "deviceID": device_id,
            "deviceIP": DEVICE_IP,
            "password": password,
            "username": username
        }

        resp = self._session.post(AUTH_URL, json=data)
        data = resp.json()
        if resp.status_code != 200 or 'sessiontoken' not in data:
            raise APIError(_(_.LOGIN_ERROR, message=data.get('message')))

        access_token = data['sessiontoken']

        userdata.set('access_token', access_token)
        userdata.set('device_id', device_id)

        self._set_access_token(access_token)

    def _renew_token(self):
        password = userdata.get(PASSWORD_KEY)

        if password:
            self.login(userdata.get('username'), password)
            return

        data = {
            "deviceID": userdata.get('device_id'),
            "deviceIP": DEVICE_IP,
            "sessionToken": userdata.get('access_token'),
        }

        resp = self._session.post(RENEW_URL, json=data)
        data = resp.json()

        if resp.status_code != 200 or 'sessiontoken' not in data:
            raise APIError(_(_.RENEW_TOKEN_ERROR, message=data.get('message')))

        access_token = data['sessiontoken']
        userdata.set('access_token', access_token)

        self._set_access_token(access_token)

    def _get_play_token(self):
        self._renew_token()

        params = {
            'profileId': userdata.get('device_id'),
            'deviceId': userdata.get('device_id'),
            'partnerId': 'skygo',
            'description': 'ANDROID',
        }

        resp = self._session.get(TOKEN_URL, params=params)
        data = resp.json()

        if resp.status_code != 200 or 'token' not in data:
            raise APIError(_(_.TOKEN_ERROR, message=data.get('message')))

        return data['token']

    def play_media(self, media_id):
        token = self._get_play_token()

        params = {
            'form': 'json',
            'types': None,
            'fields': 'id,content',
            'byId': media_id,
        }

        data = self._session.get(PLAY_URL, params=params).json()

        videos = data['entries'][0]['media$content']

        chosen = videos[0]
        for video in videos:
            if video['plfile$format'] == 'MPEG-DASH':
                chosen = video
                break

        url = '{}&auth={}&formats=mpeg-dash&tracking=true'.format(chosen['plfile$url'], token)
        resp = self._session.get(url, allow_redirects=False)

        if resp.status_code != 302:
            data = resp.json()
            raise APIError(_(_.PLAY_ERROR, message=data.get('description')))

        url = resp.headers.get('location')
        pid = chosen['plfile$url'].split('?')[0].split('/')[-1]

        return plugin.Item(
            path=url,
            art=False,
            inputstream=inputstream.Widevine(
                license_key=WIDEVINE_URL.format(token=token, pid=pid, challenge='B{SSM}'),
                challenge='',
                content_type='',
                response='JBlicense',
            ),
        )

    def _get_vrt_player_token(self):
        resp = self._session.post(VRT_PLAYER_TOKEN_URL)
        data = resp.json()

        if resp.status_code != 200 or 'vrtPlayerToken' not in data:
            raise APIError(_(_.RENEW_TOKEN_ERROR, message=data.get('message')))

        return data['vrtPlayerToken']

    def _get_vrt_license_url(self):
        return self._session.get(VUPLAY_API_URL).json()['drm_providers']['widevine']['la_url']

    def play_channel(self, channel):
        channels = self.channels()
        channel = channels.get(channel)
        if not channel:
            raise APIError(_.NO_CHANNEL)

        token = self._get_vrt_player_token()
        url = '{}&vrtPlayerToken={}'.format(channel['url'], token)
        resp = self._session.get(url, allow_redirects=False)
        data = resp.json()

        #### VRT:
        # {
        #   "playlist": {
        #     "content": []
        #   },
        #   "targetUrls": [
        #     {
        #       "url": "https://live-cf-vrt.akamaized.net/groupc/live/8edf3bdf-7db3-41c3-a318-72cb7f82de66/live.isml/.mpd",
        #       "type": "mpeg_dash"
        #     },
        #     {
        #       "url": "https://live-cf-vrt.akamaized.net/groupc/live/8edf3bdf-7db3-41c3-a318-72cb7f82de66/live.isml/.m3u8",
        #       "type": "hls"
        #     }
        #   ],
        #   "title": "En LIVE",
        #   "chaptering": {
        #     "content": []
        #   },
        #   "channelId": "vualto_een_geo",
        #   "drmExpired": "2019-02-26T02:25:51.549Z",
        #   "skinType": "live",
        #   "drm": "vrt|2019-02-26T00:25:51Z|JQ+5wYy/Tp9XH+ZTKSAoNEVid6kPznYl6noAaJxgq6G2oJlDx4Dt7hA1ctuYQDKyO651wPlp8f1LntmiGlAcrKNRgnOCuzSyw8UTb0o8lc2dLmA6O9YKnkjpLN0TovVDSxm+jsgmbxsoFee3/B26guvbGkXFJjaKuE4ghiIGCAlobStTWYsDYiHuArUpx/Cm|4e89f13fdc1242c6ddc2dbe8bd6588b837fe5514",
        #   "posterImageUrl": null,
        #   "duration": 0,
        #   "aspectRatio": null,
        #   "shortDescription": null
        # }

        #### CANVAS:
        # {
        #   "playlist": {
        #     "content": []
        #   },
        #   "targetUrls": [
        #     {
        #       "url": "https://live-cf-vrt.akamaized.net/groupc/live/14a2c0f6-3043-4850-88a5-7fb062fe7f05/live.isml/.m3u8",
        #       "type": "hls"
        #     },
        #     {
        #       "url": "https://live-cf-vrt.akamaized.net/groupc/live/14a2c0f6-3043-4850-88a5-7fb062fe7f05/live_aes.isml/.m3u8",
        #       "type": "hls_aes"
        #     },
        #     {
        #       "url": "https://live-cf-vrt.akamaized.net/groupc/live/14a2c0f6-3043-4850-88a5-7fb062fe7f05/live.isml/.mpd",
        #       "type": "mpeg_dash"
        #     }
        #   ],
        #   "title": "Canvas LIVE",
        #   "chaptering": {
        #     "content": []
        #   },
        #   "channelId": "vualto_canvas_geo",
        #   "drmExpired": "2019-02-26T23:06:01.958Z",
        #   "skinType": "live",
        #   "drm": "vrt|2019-02-26T21:06:01Z|wOmvkzrtihK711rrhO0mFf5EP/9yKXnVOWigvjOEvvDwXKjuoB9UuI13FwAqVDUgH3g0OBYMwjcsoZo+siQKqcYmD8y5RlIoFFUq5RPhxXCdLmA6O9YKnkjpLN0TovVDSxm+jsgmbxsoFee3/B26guvbGkXFJjaKuE4ghiIGCAlobStTWYsDYiHuArUpx/Cm|0cf9eda61ba0c430e20eb8de463756c1ebf36205",
        #   "posterImageUrl": null,
        #   "duration": 0,
        #   "aspectRatio": null,
        #   "shortDescription": null
        # }

        # xbmc.log(encryption_json, xbmc.LOGNOTICE)

        encryption_json = '{{"token":"{0}","drm_info":[D{{SSM}}],"kid":"{{KID}}"}}'.format(data['drm'])

        plugin_item = None

        for targetUrl in data['targetUrls']:
            if plugin_item is None and targetUrl['type'] == 'mpeg_dash':
                plugin_item = plugin.Item(
                    path=targetUrl['url'],
                    label=channel['title'],
                    art=False,
                    info={'description': channel['description']},
                    inputstream=inputstream.Widevine(
                        license_key=self._get_vrt_license_url(),
                        challenge=requests.utils.quote(encryption_json),
                        content_type='text/plain;charset=UTF-8',
                        response='',
                    ),
                )

        return plugin_item

    def logout(self):
        userdata.delete('device_id')
        userdata.delete('access_token')
        userdata.delete(PASSWORD_KEY)
        self._logged_in = False
