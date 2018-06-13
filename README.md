# Kodi zalukaj video plugin

This plugin provided streaming from [zalukaj.com](https://zalukaj.com) website.

**Currently plugin is highly maintained, changes are available in [changelog](./CHANGELOG.md)**    
Feel free to open any pull requests!

## Roadmap

### Planed for v1.0.0
- [x] login in zalukaj service and fetch basic data about account
- [x] stream tv series
- [ ] give possibility to list movies by genre
- [ ] give possibility to list last added / streamed movies
- [ ] stream movies (with quality select)
- [ ] documentation with tutorial about installation and usage
- [ ] updated unit and functional tests

### Planed for v1.1.0
- [ ] improve tv series and movies listing GUI (add descriptions and other properties)

### Planed for v1.2.0
- [ ] add search

### Planed for v1.3.0
- [ ] give possibility to stream movies for not logged in users and account without premium subscriptions

## Privacy

Plugin use user credentials (login and password), to fetch session cookie from zalukaj.com. This cookie is used in
every requests send to zalukaj.com service and is persisted in plugin directory under `zalukaj.cookie` name.     

Plugin author is not responsible for the inappropriate use of this data by other developers and Kodi team.