# Kodi zalukaj video plugin

This plugin provided streaming from [zalukaj.com](https://zalukaj.com) website.

**Currently plugin is highly maintained, changes are available in [changelog](./CHANGELOG.md)**    
Feel free to open any pull requests!

## Roadmap

### Planed for v1.0.0
- [x] login in zalukaj service and fetch basic data about account
- [x] stream tv series
- [x] give possibility to list movies by genre
- [x] stream movies (with quality select)
- [x] updated unit and functional tests
- [ ] give possibility to list last added / streamed movies
- [ ] documentation with tutorial about installation and usage

### Planed for v1.1.0
- [ ] improve tv series and movies listing GUI (add descriptions and other properties)

### Planed for v1.2.0
- [ ] add search

### Planed for v1.3.0
- [ ] give possibility to stream movies for not logged in users and account without premium subscriptions

## Create package

Before package generation remember to update version in `addon.xml` and `addon.xml.md5`.       
Package zip is created from source in `plugin.video.zalukaj`. To create another package marked as version `0.0.1` just type:
```bash
$ python make_package.py 0.0.1
```

## Functional test

To start functional test fill details into dict named `TEST_CONFIG` in `zalukaj_test.py`.     
Remember to fill real account because this test checks real responses.

```bash
python -m unittest discover -s plugin.video.zalukaj --pattern "*_test.py"
```

## Privacy

Plugin use user credentials (login and password), to fetch session cookie from zalukaj.com. This cookie is used in
every requests send to zalukaj.com service and is persisted in plugin directory under `zalukaj.cookie` name.     

Plugin author is not responsible for the inappropriate use of this data by other developers and Kodi team.