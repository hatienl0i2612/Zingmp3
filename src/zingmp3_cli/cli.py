"""Command-line parsing and application orchestration."""

import argparse
import json
import sys

from .crawler import ZingMp3Crawler
from .downloader import Downloader
from .exceptions import ZingMp3Error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zingmp3", description="Crawl metadata and download media from zingmp3.vn"
    )
    parser.add_argument("url", help="Zing MP3 URL to crawl")
    parser.add_argument(
        "-c",
        "--cookies",
        "--cookies-file",
        dest="cookies",
        metavar="FILE_OR_VALUE",
        help=(
            "Netscape cookies.txt, a file containing a raw Cookie header, "
            "or a raw Cookie header"
        ),
    )
    parser.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER[:COOKIE_DB]",
        help=(
            "read cookies from brave, chrome, chromium, edge, firefox, "
            "opera, safari, vivaldi, ..."
        ),
    )
    parser.add_argument(
        "-H",
        "--headers",
        action="append",
        default=[],
        metavar="KEY: VALUE",
        help="HTTP header sent with every request; may be specified multiple times",
    )
    parser.add_argument(
        "-j", "--json", action="store_true", help="only print resolved metadata as JSON"
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help=(
            "destination file for media or directory for collections; "
            "ignored for LIVE URLs"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        crawler = ZingMp3Crawler(
            cookies=args.cookies,
            cookies_from_browser=args.cookies_from_browser,
            headers=args.headers,
        )
        if args.json:
            result = crawler.extract(args.url)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        result = crawler.extract(args.url, resolve=False)
        downloader = Downloader(crawler.client)
        for path in downloader.iter_downloads(
            crawler.iter_media(result),
            args.output,
            is_playlist=result.get("_type") == "playlist",
        ):
            print(path)
        return 0
    except (ZingMp3Error, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
