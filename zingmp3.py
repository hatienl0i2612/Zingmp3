from setup import *


class Authentication:
    def __init__(self, path_cookies='', username='', password=''):
        self._path_cookies = path_cookies
        self._username = username
        self._password = password
        self._headers = HEADERS

    def auth_with_cookies(self):
        file = open(self._path_cookies, 'r', encoding='utf-8')
        cookies = {}
        out = ''
        for line in file:
            line = line.strip()
            if '#' not in line:
                item = re.findall(r'[0-9]\s(.*)', line)
                if item:
                    item = item[0].split('\t')
                    if len(item) == 1:
                        cookies[item[0]] = ''
                        out += "%s=''; " % item[0]
                    else:
                        cookies[item[0]] = item[1]
        update_cookies(cookies)
        return True


class Zingmp3_vn(ProgressBar):
    LIST_TEST = '''
https://zingmp3.vn/Mr-Siro/bai-hat

https://zingmp3.vn/Mr-Siro/playlist

https://zingmp3.vn/Mr-Siro/video

https://zingmp3.vn/nghe-si/Huong-Giang-Idol/bai-hat

https://zingmp3.vn/nghe-si/Huong-Giang-Idol/album

https://zingmp3.vn/nghe-si/Huong-Giang-Idol/video

https://zingmp3.vn/top-new-release/index.html

https://zingmp3.vn/zing-chart/bai-hat.html

https://zingmp3.vn/zing-chart-tuan/video-US-UK/IWZ9Z0BU.html

https://zingmp3.vn/zing-chart-tuan/bai-hat-US-UK/IWZ9Z0BW.html

https://zingmp3.vn/album/Khoc-Cung-Em-Single-Mr-Siro-Gray-Wind/ZF90UA9I.html

https://zingmp3.vn/playlist/Sofm-s-playlist/IWE606EA.html

https://zingmp3.vn/chu-de/Nhac-Hot/IWZ9Z0C8.html

https://zingmp3.vn/the-loai-video/Nhac-Tre/IWZ9Z088.html

https://zingmp3.vn/the-loai-album/Rap-Hip-Hop/IWZ9Z09B.html

https://zingmp3.vn/video-clip/Tim-Ve-Loi-Ru-New-Version-Thanh-Hung-Various-Artists/ZW6ZOIZ7.html

https://zingmp3.vn/video-clip/Yeu-Nhieu-Ghen-Nhieu-Thanh-Hung/ZWB087B9.html

https://zingmp3.vn/bai-hat/Khoc-Cung-Em-Mr-Siro-Gray-Wind/ZWBI0DFI.html

https://zingmp3.vn/embed/song/ZWBW6WE8?start=false
'''

    _regex_url = r'''(?x)^
        ((?:http[s]?|fpt):)\/?\/(?:www\.|m\.|)
        (?P<site>
            (zingmp3\.vn)
        )\/(?P<type>(?:bai-hat|video-clip|embed))\/(?P<slug>.*?)\/(?P<id>.*?)\W
        '''

    def __init__(self, *args, **kwargs):
        self._default_host = "https://zingmp3.vn/"
        self._headers = HEADERS
        self._is_login = kwargs.get('is_login')
        self._path_save = kwargs.get("path_save") or os.getcwd()
        self._show_json_info = kwargs.get("show_json_info")
        self._down_lyric = kwargs.get("down_lyric")
        self._add_index = kwargs.get('add_index')
        self._convert_audio = kwargs.get("convert_audio")
        self.f = True
        if self._add_index:
            self._index_media = 1
        else:
            self._index_media = -1

    def run(self, url):
        mobj = re.search(self._regex_url, url)
        if not mobj:
            return
        video_id = mobj.group('id')
        _type = mobj.group('type')
        slug = mobj.group('slug')
        return self.extract_info_media(_type, slug, video_id)

    def extract_info_media(self, _type, slug, video_id):
        sys.stdout.write("\n")
        name_api = ''
        if _type == 'bai-hat':
            name_api = '/song/get-song-info'
        elif _type == 'embed':
            if slug and slug == 'song':
                name_api = '/song/get-song-info'
        elif _type == 'video-clip':
            name_api = "/video/get-video-detail"

        api = self.get_api_with_signature(name_api=name_api, video_id=video_id)
        info = self.fr(api=api,note="Downloading json from %s" % video_id)
        if _type == 'video-clip' and not self._is_login:
            # TODO: Have api can get best quality like 1080p, 720p, default if dont have VIP just 480p is best quality.
            #  If requests are continuous without downtime,
            #  you may be blocked IP for a short period of time,
            #  So => time.sleep(2)
            _api_video = """http://api.mp3.zing.vn/api/mobile/video/getvideoinfo?requestdata={"id":"%s"}"""
            _json_video = self.fr(api=_api_video % video_id)
            info['data']['streaming']['data']['default'] = _json_video.get("source")
            time.sleep(2)

        if self._is_login:
            # TODO: if have vip account can get 320 or lossless media, default is 128
            # TODO: Just support login with cookie file, use -c or --cookie FILE.
            api_download = self.get_api_with_signature(name_api='/download/get-streamings', video_id=video_id)
            _json = self.fr(api=api_download,note="")
            if _json and _json.get('msg') != 'Chỉ tài khoản VIP có thể tải bài hát này':
                info['data']['streaming']['default'] = _json.get('data')

        def convert_thumbnail(url):
            if url:
                return re.sub(r'w[0-9]+', 'w1080', url)
        if self._show_json_info:
            sys.stdout.write(json.dumps(info, indent=4, ensure_ascii=False))
            return
        if info.get('msg') == 'Success':
            data = info.get('data')
            title = data.get('title')
            streaming = data.get('streaming')
            thumbnail = data.get("thumbnail_medium") or data.get("thumbnail")
            lyric = data.get('lyric') or try_get(data, lambda x: x['lyrics'][0]['content'], str)
            self.start_download(streaming=streaming, _type=_type, title=title, lyric=lyric, thumbnail=thumbnail)
        else:
            to_screen("Error can not find media data.")

    def start_download(self, streaming, _type, title, lyric, thumbnail):
        stream_data = streaming.get('data', dict)
        DirDownload = os.path.join(os.getcwd(), "DOWNLOAD")
        if not os.path.exists(DirDownload):
            os.mkdir(DirDownload)

        def add_protocol(url):
            if not url.startswith("http"):
                return 'https:' + url
            return url

        def remove_p_quality(text):
            return search_regex(r'([0-9]+)', text)

        def get_lyric(lyric):
            if is_url(lyric):
                lyric = session.get(url=lyric, headers=self._headers).text
            if lyric:
                return lyric

        def down_lyric():
            if self._down_lyric:
                with io.open(os.path.join(DirDownload, "%s.lrc" % title), 'w', encoding='utf-8-sig') as f:
                    str_lyric = get_lyric(lyric)
                    if str_lyric:
                        f.write(str_lyric)
                        to_screen("Download lyric .... DONE.")
                    else:
                        to_screen("This media don't have lyric.")

        def remove_temp_path(temp_output):
            if os.path.exists(temp_output):
                if os.path.isfile(temp_output):
                    os.remove(temp_output)

        formats = []
        title = removeCharacter_filename(title)
        if self._index_media != -1:
            title = "%s - %s" % (self._index_media, title)
            self._index_media += 1
        to_screen("Bài hát : %s" % title)
        if _type == 'video-clip':

            for protocol, stream in stream_data.items():
                if protocol == 'default':
                    protocol = 'http'
                for quality, url in stream.items():
                    if url and url != "ERROR":
                        if protocol == 'hls':
                            formats.append({
                                "quality": remove_p_quality(quality),
                                "url": url,
                                "protocol": "hls",
                                'ext': "mp4"
                            })
                        elif protocol == 'http':
                            formats.append({
                                'url': add_protocol(url),
                                "quality": remove_p_quality(quality),
                                "protocol": "http",
                                "ext": "mp4"
                            })
            formats = sorted(formats, key=lambda x: (
                is_int(x['quality']),
                1 if x["protocol"] == "http" else 0
            ))
        else:
            if streaming.get('msg') != "Success":
                to_screen(
                    "  Zingmp3_vn requires authentication.\n"
                    "\tBecause This media need VIP account to listen or watch.\n"
                    "\tYou should use -c or --cookie FILE.\n"
                )
                return
            default = streaming.get('default')
            for quality, url in default.items():
                if url:
                    if quality == 'lossless':
                        formats.append({
                            'url': add_protocol(url),
                            'ext': 'flac',
                            'protocol': 'http'
                        })
                    else:
                        formats.append({
                            'url': add_protocol(url),
                            'ext': 'mp3',
                            'protocol': 'http'
                        })
        will_down = formats[-1]
        protocol = will_down.get("protocol")
        _url = will_down.get('url')
        _ext = will_down.get("ext")
        output_convert_mp3 = os.path.join(DirDownload, r"%s.mp3" % (title))
        temp_output = os.path.join(DirDownload, r"%s.hatienl0i261299" % title)
        outtmpl = os.path.join(DirDownload, r"%s.%s" % (title, _ext))
        if self._convert_audio:
            if not os.path.exists(output_convert_mp3):
                down = Downloader(url=_url)
                down.download(
                    filepath=temp_output,
                    callback=self.show_progress
                )
            else:
                to_screen("Already downloaded")
        else:
            if not os.path.exists(outtmpl):
                if protocol == "http":
                    down = Downloader(url=_url)
                    down.download(
                        filepath=temp_output,
                        callback=self.show_progress
                    )
                elif protocol == "hls":
                    status = use_ffmpeg(
                        cmd='''ffmpeg -y -loglevel "repeat+info" -i "%s" -c copy -f mp4 "-bsf:a" aac_adtstoasc "%s"''' % (
                            _url, temp_output),
                        progress_bar=True,
                        note="Download hls"
                    )
            else:
                to_screen("Already downloaded")
        if self._convert_audio and _ext == "flac":
            temp_path_ffmpeg = os.path.join(DirDownload, r"%s.%s.hatienl0i261299" % (title, _ext))
            status = use_ffmpeg(
                cmd='''ffmpeg -y -loglevel "repeat+info" -i "%s" -ab 320k -map_metadata 0 -id3v2_version 3 -f mp3 "%s"''' % (
                    temp_output, temp_path_ffmpeg),
                progress_bar=True,
                note=".flac to .mp3"
            )
            if os.path.exists(temp_path_ffmpeg):
                if os.path.isfile(temp_path_ffmpeg):
                    if not os.path.exists(output_convert_mp3):
                        os.rename(temp_path_ffmpeg, output_convert_mp3)
            remove_temp_path(temp_output)
            down_lyric()
            return

        if not os.path.exists(outtmpl):
            os.rename(temp_output, outtmpl)
        remove_temp_path(temp_output)
        down_lyric()
        return
    
    def fr(self,api,params={},note = ""):
        if self.f:
            get_req(url=api, headers=self._headers) 
            info = get_req(url=api, headers=self._headers, params=params, type='json', note=note)
            self.f = False
        else:
            info = get_req(url=api, headers=self._headers, params=params, type='json', note=note)
        return info


    def get_api_with_signature(self, name_api, q_search='', video_id='', alias='', _type='', new_release=False):
        """
        - The api of this site has 1 param named sig => signature
        - It uses the hash function of the variables ctime, id, and name_api.
        - Sone api don't need id, just need ctime and name_api,
        :param _type:
        :param alias:
        :param name_api:
        :param video_id:
        :param _type:
        :param new_release:
        :return: api
        """
        API_KEY = '38e8643fb0dc04e8d65b99994d3dafff'
        SECRET_KEY = b'10a01dcf33762d3a204cb96429918ff6'
        if not name_api:
            return
        _time = str(int(datetime.datetime.now().timestamp()))

        def get_hash256(string):
            return hashlib.sha256(string.encode('utf-8')).hexdigest()

        def get_hmac512(string):
            return hmac.new(SECRET_KEY, string.encode('utf-8'), hashlib.sha512).hexdigest()

        def get_api_by_id(_id):
            url = r"https://zingmp3.vn/api%s?id=%s&" % (name_api, _id)
            sha256 = get_hash256(r"ctime=%sid=%s" % (_time, _id))

            data = {
                'ctime': _time,
                'api_key': API_KEY,
                'sig': get_hmac512(r"%s%s" % (name_api, sha256))
            }
            return url + urlencode(data)

        def get_api_chart(_type):
            url = r"https://zingmp3.vn/api%s?type=%s&" % (name_api, _type)
            sha256 = get_hash256(r"ctime=%s" % _time)

            data = {
                'ctime': _time,
                'api_key': API_KEY,
                'sig': get_hmac512(r"%s%s" % (name_api, sha256))
            }
            return url + urlencode(data)

        def get_api_new_release():
            url = r"https://zingmp3.vn/api%s?" % name_api
            sha256 = get_hash256(r"ctime=%s" % _time)

            data = {
                'ctime': _time,
                'api_key': API_KEY,
                'sig': get_hmac512(r"%s%s" % (name_api, sha256))
            }
            return url + urlencode(data)

        def get_api_download(_id):
            url = r"https://download.zingmp3.vn/api%s?id=%s&" % (name_api, _id)
            sha256 = get_hash256(r"ctime=%sid=%s" % (_time, _id))

            data = {
                'ctime': _time,
                'api_key': API_KEY,
                'sig': get_hmac512(r"%s%s" % (name_api, sha256))
            }
            return url + urlencode(data)

        def get_api_info_alias(alias):
            url = r"https://zingmp3.vn/api%s?alias=%s&" % (name_api, alias)
            sha256 = get_hash256(r"ctime=%s" % _time)

            data = {
                'ctime': _time,
                'api_key': API_KEY,
                'sig': get_hmac512(r"%s%s" % (name_api, sha256))
            }
            return url + urlencode(data)

        def get_api_search():
            url = "https://zingmp3.vn/api%s?" % name_api
            time = str(int(datetime.datetime.now().timestamp()))
            sha256 = get_hash256(f"ctime={time}")

            data = {
                'ctime': time,
                'api_key': API_KEY,
                'q': q_search,
                'sig': get_hmac512(r"%s%s" % (name_api, sha256))
            }

            return url + urlencode(data)

        if 'download' in name_api:
            return get_api_download(_id=video_id)
        if q_search:
            return get_api_search()
        if alias:
            return get_api_info_alias(alias)
        if video_id:
            return get_api_by_id(video_id)
        if _type:
            return get_api_chart(_type)
        if new_release:
            return get_api_new_release()
        return


