from .progress_bar import *
from .utils import to_screen


class ConnectionError(RequestException):
    """A Connection error occurred."""


early_py_version = sys.version_info[:2] < (2, 7)


def use_ffmpeg(cmd,progress_bar = True,note = ""):
    """
    - use ffmpeg to download with url and user_agent and convert them to .mp4 and put them to path download
    :param cmd: cmd
    :return: a processbar in terminal
    """
    bar_length = 25
    try:
        if progress_bar:
            x = 0
            duration = []
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8-sig'
            )
            for line in process.stdout:
                line = str(line)

                try:
                    if 'Duration' in line:
                        duration = re.findall(r':\s(.*?)\,', line)
                        h = int(duration[0][0:2])
                        m = int(duration[0][3:5])
                        s = int(duration[0][6:8])
                        x = h + m / 60 + s / 60 / 60
                    if re.findall(r'time=(.*?)\s', line):
                        time = re.findall(r'time=(.*?)\s', line)
                        hh = int(time[0][0:2])
                        mm = int(time[0][3:5])
                        ss = int(time[0][6:8])
                        y = hh + mm / 60 + ss / 60 / 60
                        percent = int((y / x) * bar_length)
                        sys.stdout.write(
                            fg + sb + '\r[' + fc + '*' + fg + f'''] : {note}: {duration[0]} ╢{fc + percent * "#"}{fg + (bar_length - percent) * "-"}╟ {round((y / x) * 100, 2)} % Time: {time[0]}        ''')
                        sys.stdout.flush()
                    if line.startswith('video:'):
                        y = x
                        percent = int((y / x) * bar_length)
                        sys.stdout.write(
                            fg + sb + '\r[' + fc + '*' + fg + f'''] : {note}: {duration[0]} ╢{fc + percent * "#"}{fg + (bar_length - percent) * "-"}╟ 100 % Time: {duration[0]}        ''')
                        sys.stdout.flush()
                except Exception as e:
                    pass
            sys.stdout.write("\n")
        else:
            subprocess.run(cmd,shell=False)
        return True
    except FileNotFoundError:
        to_screen("This url need ffmpeg\n\tPls download and setup ffmpeg https://www.ffmpeg.org")
        sys.exit()


class Download_HLS(ProgressBar):
    def __init__(self, urlM3u8, name, ext=None, callback=lambda *x: None, DirDownload=None, headers={}):
        self.urlM3u8 = urlM3u8
        self.session = requests.Session()
        self.DirDownload = DirDownload
        self.name = name
        self.headers = headers
        self.count = 1
        self.d_ts = float()
        self.callback = callback
        self.ext = ext or 'mp4'
        self.ver = 'hls'

    def run(self):
        self.path = '%s/%s.%s' % (self.DirDownload, self.name, self.ext)
        self.temp_path = '%s/%s' % (self.DirDownload, 'temp')
        if not os.path.exists(self.temp_path):
            os.mkdir(self.temp_path)
        if os.path.exists(self.path):
            sys.stdout.write(fg + '[' + fr + '-' + fg + '] : Already downloaded.\n')
            return
        self.GetTsFromM3u8()
        self.DownloadTsAndKey()

    def GetTsFromM3u8(self):
        r = self.session.get(self.urlM3u8, headers=self.headers)
        string = r.text
        self.url_key = re.findall(r'URI=\"(.*?)\"', str(r.text))
        if self.url_key:
            self.url_key = self.url_key[0]
            string = string.replace(self.url_key, 'temp.key')
        self.lst_ts = re.findall(r'#EXTINF:(.*?)\,\n(.*?)\n', str(r.text))
        l = list(map(float, [i[0] for i in self.lst_ts]))
        self.sum_duration = sum(l)
        for index, [duration_ts, ts] in enumerate(self.lst_ts):
            if ts:
                url_ts = urljoin(self.urlM3u8, ts)
                temp_ts = 'temp%s.ts' % index
                self.lst_ts[index] = [duration_ts, url_ts, temp_ts]
                string = string.replace(url_ts, temp_ts)
        self.allow_file = '%s/hls.txt' % (self.temp_path)
        with io.open(self.allow_file, 'w') as f:
            f.write(string)

    def write_data(self, data, name):
        with io.open('%s/%s' % (self.temp_path, name), 'wb') as f:
            f.write(data)
        return

    def DownloadTsAndKey(self):
        if self.url_key:
            r = self.session.get(self.url_key, headers=self.headers)
            self.key = r.content
            self.write_data(data=self.key, name='temp.key')
        self.l = len(self.lst_ts)
        thread = int(self.l ** (1 / 4))
        p = Pool(1)
        p.map(self.Decript, self.lst_ts)
        p.close()
        cmd = '''ffmpeg -allowed_extensions ALL -i "%s" -c copy "%s" -y''' % (self.allow_file, self.path)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        text = fg + '\r[' + fr + '-' + fg + '] : Merge video [ %s ] ... ' % (self.name)
        sys.stdout.write('\n')
        for line in process.stdout:
            self.spinner(text=text)
        sys.stdout.write(fg + '\r[' + fr + '-' + fg + '] : Merge video [ %s ] ... (done)\n' % (self.name))
        shutil.rmtree(self.temp_path)

    def get_info_for_progress_bar(self, end, first, is_malformed, time_run=float()):
        if time_run:
            try:
                rate = ((float(end) - float(first)) / 1024.0) / time_run
                eta = (self.sum_duration - self.d_ts) / (rate * 1024.0)
            except ZeroDivisionError:
                is_malformed = True
                retVal = {"status": False,
                          "msg": "ZeroDivisionError : it seems, file has malfunction or is zero byte(s) .."}
                sys.stdout.write(fg + '[' + fr + '-' + fg + '] : %s\n' % (retVal['msg']))
                return
        else:
            rate = 0
            eta = 0
        return rate, eta, is_malformed

    def Decript(self, item, IV=None):
        is_malformed = False
        duration_ts, ts, name_ts = item
        o1 = time.time()
        r = self.session.get(url=ts, headers=self.headers)
        data = r.content
        offset = self.d_ts
        self.d_ts += float(duration_ts)
        elapsed = time.time() - o1

        rate, eta, is_malformed = self.get_info_for_progress_bar(end=self.d_ts, first=offset, time_run=elapsed,
                                                                 is_malformed=is_malformed)
        temp = None
        if self.url_key:
            if len(self.key) % 16:
                retVal = {"status": False,
                          "msg": "Reason : Can not decode .ts file."}
                sys.stdout.write(fg + '[' + fr + '-' + fg + '] : %s\n' % (retVal['msg']))
                return
            if IV is None:
                IV = data[0:16]
                data = data[16:]
            datalen = len(data)
            decryptor = AES.new(self.key, AES.MODE_CBC, IV)
            chucksize = 64 * 1024
            dataOut = b''
            i = 0
            while True:
                chunk = data[i:i + chucksize]
                i += len(chunk)
                if i >= datalen:
                    chunk = decryptor.decrypt(chunk)
                    dataOut += chunk
                    break
                else:
                    dataOut += decryptor.decrypt(chunk)
            if not is_malformed:
                progress_stats = (self.d_ts, self.d_ts * 1.0 / self.sum_duration, rate, eta, self.ver, self.d_ts)
                self.show_progress(self.sum_duration, *progress_stats)
            temp = dataOut
        else:
            if not is_malformed:
                progress_stats = (self.d_ts, self.d_ts * 1.0 / self.sum_duration, rate, eta, self.ver, self.d_ts)
                self.show_progress(self.sum_duration, *progress_stats)
            temp = r.content
        self.write_data(data=temp, name=name_ts)
        return
