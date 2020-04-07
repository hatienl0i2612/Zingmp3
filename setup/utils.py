from .module import *

ACCENT_CHARS = dict(zip('ÂÃÄÀÁÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖŐØŒÙÚÛÜŰÝÞßàáâãäåæçèéêëìíîïðñòóôõöőøœùúûüűýþÿ',
                        itertools.chain('AAAAAA', ['AE'], 'CEEEEIIIIDNOOOOOOO', ['OE'], 'UUUUUY', ['TH', 'ss'],
                                        'aaaaaa', ['ae'], 'ceeeeiiiionooooooo', ['oe'], 'uuuuuy', ['th'], 'y')))

session = requests.Session()
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36',
}
KNOWN_EXTENSIONS = [
    'mp4', 'm4a', 'm4p', 'm4b', 'm4r', 'm4v', 'aac',
    'flv', 'f4v', 'f4a', 'f4b',
    'webm', 'ogg', 'ogv', 'oga', 'ogx', 'spx', 'opus',
    'mkv', 'mka', 'mk3d',
    'avi', 'divx',
    'mov',
    'asf', 'wmv', 'wma',
    '3gp', '3g2',
    'mp3',
    'flac',
    'ape',
    'wav',
    'f4f', 'f4m', 'm3u8', 'smil']


def duration_to_length(duration):
    if duration:
        length = datetime.timedelta(seconds=duration)
        if length:
            return length
    return None


def removeCharacters(value):
    value = str(value)
    return re.sub('\s+', ' ', value)


def removeCharacter_filename(s, restricted=False, is_id=False):
    def replace_insane(char):
        if restricted and char in ACCENT_CHARS:
            return ACCENT_CHARS[char]
        if char == '?' or ord(char) < 32 or ord(char) == 127:
            return ''
        elif char == '"':
            return '' if restricted else '\''
        elif char == ':':
            return '_-' if restricted else ' -'
        elif char in '\\/|*<>':
            return '_'
        if restricted and (char in '!&\'()[]{}$;`^,#' or char.isspace()):
            return '_'
        if restricted and ord(char) > 127:
            return '_'
        return char

    s = re.sub(r'[0-9]+(?::[0-9]+)+', lambda m: m.group(0).replace(':', '_'), s)
    result = ''.join(map(replace_insane, s))
    if not is_id:
        while '__' in result:
            result = result.replace('__', '_')
        result = result.strip('_')
        if restricted and result.startswith('-_'):
            result = result[2:]
        if result.startswith('-'):
            result = '_' + result[len('-'):]
        result = result.lstrip('.')
        if not result:
            result = '_'
    return result


def remove_quotes(s):
    if s is None or len(s) < 2:
        return s
    for quote in ('"', "'",):
        if s[0] == quote and s[-1] == quote:
            return s[1:-1]
    return s


def parse_json(json_string, transform_source=None):
    if transform_source:
        json_string = transform_source(json_string)
    if not json_string:
        return None
    try:
        return json.loads(json_string)
    except ValueError as ve:
        errmsg = '%s: Failed to parse JSON ' % ve
        return None