class Zingmp3_vnPlaylist(Zingmp3_vn):
    _regex_playlist = r'''(?x)^
            ((?:http[s]?|fpt):)\/?\/(?:www\.|m\.|)
                (?P<site>
                    (zingmp3\.vn)
                )\/(?P<type>(?:album|playlist|chu-de|the-loai-video|the-loai-album))\/(?P<slug>.*?)\/(?P<playlist_id>.*?)\W
                '''

    def __init__(self, *args, **kwargs):
        super(Zingmp3_vnPlaylist, self).__init__(*args, **kwargs)
        self.name_api_album_or_playlist = '/playlist/get-playlist-detail'
        self.name_api_topic = "/topic/get-detail"
        self.name_api_the_loai_video = "/video/get-list"
        self.name_api_the_loai_album = "/playlist/get-list"

    def run_playlist(self, url):
        mobj = re.search(self._regex_playlist, url)
        _type = mobj.group('type')
        playlist_id = mobj.group('playlist_id')
        slug = mobj.group('slug')
        if _type == 'chu-de':
            return self._entries_for_chu_de(id_chu_de=playlist_id)
        elif _type == "the-loai-video":
            return self._entries_for_the_loai_video(id_the_loai_video=playlist_id, slug=slug)
        elif _type == "the-loai-album":
            return self._entries_for_the_loai_album(id_the_loai_album=playlist_id, slug=slug)
        return self._extract_playlist(id_playlist=playlist_id)

    def _entries_for_the_loai_album(self, id_the_loai_album, slug):
        to_screen("the-loai-album :  %s  %s" % (slug, id_the_loai_album))
        api = self.get_api_with_signature(name_api=self.name_api_the_loai_album, video_id=id_the_loai_album)
        start = 0
        count = 30
        while True:
            info = self.fr(api=api,params={
                "type": "genre_album",
                "sort": "listen",
                "start": start,
                "count": count,
            })
            if info.get("msg").lower() != "success":
                break
            items = try_get(info, lambda x: x["data"]["items"], list) or []
            if not items:
                break
            for item in items:
                if not item:
                    continue
                url = urljoin(self._default_host, item.get("link"))
                if 'album' in url or 'playlist' in url:
                    self.run_playlist(url)
                else:
                    self.run(url)
            total = is_int(try_get(info, lambda x: x['data']['total'], int)) or -1
            start += count

            if total <= start:
                break

    def _entries_for_the_loai_video(self, id_the_loai_video, slug):
        to_screen("the-loai-video :  %s  %s" % (slug, id_the_loai_video))
        api = self.get_api_with_signature(name_api=self.name_api_the_loai_video, video_id=id_the_loai_video)
        start = 0
        count = 30
        while True:
            info = self.fr(api=api,params={
                "type": "genre",
                "sort": "listen",
                "start": start,
                "count": count,
            })
            if info.get("msg").lower() != "success":
                break
            items = try_get(info, lambda x: x["data"]["items"], list) or []
            if not items:
                break
            for item in items:
                if not item:
                    continue
                url = urljoin(self._default_host, item.get("link"))
                if 'album' in url or 'playlist' in url:
                    self.run_playlist(url)
                else:
                    self.run(url)
            total = is_int(try_get(info, lambda x: x['data']['total'], int)) or -1
            start += count

            if total <= start:
                break

    def _entries_for_chu_de(self, id_chu_de):
        api = self.get_api_with_signature(name_api=self.name_api_topic, video_id=id_chu_de)
        info = self.fr(api=api)
        if info.get('msg').lower() != "success":
            to_screen("Can not find data, something was wrong, pls check url again.")
            return
        title_chu_de = try_get(info, lambda x: x['data']["info"]["title"])
        items = try_get(info, lambda x: x['data']['playlist']['items'], list) or []
        to_screen(f"Chủ đề : {title_chu_de}")
        for item in items:
            if not item:
                continue
            url = urljoin(self._default_host, item.get('link'))
            media_id = item.get('id')
            if 'album' in url or 'playlist' in url:
                self._extract_playlist(media_id)

    def _extract_playlist(self, id_playlist):
        api = self.get_api_with_signature(name_api=self.name_api_album_or_playlist, video_id=id_playlist)
        info = self.fr(api=api)
        title_playlist = try_get(info, lambda x: x['data']['title'], str) or ''
        items = try_get(info, lambda x: x['data']['song']['items'], list) or []
        to_screen(f"Playlist : {title_playlist}")
        for item in items:
            if not item:
                continue
            url = urljoin(self._default_host, item.get('link'))
            self.run(url)


