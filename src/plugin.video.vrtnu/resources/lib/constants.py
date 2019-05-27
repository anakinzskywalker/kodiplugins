HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
    'TE': 'trailers',
    'Origin': 'https://www.vrt.be',
    'Referer': 'https://www.vrt.be/'
    #'sky-x-forwarded-for': 'test',
    #'x-api-key': '0VLwN2X1Nk99ao12C5byc7fn59iHxatD9SUQye69',
    #'X-Sky-API-Key': '375663d6df9ad11809c7bb9dd3e634f8',
    #'X-Forwarded-For': '202.89.4.222',
}

#DEVICE_IP               = '192.168.1.1'
VRT_PLAYER_TOKEN_URL    = 'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/tokens'
CANVAS_STREAM_URL       = 'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/videos/vualto_canvas_geo?client=vrtvideo'
EEN_STREAM_URL          = 'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/videos/vualto_een_geo?client=vrtvideo'
KETNET_STREAM_URL       = 'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/videos/vualto_ketnet_geo?client=vrtvideo'
VUPLAY_API_URL          = 'https://api.vuplay.co.uk'

#CHANNELS_URL = 'https://feed.theplatform.com/f/7tMqSC/PDBWHrmbpxqw?form=json&validFeed=true&omitInvalidFields=true&fields=content,title,description,thumbnails'
#AUTH_URL     = 'https://4azub3wqb8.execute-api.ap-southeast-2.amazonaws.com/prod/auth/skygo/token/v1/authenticate/'
#TOKEN_URL    = 'https://6cwj6qmdoa.execute-api.ap-southeast-2.amazonaws.com/prod/v1/token/mpx/'
#RENEW_URL    = 'https://4azub3wqb8.execute-api.ap-southeast-2.amazonaws.com/prod/auth/skygo/token/v1/renew'
#CONTENT_URL  = 'https://d3207bvak4txrg.cloudfront.net/v1/content'
#IMAGE_URL    = 'https://prod-images.skygo.co.nz/{}'
#PLAY_URL     = 'https://feed.theplatform.com/f/7tMqSC/T2XJ65T_soBz'
#WIDEVINE_URL = 'https://widevine.entitlement.theplatform.com/wv/web/ModularDrm/getWidevineLicense?schema=1.0&token={token}&form=json&account=http://access.auth.theplatform.com/data/Account/2682481291&_releasePid={pid}&_widevineChallenge={challenge}'

CHANNEL_EXPIRY = (60*60*1) #1 hour
CHANNELS_CACHE_KEY = 'channels'
PASSWORD_KEY = 'Z03Px'