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