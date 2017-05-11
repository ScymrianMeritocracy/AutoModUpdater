AutoModUpdater
==============

This is a simple script allowing subreddit [AutoModerator](https://www.reddit.com/r/AutoModerator/) configurations to be edited locally in your favorite $EDITOR. It also supports adding/removing a rule from a list of subreddits by doing so in a single file. The YAML is cached locally and moved to/from Reddit as needed.

Requirements
------------

 * [Python 3](https://www.python.org/)
 * [PRAW4](https://praw.readthedocs.io/en/praw4/index.html)

Setup
-----

Copy the example configuration to a file called `praw.ini` (which is expected to be in the same directory as the script), and edit at least the stuff in caps to suit your needs. Note that the `client_id` and `client_secret` values are obtained in your [account preferences](https://github.com/reddit/reddit/wiki/OAuth2-Quick-Start-Example#first-steps). The account used must be a moderator with `config` and `wiki` privileges in the target subreddits.

Usage
-----

Create your local copy of the rules from subreddits /r/foo, /r/bar, and /r/baz:

    $ amupdate.py init foo bar baz

Local YAML files are stored in an `AutoMod` directory with the script. An `all.yaml` file will also be created if there are any rules shared between every targeted subreddit.

Push local updates to Reddit:

    $ amupdate.py push

Pull updates made on Reddit down to the local copies:

    $ amupdate.py pull

The `push` or `pull` commands will show a diff, by subreddit, of changes, and ask for confirmation before applying. Additionally, when pushing to Reddit, a commit message may be entered. The latter are cached using `readline`, and can be reused at subsequent prompts by pressing the up arrow.

When creating a new `config/automoderator` page, do so on Reddit, then touch a local YAML file and run `pull`. The `push` command does not create wiki pages.
