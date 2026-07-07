# ReTrak.tv scrobbler and library sync

### Table of Contents

- [What is ReTrak?](#what-is-retrak)
- [What can this addon do?](#what-can-this-addon-do)
- [What can be scrobbled?](#what-can-be-scrobbled)
- [Installation](#installation)
- [Problems?](#problems)
  - ["I found something that doesn't work"](#i-found-something-that-doesnt-work)
  - [Creating logfiles](#creating-logfiles)
  - [Invoke sync via JSON-RPC](#invoke-sync-via-jsonrpc)
- [Contribute](#contribute)
- [Thanks](#thanks)

---

### What is ReTrak?

Automatically scrobble all TV episodes and movies you are watching to ReTrak! Keep a comprehensive history of everything you've watched and be part of a community of TV and movie enthusiasts. Sign up for a free account at [ReTrak.tv](https://retrak.tv) and get a ton of features:

- Automatically scrobble what you're watching
- Personalized calendar so you never miss a TV show
- Follow your friends and track your progress
- Use watchlists so you don't forget what to watch
- Track your media collections

---

### What can this addon do?

- Automatically scrobble TV episodes and movies you are watching
- Sync your TV episode and movie collections to ReTrak (manually or triggered by a library update)
- Keep watched statuses synced between Kodi and ReTrak
- Rate movies and episodes after watching them
- Custom skin/keymap actions for toggling watched status and rating

---

### What can be scrobbled?

This plugin will scrobble local media and most remote streaming content. Local media should be played in Kodi library mode. ReTrak will attempt to identify the media through different third party IDs available from the metadata. TV shows are identified by TVDb ID or IMDb ID. Movies are identified by TMDb ID or IMDb ID. 

The best supported and recommended configuration is to use [TVDb](https://thetvdb.com/) (for TV shows) and [TMDb](https://themoviedb.org) (for movies) as your scrapers.

---

### Installation

If you are not a developer, you should install this add-on from a repository. If you are a developer, here is how you install it manually:

1. Clone this repository or download the ZIP archive.
2. Place or extract it into a folder called **script.retrak** inside your Kodi **addons** folder.
3. Start Kodi (or restart it if it's already running).
4. Make sure you have the required Kodi modules installed (including `dateutil`).
5. Navigate to *Settings* > *Add-ons* > *My add-ons* > *Services* > **ReTrak**.
6. Select *ReTrak* and go to **Configure**.
7. Under **General settings**:
   - Set your **ReTrak URL** (defaults to `https://retrak.tv`).
   - Enter your personal **ReTrak API Key** (typically starting with `dnt_`).
8. Select **OK** to save your settings.
9. Watch something and see it show up on your ReTrak dashboard!

---

### Problems?

#### "I found something that doesn't work"

- Search the issues on GitHub to see if it has already been reported, if so add your information there.
- If not, create a new issue and provide as much data about your system as possible, along with debug log files.

#### Creating logfiles

- To create a logfile, enable the debug settings in both Kodi and script.retrak, otherwise the logfile won't show any debugging details from script.retrak. Check the [Kodi documentation](http://kodi.wiki/view/Log_file) if you don't know where your logfile can be found.

#### Invoke sync via JSON-RPC

Save this as `kodi-retrak-update.sh`:

```bash
#!/bin/sh

# url to kodi jsonrpc
url=http://localhost:8080/jsonrpc

request='{
        "jsonrpc":"2.0",
        "method":"Addons.ExecuteAddon",
        "params":{
                "addonid":"script.retrak",
                "params":{
                        "action":"sync",
                        "silent":"False"
                }
        },
        "id":1
}'

exec curl -sSLf --include --header 'content-type: application/json;' --request POST --data-binary "$request" "$url"
```

---

### Thanks

- Special thanks to all who contribute to this plugin! Check the commit history and changelog to see these talented developers.
- Special thanks to fuzeman for [trakt.py](https://github.com/fuzeman/trakt.py).
