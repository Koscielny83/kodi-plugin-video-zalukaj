import re
import unittest

from resources.lib.zalukaj import Zalukaj

TEST_CONFIG = {
    'username': '',
    'password': '',
    'display_name': '',
}


class DocDict(dict):
    def __getattr__(self, name):
        return self[name]


class TestStringMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.z = Zalukaj('')
        cls.z.login(TEST_CONFIG['username'], TEST_CONFIG['password'])

    @classmethod
    def tearDownClass(cls):
        cls.z.session.cookies.clear()
        cls.z.session.cookies.save()

    def test_fetch_movie_categories_list(self):
        resp = self.z.fetch_movie_categories_list()
        self.assertGreater(len(resp), 0)
        for item in resp:
            self.assertIn('title', item)
            self.assertIn('url', item)
            self.assertRegexpMatches(item['url'], "^/gatunek/[0-9]*")

    def test_fetch_movies_list(self):
        resp = self.z.fetch_movies_list('/gatunek/22')
        self.assertGreater(len(resp), 0)
        for item in resp:
            self.assertIn('title', item)
            self.assertIn('url', item)
            self.assertRegexpMatches(item['url'], "^https://zalukaj.com/(zalukaj-film|gatunek,[0-9]+)/[a-z0-9-,./]+$")

    def test_login_correctly(self):
        resp = self.z.fetch_user_data()
        self.assertTrue(resp.is_logged())
        self.assertEqual(resp.name, TEST_CONFIG['display_name'])

    def test_fetch_tv_series_list(self):
        resp = self.z.fetch_tv_series_list()
        self.assertGreater(len(resp), 0)
        self.assertIn('title', resp[0])
        self.assertIn('url', resp[0])
        self.assertRegexpMatches(resp[0]['url'], "^/serial/[0-9a-z-]*.html$")

    def test_fetch_tv_series_seasons_list(self):
        resp = self.z.fetch_tv_series_seasons_list('/serial/simpsonowie-583.html')
        self.assertGreater(len(resp), 0)
        self.assertIn('title', resp[0])
        self.assertIn('img', resp[0])
        self.assertIn('url', resp[0])
        self.assertRegexpMatches(resp[0]['url'], "^/kategoria-serialu/[0-9,]*/[a-z0-9_]*/$")

    def test_fetch_tv_series_episodes_list(self):
        resp = self.z.fetch_tv_series_episodes_list('/kategoria-serialu/773656,1/simpsonowie_the_simpsons_sezon_30/')
        self.assertGreater(len(resp), 0)
        self.assertIn('img', resp[0])
        self.assertIn('title', resp[0])
        self.assertIn('episode', resp[0])
        self.assertIn('season', resp[0])
        self.assertIn('url', resp[0])
        self.assertRegexpMatches(resp[0]['url'], "^https://zalukaj.com/serial-online/[0-9]+/[a-z0-9-]+.html$")
        self.assertGreater(resp[0]['season'], 0)
        self.assertGreater(resp[0]['episode'], 0)

    def test_search_movies(self):
        resp = self.z.search_movies('futurama')
        self.assertGreater(len(resp), 0)
        for item in resp:
            self.assertIn('img', item)
            self.assertIn('title', item)
            self.assertIn('url', item)
            self.assertIn('description', item)
            self.assertIn('year', item)
            self.assertRegexpMatches(item['title'], re.compile("(futurama)", re.IGNORECASE))
