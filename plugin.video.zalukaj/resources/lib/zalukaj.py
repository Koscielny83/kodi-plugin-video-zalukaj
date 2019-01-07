# -*- coding: utf-8 -*-
import os
import re
from cookielib import LWPCookieJar

import requests
from bs4 import BeautifulSoup

""" Main url address """
URL = "https://zalukaj.com"

""" Cookie name where session is stored """
SESSION_COOKIE_NAME = "PHPSESSID"

""" Maximum wait time for response"""
REQUEST_TIMEOUT = 5

""" File where cookies are storage """
FILE_COOKIES_NAME = "zalukaj.cookie"


class ZalukajError(Exception):
    pass


class ZalukajSuspiciousActivityError(ZalukajError):
    pass


class ZalukajLoginError(ZalukajError):
    pass


class ZalukajUser(object):
    def __init__(self, name=None, account_type=None):
        self.name = name
        self.account_type = account_type

    def is_logged(self):
        return self.name is not None

    def is_premium(self):
        return self.is_logged() and 'vip' in self.account_type.lower()

    def __repr__(self):
        return 'ZalukajUser<{}, {}>'.format(self.name.encode('utf-8'), self.account_type.encode('utf-8'))


class Zalukaj(object):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pl,en-US;q=0.9,en;q=0.8,fr;q=0.7',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
        'Referer': 'https://zalukaj.com/',
        'Origin': 'https://zalukaj.com/'
    }

    def __init__(self, data_path, session=None):
        cookies_file = os.path.join(data_path, FILE_COOKIES_NAME)  # Define path to cookies file
        self.session = session if session else requests.Session()
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

        """
        Session is initialized if expected session cookie is present in request response.
        """

        def initialize_session(response_cookies):
            if response_cookies.get(SESSION_COOKIE_NAME) is not None:
                self.session.cookies.save()
                return self.fetch_user_data()

            return ZalukajUser()

        headers = self.headers
        """
        First we have to fetch csrf hash token to perform login action.
        To do this fetch main page raw html and take hash from form.
        """
        main_page_response = self.session.get(url=URL,
                                              headers=headers,
                                              allow_redirects=False,
                                              timeout=REQUEST_TIMEOUT)

        """
        If hash is present, take it from known input.
        If hash is not present we are probably logged in or account is blocked. Check known problems before fetching 
        hash content.
        """
        self._detect_problems(main_page_response)
        login_hash_obj = self._get_bs4(main_page_response.text).find('input', attrs={'name': 'hash'})
        login_hash = login_hash_obj['value'] if login_hash_obj else None

        """
        When hash is present start login process using credentials.
        """
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['X-Requested-With'] = 'XMLHttpRequest'
        login_response = self.session.post(url='{}/ajax/login'.format(URL),
                                           data='username={}&password={}&hash={}'.format(user, password, login_hash),
                                           headers=headers,
                                           allow_redirects=False,
                                           timeout=REQUEST_TIMEOUT)

        if "Zalogowano!" not in login_response.text:
            raise ZalukajLoginError("Wystąpił problem z logowaniem.")

        return initialize_session(login_response.cookies if login_response.cookies else {})

    def logout(self):
        """
        To logout just remove all cookies.
        """
        self.session.cookies.clear()
        self.session.cookies.save()

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

        if link[0:5] != "https":
            link = "{}{}".format(URL, link)

        soup = self._get(link)

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

    def fetch_movie_details(self, link):
        """
        Fetch movie details to play.

        :param link: string - link to tv episode
        :return: list | None - tv movie details or None if can not fetch data.
            quality: string - stream quality
            url: string - address to stream for specified quality
        """

        soup = self._get(link)

        return self.fetch_movie_from_player("{}{}&x=1".format(URL, soup.select_one('iframe')['src']))

    def fetch_movie_from_player(self, link):
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

    def fetch_movie_categories_list(self):
        """
        Fetch list of all available movie categories.

        :return: list of dicts with:
            url: string - url to tv series episodes list,
            title: string - tv series name
        """

        soup = self._get(URL)
        collection = soup.select('table#one td a')
        return [{'url': single['href'], 'title': single.text} for single in collection]

    def fetch_movies_list(self, link):
        """
        Fetch list movies for given link.

        :return: list of dicts with:
            url: string - url to tv series episodes list,
            title: string - tv series name
            img: string - movie thumb,
            description: string - movie short description
        """

        def get_navigation_links(navigation):
            previous_page = None
            next_page = None
            current_page = navigation.select_one("span.pc_current")
            if current_page:
                current_page = int(current_page.text)
                for item in navigation.select("a"):
                    try:
                        item_page = int(item.text)

                        if current_page - 1 == item_page:
                            previous_page = [
                                item_page,
                                item['href'] if item['href'][0:5] == 'https' else '{}{}'.format(URL, item['href'])
                            ]
                            continue

                        if current_page + 1 == item_page:
                            next_page = [
                                item_page,
                                item['href'] if item['href'][0:5] == 'https' else '{}{}'.format(URL, item['href'])
                            ]
                            continue
                    except:
                        pass

            return previous_page, next_page

        def get_movie_cover(cover_item):
            """
            :param cover_item: string - cover bs4 element
            :return: string - link to movie cover
            """
            if cover_item and cover_item['style']:
                reg = re.search('background-image:url\(([a-z0-9-_.:/)]+)\);', cover_item['style'], re.IGNORECASE)
                if reg and len(reg.groups()) == 1:
                    return reg.group(1) if reg.group(1)[0:5] == 'https' else '{}{}'.format(URL, reg.group(1))

            return None

        def get_movie_year(cover_item):
            """
            :param cover_item: string - cover bs4 element
            :return: string - link to movie cover
            """
            if cover_item:
                year = cover_item.select_one('p span')
                try:
                    return int(year.text)
                except:
                    return None

            return None

        if link[0:5] != 'https':
            link = "{}{}".format(URL, link)

        soup = self._get(link)
        link_next, link_previous = get_navigation_links(soup.select_one("div.categories_page"))

        # Fetch movies
        movies = []
        if link_next:
            movies.append({'url': link_next[1],
                           'title': '<< Wróć (strong {}) <<'.format(link_next[0]),
                           'nav': True})
        if link_previous:
            movies.append({'url': link_previous[1],
                           'title': '>> Dalej (strona {}) >>'.format(link_previous[0]),
                           'nav': True})

        for item in soup.select('div#index_content div.tivief4'):
            item_link = item.select_one('div.rmk23m4 h3 a')
            description = item.select_one('div.rmk23m4 > div')
            movies.append({
                'url': item_link['href'],
                'img': get_movie_cover(item.select_one('div.im23jf')),
                'year': get_movie_year(item.select_one('div.im23jf')),
                'title': item_link['title'].encode('utf-8'),
                'description': description.text.encode('utf-8') if description else ''
            })

        if link_next:
            movies.append({'url': link_next[1],
                           'title': '<< Wróć (strong {}) <<'.format(link_next[0]),
                           'nav': True})
        if link_previous:
            movies.append({'url': link_previous[1],
                           'title': '>> Dalej (strona {}) >>'.format(link_previous[0]),
                           'nav': True})

        return movies

    def search_movies(self, search_phrase):
        link = "{}/v2/ajax/load.search?html=1&q={}".format(URL, search_phrase)
        soup = self._get(link)

        def get_movie_year(el):
            if not el:
                return None

            try:
                text = el.text.encode('utf-8')
                reg = re.search('^([0-9]{4}).*', text, re.IGNORECASE)
                return int(reg.group(1))
            except:
                return None

        movies = []
        for item in soup.select('div.row'):
            cover = item.select_one('div.thumb img')
            data = item.select_one('div.details div.title a')
            description = item.select_one('div.desc')
            if data:
                is_tv_series = re.search('.*/serial.*', data['href'])
                movies.append({
                    'url': data['href'] if data['href'][0:5] == 'https' else '{}{}'.format(URL, data['href']),
                    'img': cover['src'] if cover else None,
                    'year': get_movie_year(item.select_one('div.details div.gen')),
                    'title': data['title'].encode('utf-8'),
                    'description': description.text.encode('utf-8') if description else '',
                    'tv_series': True if is_tv_series else False
                })

        return movies

    def _get(self, url):
        """
        :param url: string - url address to fetch and parse
        :return: BeautifulSoup
        """
        response = self.session.get(url=url,
                                    headers=self.headers,
                                    allow_redirects=True,
                                    timeout=REQUEST_TIMEOUT)
        self._detect_problems(response)
        return self._get_bs4(response.text)

    @staticmethod
    def _get_bs4(text):
        """
        Return BS4 object from raw html.
        :param text:
        :return: BeautifulSoup
        """
        return BeautifulSoup(text, 'html.parser')

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