class Zingmp3_vnChart(Zingmp3_vn):
    _regex_chart = r'''(?x)^
            ((?:http[s]?|fpt):)\/?\/(?:www\.|m\.|)
            (?P<site>
                (zingmp3\.vn)
            )\/(?P<name>(?:zing-chart-tuan|zing-chart|top-new-release))\/
            (?P<slug_name>.*?)(\.|\/)(?P<id_name>.*?\.)?
            '''

    def __init__(self, *args, **kwargs):
        super(Zingmp3_vnChart, self).__init__(*args, **kwargs)
        self.list_name_api = {
            'zing-chart': {
                'name': '/chart-realtime/get-detail',
                'bai-hat': 'song',
                'index': 'song',
                'video': 'video',
            },
            'zing-chart-tuan': {
                'name': '/chart/get-chart',
            },
            'top-new-release': {
                'name': '/chart/get-chart-new-release'
            }
        }

    def run_chart(self, url):
        mobj = re.search(self._regex_chart, url)
        name = mobj.group('name')
        slug_name = mobj.group('slug_name')

        to_screen("#%s : %s" % (name, slug_name))

        if name == 'zing-chart':
            api = self.get_api_with_signature(
                name_api=self.list_name_api.get(name).get('name'),
                _type=self.list_name_api.get(name).get(slug_name))
        elif name == 'zing-chart-tuan':
            api = self.get_api_with_signature(
                name_api=self.list_name_api.get(name).get('name'),
                video_id=mobj.group('id_name'))
        else:
            api = self.get_api_with_signature(
                name_api=self.list_name_api.get(name).get('name'),
                new_release=True)
        count = 0
        info = None
        while count != 3:
            info = self.fr(api=api)
            if info:
                info = parse_json(info, transform_source=js_to_json)
                break
            count += 1
        if info:
            return self._entries(try_get(info, lambda x: x['data']['items'], list))

    def _entries(self, items):
        for item in items:
            if not item:
                continue
            url = urljoin(self._default_host, item.get('link'))
            self.run(url)


