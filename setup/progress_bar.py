from .color import *

_spin = itertools.cycle(['▲', '►', '▼', '◄'])


class ProgressBar(object):

    def _progress(self, iteration, total, prefix='', ver=None, video_time=None, ts_time=None, file_size='',
                  downloaded='', rate='', suffix='', bar_length=25):
        filledLength = int(round(bar_length * iteration / float(total)))
        percents = format(100.00 * (iteration / float(total)), '.2f')
        bar = fw + sb + '#' * filledLength + fw + sd + '-' * (bar_length - filledLength)
        # bar = fc + sb + '▓' * filledLength + fw + sd + '-' * (bar_length - filledLength)
        if ver == 'hls':
            sys.stdout.write(
                '\033[2K\033[1G\r\r{}{}[{}{}*{}{}] : {}{}Length-video : [ {}/{} ] ╢{}{}{}╟  Percent : {}% '.format(
                    fg, sd, fc, sb, fg, sd, fg, sb, ts_time, video_time, bar, fg, sb, percents))
            sys.stdout.flush()
        else:
            if '0.00' not in rate:
                sys.stdout.write(
                    "\r{}{}[{}*{}] : Content-length : {}   ╢{}{}{}╟ Speed : {} Percent : {} %            ".format(
                        sb, fw, fw, fw, file_size, bar, fw, sb, rate, percents
                    )
                )
                sys.stdout.flush()

    def show_progress(self, total, recvd, ratio, rate, eta, ver=None, duration_ts=None):

        # for hls
        video_time = ''
        ts_time = ''
        if ver == 'hls':
            video_time = datetime.timedelta(seconds=int(total))
            ts_time = datetime.timedelta(seconds=int(duration_ts))
        # end for hls

        if total <= 1048576:
            _total_size = round(float(total) / 1024.00, 2)
            _receiving = round(float(recvd) / 1024.00, 2)
            _size = format(_total_size if _total_size < 1024.00 else _total_size / 1024.00, '.2f')
            _received = format(_receiving if _receiving < 1024.00 else _receiving / 1024.00, '.2f')
            suffix_size = 'KB' if _total_size < 1024.00 else 'MB'
            suffix_recvd = 'KB' if _receiving < 1024.00 else 'MB'
        else:
            _total_size = round(float(total) / 1048576, 2)
            _receiving = round(float(recvd) / 1048576, 2)
            _size = format(_total_size if _total_size < 1024.00 else _total_size / 1024.00, '.2f')
            _received = format(_receiving if _receiving < 1024.00 else _receiving / 1024.00, '.2f')
            suffix_size = 'MB' if _total_size < 1024.00 else 'GB'
            suffix_recvd = 'MB' if _receiving < 1024.00 else 'GB'

        _rate = round(float(rate), 2)
        rate = format(_rate if _rate < 1024.00 else _rate / 1024.00, '.2f')
        suffix_rate = 'kB/s' if _rate < 1024.00 else 'MB/s'
        (mins, secs) = divmod(eta, 60)
        (hours, mins) = divmod(mins, 60)
        if hours > 99:
            eta = "--:--:--"
        if hours == 0:
            eta = "eta %02d:%02ds" % (mins, secs)
        else:
            eta = "eta %02d:%02d:%02ds" % (hours, mins, secs)
        if secs == 0:
            eta = "\n"

        self._progress(_receiving, _total_size, file_size=str(_size) + str(suffix_size),
                       downloaded=str(_received) + str(suffix_recvd),
                       rate=str(rate) + str(suffix_rate),
                       suffix=str(eta),
                       ver=ver,
                       video_time=video_time,
                       ts_time=ts_time
                       )

    def spinner(self, text):
        spin = _spin.__next__()
        sys.stdout.write(text + spin)
        sys.stdout.flush()
        time.sleep(0.01)