def extract_ok_ru(text):
    if not text:
        return

    def remove_char(s, f, t):
        return re.sub(f, t, s)

    f = []
    mobj = re.search(r'''(?x)\\\&quot;metadataUrl\\\&quot;\:\\\&quot;(?P<metadataUrl>.*?)\\\&quot;.*?
            \\\&quot;metadataWebmUrl\\\&quot;\:\\\&quot;(?P<metadataWebmUrl>.*?)\\\&quot;.*?
            \\\&quot;hlsManifestUrl\\\&quot;\:\\\&quot;(?P<hlsManifestUrl>.*?)\\\&quot;''', text)

    base_data = findAll_regex(r'''(?x)\\\\u003CRepresentation\s+
                            audioSamplingRate=\\\\\\&quot;(?P<audioSamplingRate>.*?)\\\\\\&quot;\s+
                            bandwidth=\\\\\\&quot;(?P<bandwidth>.*?)\\\\\\&quot;\s+
                            codecs=\\\\\\&quot;(?P<codecs>.*?)\\\\\\&quot;\s+
                            frameRate=\\\\\\&quot;(?P<frameRate>.*?)\\\\\\&quot;\s+
                            height=\\\\\\&quot;(?P<height>.*?)\\\\\\&quot;\s+
                            id=\\\\\\&quot;(?P<id>.*?)\\\\\\&quot;\s+
                            mimeType=\\\\\\&quot;(?P<mimeType>.*?)\\\\\\&quot;.*?
                            width=\\\\\\&quot;(?P<width>.*?)\\\\\\&quot;.*?
                            \\\\u003CBaseURL\\\\u003E(?P<url>.*?)\\\\u003C/BaseURL\\\\u003E
                            ''', text, all_data=True)
    sig = search_regex(r'author.*?\:.*?(movie.*?),\\\&quot;metadataEmbedded', text.replace('\n', ''))
    if not sig:
        sig = search_regex(r'author.*?\:.*?(movie.*?),\\\&quot;autoplay', text.replace('\n', ''))

    for a in base_data:
        if a:
            audioSamplingRate, bandwidth, codecs, frameRate, height, id, mimeType, width, url = a
            url = remove_char(url, r'(\\\\u0026amp;)', '&')
            f.append({
                'id': id,
                'height': height,
                'width': width,
                'mimeType': mimetype2ext(mimeType),
                'codecs': parse_codecs(codecs),
                'bandwidth': bandwidth,
                'audioSamplingRate': audioSamplingRate,
                'frameRate': frameRate,
                'url': url,
            })

    f = sorted(f, key=lambda x: x.get('id'))
    if sig:
        sig = sig.replace('&quot;', '').replace(r'\\u0026', '&').replace('\\', '"')
        sig = '{"%s}' % sig
        f.append(parse_json(sig))
    if mobj:
        meta = mobj.groupdict()
        for k, v in meta.items():
            meta[k] = remove_char(v, r'(\\\\u0026)', '&')
        f.append(meta)

    return f