class Zingmp3_vnUser(Zingmp3_vnPlaylist):
    _regex_user = r'''(?x)^
        ((?:http[s]?|fpt):)\/?\/(?:www\.|m\.|)
        (?P<site>
            (zingmp3\.vn)
        )\/(?P<nghe_si>(?!bai-hat|video-clip|embed|album|playlist|chu-de|zing-chart|top-new-release|zing-chart-tuan|the-loai-video|the-loai-album)(?:nghe-si\/|))(?P<name>.*?)
        (?:$|\/)
        (?P<slug_name>(?:bai-hat|album|video|playlist|))$
            '''

    def __init__(self, *args, **kwargs):
        super(Zingmp3_vnUser, self).__init__(*args, **kwargs)
        self.list_name_api_user = {
            'bai-hat': "/song/get-list",
            "playlist": "/playlist/get-list",
            "album": "/playlist/get-list",
            "video": "/video/get-list",
        }

    def run_user(self, url):
        mobj = re.search(self._regex_user, url)
        name = mobj.group('name')
        slug_name = mobj.group('slug_name') or "bai-hat"
        nghe_si = mobj.group('nghe_si')

        name_api = self.list_name_api_user.get(slug_name) or None
        self.id_artist = None
        to_screen(f'{name} - {slug_name}')
        if nghe_si:
            api = self.get_api_with_signature(name_api="/artist/get-detail", alias=name)
        else:
            api = self.get_api_with_signature(name_api="/oa/get-artist-info", alias=name)
        info = self.fr(api=api)
        if info.get('msg') == 'Success':
            self.id_artist = try_get(info, lambda x: x['data']['id'], str) or None

        if self.id_artist:
            self.api = self.get_api_with_signature(name_api=name_api, video_id=self.id_artist)
            return self._entries()

    def _entries(self):
        start = 0
        count = 30
        while True:
            info = self.fr(api=self.api,params={
                'type': 'artist',
                'start': start,
                'count': count,
                'sort': 'hot'
            })
            if info.get('msg').lower() != "success":
                break
            items = try_get(info, lambda x: x['data']['items'], list) or []
            if not items:
                break
            for item in items:
                if not item:
                    continue
                url = urljoin(self._default_host, item.get('link'))
                if 'album' in url or 'playlist' in url:
                    self.run_playlist(url)
                else:
                    self.run(url)
            total = is_int(try_get(info, lambda x: x['data']['total'], int)) or -1
            start += count

            if total <= start:
                break


