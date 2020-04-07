import argparse
import itertools
import json
import sys
import time
import requests
import re
import datetime
import hashlib
import hmac
import os
import io
from colorama import init, Style, Fore, Back
from requests import RequestException
from urllib.parse import urljoin, urlparse, unquote, quote, parse_qs, urlencode
from http import client
from urllib import parse
import subprocess
from multiprocessing.dummy import Pool
import shutil
from Crypto.Cipher import AES
from bs4 import BeautifulSoup as get_soup
from html import entities
import base64
import codecs