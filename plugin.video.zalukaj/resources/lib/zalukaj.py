# -*- coding: utf-8 -*-
import os
import re
from cookielib import LWPCookieJar

import requests
from bs4 import BeautifulSoup

""" Main url address """
URL = "https://zalukaj.com"

""" Maximum wait time for response"""
REQUEST_TIMEOUT = 5


class ZalukajError(Exception):
    pass


class ZalukajSuspiciousActivityError(ZalukajError):
    pass


class ZalukajUser(object):
    def __init__(self, name=None, account_type=None):
        self.name = name
        self.account_type = account_type

    def is_logged(self):
        return self.name is not None

    def is_premium(self):
        return self.is_logged() and 'vip' in self.account_type.lower()


class Zalukaj(object):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pl,en-US;q=0.9,en;q=0.8,fr;q=0.7',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
        'Referer': 'https://zalukaj.com/'
    }

    def __init__(self, data_path):
        cookies_file = os.path.join(data_path, 'zalukaj.cookie')  # Define path to cookies file
        self.session = requests.Session()
        self.session.cookies = LWPCookieJar(cookies_file)

        # Load cookies if file exists
        if os.path.isfile(cookies_file):
            self.session.cookies.load()

    def login(self, user, password):
        """
        Create user session in service.
        All data are send using ssl.

        :param user: User name
        :param password: User password
        :return:
        """

        def initialize_session(response_cookies):
            """
            Session is initialized if expected session cookie is present in request response.
            """
            if response_cookies.get('__PHPSESSIDS') is not None:
                self.session.cookies.save()
                return self.fetch_user_data()

            return ZalukajUser()

        headers = self.headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

        response = self.session.post(
            url='{}/account.php'.format(URL),
            data='login={}&password={}'.format(user, password),
            headers=headers,
            allow_redirects=False,
            timeout=REQUEST_TIMEOUT
        )

        return initialize_session(response.cookies if response.cookies else [])

    def logout(self):
        """
        To logout just remove all cookies.
        """
        self.session.cookies.clear()

    def fetch_user_data(self):
        """
        Fetch user details from account page.

        :return: ZalukajUser - user object with details
        """

        def get_user_name(bs):
            """
            Fetch user name from crawled page.

            :param bs: BeautifulSoup
            :return: string - user name
            """

            data = bs.find('a', attrs={'href': '#', 'style': 'text-decoration:underline;'})
            return data.text if data else None

        def get_account_type(bs):
            """
            Map account type to readable name.

            :param bs: BeautifulSoup
            :return: string - account type name
            """

            data = bs.select_one('div:nth-of-type(3) > p:nth-of-type(1) a')
            data = data.text if data else ''

            if "Darmowe" in data:  # shortening the name, do not want to display notification about registration
                return "konto darmowe"

            return data.lower()

        soup = self._get('{}/libs/ajax/login.php?login=1&x=2043'.format(URL))
        username = get_user_name(soup)
        if username:  # if username is present, user is logged in
            return ZalukajUser(name=username, account_type=get_account_type(soup))

        return ZalukajUser()

    def fetch_tv_series_list(self):
        """
        Fetch list of all available tv shows.

        :return: list of dicts with:
            url: string - url to tv series episodes list,
            title: string - tv series name
        """

        soup = self._get(URL)
        collection = soup.select('div#two table#main_menu a')
        return [{'url': single['href'], 'title': single['title']} for single in collection]

    def fetch_tv_series_seasons_list(self, link):
        """
        Fetch list of series for given tv series url.

        :param link: string - request url
        :return: list of dicts with:
            url: string - url to tv series episodes list for given season
            title: string - season name (in most cases it is just season number)
            img: string - link to season image (mostly image of tv series)
        """

        def map_to_title(text):
            """
            Map season name to more readable and clean title.

            :param text: string - current season name
            :return: string - new name for specified season
            """

            try:
                reg = re.search('(.*)Sezon:(.*)([0-9])(.*)', text, re.IGNORECASE)
                return "sezon {}".format(reg.group(3)) if reg and int(reg.group(3)) > 0 else text
            except:
                return text

        soup = self._get("{}{}".format(URL, link))

        # Fetch image
        image = soup.select_one('div.blok2 div > img')
        thumb = URL + image['src'] if image else None

        # Fetch seasons
        return [
            {'url': single['href'], 'title': map_to_title(single.text), 'img': thumb}
            for single in soup.select('div#sezony a.sezon')
        ]

    def fetch_tv_series_episodes_list(self, link):
        """
        Fetch tv series episodes list for given seasons link.

        :param link: string - request url
        :return: list of dicts with:
            url: string - url to episode
            title: string - episode name
            img: string - link to episode image (mostly image of tv series)
            episode: string - episode number
        """

        def get_season_and_episode(text):
            """
            :param text: string - string to search season and episode number
            :return: (season, episode) - tuple with season and episode number
            """
            reg = re.search('S([0-9]+)E([0-9]+)', text, re.IGNORECASE)
            if reg and len(reg.groups()) == 2:
                return int(reg.group(1)), int(reg.group(2))

            return None, None

        soup = self._get("{}{}".format(URL, link))

        # Fetch image
        image = soup.select_one('div.blok2 div > img')
        thumb = URL + image['src'] if image else None

        # Fetch episodes
        episodes = []
        for item in soup.select('div.odcinkicat > div'):
            item_link = item.select_one('a')
            (season, episode) = get_season_and_episode(item.select_one('span.vinfo').text)
            episodes.append({
                'url': item_link['href'],
                'title': item_link.string,
                'img': thumb,
                'season': season,
                'episode': episode,
            })

        return episodes

    def fetch_series_single_movie(self, link):
        """
        Fetch tv series episode detail to play.

        :param link: string - link to tv episode
        :return: list | None - tv series episode details or None if can not fetch data.
            quality: string - episode quality
            url: string - address to stream for specified quality
        """

        soup = self._get("https:{}".format(link))

        return self.fetch_series_single_movie_from_player("{}{}&x=1".format(URL, soup.select_one('iframe')['src']))

    def fetch_series_single_movie_from_player(self, link):
        def is_premium(ms):
            return len(ms.select('source')) > 0

        # Add domain URL hen not present
        if "//zalukaj.com" not in link:
            link = "{}{}".format(URL, link)

        if link[0:2] == '//':
            link = "https:{}".format(link)

        movie_soup = self._get(link)

        # First try parse page as not logged in
        if is_premium(movie_soup):
            versions = [{'version': source.string, 'url': source['href']} for source in
                        movie_soup.select('div#buttonsPL a')]
            streams = [{'quality': source['label'], 'url': source['src']} for source in movie_soup.select('source')]

            return {
                'streams': streams,
                'versions': versions
            }

        return None

    def _get(self, url):
        """
        :param url: string - url address to fetch and parse
        :return: BeautifulSoup
        """
        response = self.session.get(url=url, headers=self.headers, allow_redirects=True, timeout=REQUEST_TIMEOUT)
        self._detect_problems(response)
        return BeautifulSoup(response.text, 'html.parser')

    @staticmethod
    def _detect_problems(response):
        """
        Detect common problems like suspicious activity or high traffic alert.

        :param response: requests.Response
        """
        soup = BeautifulSoup(response.text, 'html.parser')
        if response.status_code == 503:
            if "Duze obciazenie!" in soup.text:
                raise ZalukajSuspiciousActivityError("Duże obciążenie serwisu. Spróbuj się zalogować.")

            raise ZalukajSuspiciousActivityError(soup.select_one('title').text)