class Base():
    def __init__(self, *args, **kwargs):
        tm = Zingmp3_vn(*args, **kwargs)
        url = kwargs.get("url")

        if "mp3.zing.vn" in url.lower():
            url = url.replace("mp3.zing.vn", "zingmp3.vn")

        if re.match(tm._regex_url, url):
            tm.run(url)

        tm = Zingmp3_vnPlaylist(*args, **kwargs)
        if re.match(tm._regex_playlist, url):
            tm.run_playlist(url)

        tm = Zingmp3_vnChart(*args, **kwargs)
        if re.match(tm._regex_chart, url):
            tm.run_chart(url)

        tm = Zingmp3_vnUser(*args, **kwargs)
        if re.match(tm._regex_user, url):
            tm.run_user(url)


def main(argv):
    parser = argparse.ArgumentParser(description='Zingmp3 - A tool crawl data from zingmp3.vn')
    parser.add_argument('url', type=str, help='Url.')

    authen = parser.add_argument_group('Authentication')
    authen.add_argument('-c', '--cookie', dest='path_cookie', type=str, help='Cookies for authenticate with.',
                        metavar='')

    opts = parser.add_argument_group("Options")
    opts.add_argument('-s', '--save', type=str, default=os.getcwd(), help='Path to save', dest='path_save', metavar='')
    opts.add_argument('-j', '--json', default=False, action='store_true', help="Show json of info media.",
                      dest='show_json_info')
    opts.add_argument('-l', '--lyric', default=False, action='store_true', help='Download only lyric.',
                      dest='down_lyric')
    opts.add_argument("--add-index", default=False, action="store_true", help="Add index of playlist.",
                      dest="add_index")
    opts.add_argument("--convert-mp3", default=False, action="store_true", help="Convert the audio output to .mp3",
                      dest="convert_audio")

    args = parser.parse_args()
    status_auth = False
    if args.path_cookie:
        auth = Authentication(path_cookies=args.path_cookie)
        status_auth = auth.auth_with_cookies()
        if status_auth:
            to_screen("Login oke.")
        else:
            to_screen('Login false.', status="error")
    Base(
        url=args.url,
        path_save=args.path_save,
        show_json_info=args.show_json_info,
        down_lyric=args.down_lyric,
        is_login=status_auth,
        add_index=args.add_index,
        convert_audio=args.convert_audio
    )
    to_screen("Everything ..... Done.")


if __name__ == '__main__':
    try:
        if sys.stdin.isatty():
            main(sys.argv)
        else:
            argv = sys.stdin.read().split(' ')
            main(argv)
    except KeyboardInterrupt:
        sys.stdout.write(
            fc + sd + "\n[" + fr + sb + "-" + fc + sd + "] : " + fr + sd + "User Interrupted..\n")
        sys.exit(0)
    # except Exception as e:
    #     to_screen("Give that error for fix https://github.com/hatienl0i261299/Zingmp3/issues", status="error")