def extract_eval_unpacked(text):
    # if text.startswith('eval'):
    #     text = 'console.log' + text[4:]
    # else:
    #     text = 'console.log(%s)' % text
    # with io.open('temp.data', 'w', encoding='utf-8') as f:
    #     f.write(text)
    # cmd = 'node.exe temp.data'
    # process = subprocess.check_output(cmd, shell=False)
    # os.remove('temp.data')
    # if process:
    #     return process.decode()
    # return None
    PRIORITY = 1

    beginstr = ''
    endstr = ''

    def detect(source):
        begin_offset = -1
        """Detects whether `source` is P.A.C.K.E.R. coded."""
        mystr = re.search('eval[ ]*\([ ]*function[ ]*\([ ]*p[ ]*,[ ]*a[ ]*,[ ]*c[ ]*,[ ]*k[ ]*,[ ]*e[ ]*,[ ]*', source)
        if (mystr):
            begin_offset = mystr.start()
            beginstr = source[:begin_offset]
        if (begin_offset != -1):
            """ Find endstr"""
            source_end = source[begin_offset:]
            if (source_end.split("')))", 1)[0] == source_end):
                try:
                    endstr = source_end.split("}))", 1)[1]
                except IndexError:
                    endstr = ''
            else:
                endstr = source_end.split("')))", 1)[1]
        return (mystr != -1)

    def unpack(source):
        """Unpacks P.A.C.K.E.R. packed js code."""
        payload, symtab, radix, count = _filterargs(source)

        if count != len(symtab):
            return

        try:
            unbase = Unbaser(radix)
        except TypeError:
            return

        def lookup(match):
            """Look up symbols in the synthetic symtab."""
            word = match.group(0)
            return symtab[unbase(word)] or word

        source = re.sub(r'\b\w+\b', lookup, payload)
        # print(source) #source contains the desobfuscated script
        return _replacestrings(source)

    def _filterargs(source):
        """Juice from a source file the four args needed by decoder."""
        juicers = [
            (r"}\('(.*)', *(\d+|\[\]), *(\d+), *'(.*)'\.split\('\|'\), *(\d+), *(.*)\)\)"),
            (r"}\('(.*)', *(\d+|\[\]), *(\d+), *'(.*)'\.split\('\|'\)"),
        ]
        for juicer in juicers:
            args = re.search(juicer, source, re.DOTALL)
            if args:
                a = args.groups()
                if a[1] == "[]":
                    a = list(a)
                    a[1] = 62
                    a = tuple(a)
                try:
                    return a[0], a[3].split('|'), int(a[1]), int(a[2])
                except ValueError:
                    return

        # could not find a satisfying regex
        return

    def _replacestrings(source):
        """Strip string lookup table (list) and replace values in source."""
        match = re.search(r'var *(_\w+)\=\["(.*?)"\];', source, re.DOTALL)

        if match:
            varname, strings = match.groups()
            startpoint = len(match.group(0))
            lookup = strings.split('","')
            variable = '%s[%%d]' % varname
            for index, value in enumerate(lookup):
                source = source.replace(variable % index, '"%s"' % value)
            return source[startpoint:]
        return beginstr + source + endstr

    class Unbaser(object):
        """Functor for a given base. Will efficiently convert
        strings to natural numbers."""
        ALPHABET = {
            62: '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
            95: (' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                 '[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~')
        }

        def __init__(self, base):
            self.base = base

            # fill elements 37...61, if necessary
            if 36 < base < 62:
                if not hasattr(self.ALPHABET, self.ALPHABET[62][:base]):
                    self.ALPHABET[base] = self.ALPHABET[62][:base]
            # attrs = self.ALPHABET
            # print ', '.join("%s: %s" % item for item in attrs.items())
            # If base can be handled by int() builtin, let it do it for us
            if 2 <= base <= 36:
                self.unbase = lambda string: int(string, base)
            else:
                # Build conversion dictionary cache
                try:
                    self.dictionary = dict(
                        (cipher, index) for index, cipher in enumerate(
                            self.ALPHABET[base]))
                except KeyError:
                    raise TypeError('Unsupported base encoding.')

                self.unbase = self._dictunbaser

        def __call__(self, string):
            return self.unbase(string)

        def _dictunbaser(self, string):
            """Decodes a  value to an integer."""
            ret = 0
            for index, cipher in enumerate(string[::-1]):
                ret += (self.base ** index) * self.dictionary[cipher]
            return ret

    return unpack(text)


def decodeString(code, _pass):
    if not code:
        return None
    a = ""
    for i in range(len(code)):
        r = ord(code[i])
        n = r ^ _pass
        a += chr(n)
    return a


def getlist_media(string):
    return findAll_regex(r'(?:\'|\")(?:src|url|hd|sd|hls)(?:\"|\').*?(?:\"|\')(.*?)(?:\"|\')', string, all_data=True)


def date_time_milliseconds(date_time_obj):
    return int(time.mktime(date_time_obj.timetuple()) * 1000)


def uppercase_escape(s):
    unicode_escape = codecs.getdecoder('unicode_escape')
    return re.sub(
        r'\\U[0-9a-fA-F]{8}',
        lambda m: unicode_escape(m.group(0))[0],
        s)


def search_regex(pattern, string, flags=0, group=None):
    mobj = None
    if isinstance(pattern, str):
        mobj = re.search(pattern, string, flags)
    else:
        for p in pattern:
            mobj = re.search(p, string, flags)
            if mobj:
                break
    if mobj:
        if group is None:
            return next(g for g in mobj.groups() if g is not None)
        else:
            return mobj.group(group)
    else:
        return None


def parse_codecs(codecs_str):
    if not codecs_str:
        return {}
    splited_codecs = list(filter(None, map(
        lambda str: str.strip(), codecs_str.strip().strip(',').split(','))))
    vcodec, acodec = None, None
    for full_codec in splited_codecs:
        codec = full_codec.split('.')[0]
        if codec in (
                'avc1', 'avc2', 'avc3', 'avc4', 'vp9', 'vp8', 'hev1', 'hev2', 'h263', 'h264', 'mp4v', 'hvc1', 'av01',
                'theora'):
            if not vcodec:
                vcodec = full_codec
        elif codec in ('mp4a', 'opus', 'vorbis', 'mp3', 'aac', 'ac-3', 'ec-3', 'eac3', 'dtsc', 'dtse', 'dtsh', 'dtsl'):
            if not acodec:
                acodec = full_codec
        else:
            print('WARNING: Unknown codec %s\n' % full_codec, sys.stderr)
    if not vcodec and not acodec:
        if len(splited_codecs) == 2:
            return {
                'vcodec': splited_codecs[0],
                'acodec': splited_codecs[1],
            }
    else:
        return {
            'vcodec': vcodec or 'none',
            'acodec': acodec or 'none',
        }
    return {}


def merge_dicts(*dicts):
    merged = {}
    for a_dict in dicts:
        for k, v in a_dict.items():
            if v is None:
                continue
            if (k not in merged
                    or (isinstance(v, str) and v
                        and isinstance(merged[k], str)
                        and not merged[k])):
                merged[k] = v
    return merged


def findAll_regex(pattern, string, index=0, text_find=None, all_data=False):
    mobj = re.findall(pattern, string)

    if mobj:
        try:
            if all_data:
                return mobj
            if text_find:
                for i in mobj:
                    if text_find in i:
                        return i
            return mobj[index]
        except IndexError as e:
            return None
    else:
        return None


KNOWN_EXTENSIONS = (
    'mp4', 'm4a', 'm4p', 'm4b', 'm4r', 'm4v', 'aac',
    'flv', 'f4v', 'f4a', 'f4b',
    'webm', 'ogg', 'ogv', 'oga', 'ogx', 'spx', 'opus',
    'mkv', 'mka', 'mk3d',
    'avi', 'divx',
    'mov',
    'asf', 'wmv', 'wma',
    '3gp', '3g2',
    'mp3',
    'flac',
    'ape',
    'wav',
    'f4f', 'f4m', 'm3u8', 'smil')


def dict_get(d, key_or_keys, default=None, skip_false_values=True):
    if isinstance(key_or_keys, (list, tuple)):
        for key in key_or_keys:
            if key not in d or d[key] is None or skip_false_values and not d[key]:
                continue
            return d[key]
        return default
    return d.get(key_or_keys, default)


def try_get(src, getter, expected_type=None):
    if not isinstance(getter, (list, tuple)):
        getter = [getter]
    for get in getter:
        try:
            v = get(src)
        except (AttributeError, KeyError, TypeError, IndexError):
            pass
        else:
            if expected_type is None or isinstance(v, expected_type):
                return v


def decript_url(code, password):
    if not code:
        return None
    decoded = base64.b64decode(code)
    # extract salt and actual data
    salt = decoded[8:16]
    data = decoded[16:]

    # key and IV derivation
    def openssl_kdf(req):
        prev = b""
        mat = []
        while req > 0:
            prev = MD5.new(prev + password + salt).digest()
            req -= 16
            mat.append(prev)
        return mat

    mat = openssl_kdf(3 * 16)
    key = mat[0] + mat[1]
    iv = mat[2]

    # decryption
    clear = AES.new(key, AES.MODE_CBC, iv).decrypt(data).decode()
    padding_length = ord(clear[-1])
    return clear[:-padding_length]


def mimetype2ext(mt):
    if mt is None:
        return None

    ext = {
        'audio/mp4': 'm4a',
        'audio/mpeg': 'mp3',
    }.get(mt)
    if ext is not None:
        return ext

    _, _, res = mt.rpartition('/')
    res = res.split(';')[0].strip().lower()

    return {
        '3gpp': '3gp',
        'smptett+xml': 'tt',
        'ttaf+xml': 'dfxp',
        'ttml+xml': 'ttml',
        'x-flv': 'flv',
        'x-mp4-fragmented': 'mp4',
        'x-ms-sami': 'sami',
        'x-ms-wmv': 'wmv',
        'mpegurl': 'm3u8',
        'x-mpegurl': 'm3u8',
        'vnd.apple.mpegurl': 'm3u8',
        'dash+xml': 'mpd',
        'f4m+xml': 'f4m',
        'hds+xml': 'f4m',
        'vnd.ms-sstr+xml': 'ism',
        'quicktime': 'mov',
        'mp2t': 'ts',
    }.get(res, res)


def is_url(url):
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    return url if re.match(r'^(?:[a-zA-Z][\da-zA-Z.+-]*:)?//|^\/(.*?)\/', url) else None


def is_int(v, scale=1, default=None, get_attr=None, invscale=1):
    if get_attr:
        if v is not None:
            v = getattr(v, get_attr, None)
    if v == '':
        v = None
    if v is None:
        return default
    try:
        return int(v) * invscale // scale
    except (ValueError, TypeError):
        return default


def is_float(v, scale=1, invscale=1, default=None):
    if v is None:
        return default
    try:
        return float(v) * invscale / scale
    except (ValueError, TypeError):
        return default


def js_to_json(code):
    if not code:
        return None
    code = code.replace(':!', ':')
    COMMENT_RE = r'/\*(?:(?!\*/).)*?\*/|//[^\n]*'
    SKIP_RE = r'\s*(?:{comment})?\s*'.format(comment=COMMENT_RE)
    INTEGER_TABLE = (
        (r'(?s)^(0[xX][0-9a-fA-F]+){skip}:?$'.format(skip=SKIP_RE), 16),
        (r'(?s)^(0+[0-7]+){skip}:?$'.format(skip=SKIP_RE), 8),
    )

    def fix_kv(m):
        v = m.group(0)
        if v in ('true', 'false', 'null'):
            return v
        elif v.startswith('/*') or v.startswith('//') or v == ',':
            return ""

        if v[0] in ("'", '"'):
            v = re.sub(r'(?s)\\.|"', lambda m: {
                '"': '\\"',
                "\\'": "'",
                '\\\n': '',
                '\\x': '\\u00',
            }.get(m.group(0), m.group(0)), v[1:-1])

        for regex, base in INTEGER_TABLE:
            im = re.match(regex, v)
            if im:
                i = int(im.group(1), base)
                return '"%d":' % i if v.endswith(':') else '%d' % i

        return '"%s"' % v

    return re.sub(r'''(?sx)
        "(?:[^"\\]*(?:\\\\|\\['"nurtbfx/\n]))*[^"\\]*"|
        '(?:[^'\\]*(?:\\\\|\\['"nurtbfx/\n]))*[^'\\]*'|
        {comment}|,(?={skip}[\]}}])|
        (?:(?<![0-9])[eE]|[a-df-zA-DF-Z_])[.a-zA-Z_0-9]*|
        \b(?:0[xX][0-9a-fA-F]+|0+[0-7]+)(?:{skip}:)?|
        [0-9]+(?={skip}:)
        '''.format(comment=COMMENT_RE, skip=SKIP_RE), fix_kv, code)


def determine_ext(url, default_ext='unknown_video'):
    if url is None or '.' not in url:
        return default_ext
    guess = url.partition('?')[0].rpartition('.')[2]
    if re.match(r'^[A-Za-z0-9]+$', guess):
        return guess
    elif guess.rstrip('/') in KNOWN_EXTENSIONS:
        return guess.rstrip('/')
    else:
        return default_ext


def _htmlentity_transform(entity_with_semicolon):
    entity = entity_with_semicolon[:-1]

    if entity in entities.name2codepoint:
        return chr(entities.name2codepoint[entity])

    if entity_with_semicolon in entities.html5:
        return entities.html5[entity_with_semicolon]

    mobj = re.match(r'#(x[0-9a-fA-F]+|[0-9]+)', entity)
    if mobj is not None:
        numstr = mobj.group(1)
        if numstr.startswith('x'):
            base = 16
            numstr = '0%s' % numstr
        else:
            base = 10
        try:
            return chr(int(numstr, base))
        except ValueError:
            pass

    return '&%s;' % entity


def unescapeHTML(s):
    if s is None:
        return None
    assert type(s) == str

    return re.sub(
        r'&([^&;]+;)', lambda m: _htmlentity_transform(m.group(1)), s)


def remove_char_in_dict(text):
    if not text:
        return

    def do(text):
        regx = r"\=(?:\"|\')(.*?)(?:\"|\')"
        for tm in re.findall(regx, text):
            text = text.replace(f'"{tm}"', f"'{tm}'")

        return text

    text = re.sub(r'(\\)', '', text)
    text = re.sub(r'(\"\[)', '[', text)
    text = re.sub(r'(\]\")', "]", text)
    text = re.sub(r'(\\\")', '"', text)
    text = do(text)
    return text


def clean_html(html):
    # """Clean an HTML snippet into a readable string"""

    if html is None:  # Convenience for sanitizing descriptions etc.
        return html

    # # Newline vs <br />
    # html = html.replace('\n', ' ')
    # html = re.sub(r'(?u)\s*<\s*br\s*/?\s*>\s*', '\n', html)
    # html = re.sub(r'(?u)<\s*/\s*p\s*>\s*<\s*p[^>]*>', '\n', html)
    # # Strip html tags
    # html = re.sub('<.*?>', '', html)
    # # Replace html entities
    # html = unescapeHTML(html)
    # return html.strip()
    html = removeCharacters(html)
    soup = get_soup(html, 'html5lib')
    return soup.text


class ErrorException(Exception):
    """Raise when have a bug"""
