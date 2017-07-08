AutoModUpdater
==============

This is a simple script allowing subreddit [AutoModerator](https://www.reddit.com/r/AutoModerator/) configurations to be edited locally in your favorite `$EDITOR`. It supports modifying the rule lists of multiple subreddits from a single rule list in one file. The YAML is cached locally and moved to/from Reddit as needed.

Requirements
------------

 * [Python 3](https://www.python.org/)
 * [PRAW 4.0.0+](https://praw.readthedocs.io/en/latest/index.html)
 * [ruamel.yaml](https://yaml.readthedocs.io/en/latest/index.html)

Setup
-----

Copy the example configuration to a file called `praw.ini` (which is expected to be in the same directory as the script), and edit at least the stuff in caps to suit your needs. Note that the `client_id` and `client_secret` values are obtained in your [account preferences](https://github.com/reddit/reddit/wiki/OAuth2-Quick-Start-Example#first-steps). The account used must be a moderator with `config` and `wiki` privileges in the target subreddits.

Usage
-----

Create your local copy of the rules from subreddits /r/foo, /r/bar, and /r/baz:

    $ amupdate.py init foo bar baz

Or create your local copy of the rules from all moderated subreddits:

    $ amupdate.py modinit

The local YAML file is named `rules.yaml`, and is stored in the directory with the script.

Push local updates to Reddit:

    $ amupdate.py push

Pull updates made on Reddit down to the local copy:

    $ amupdate.py pull

The `push` or `pull` commands will show a diff of changes, and ask for confirmation before applying. For push, the diff is by subreddit, but for pull, it is against your local file. Additionally, when pushing to Reddit, a commit message may be entered. The latter are cached using `readline`, and can be reused at subsequent prompts by pressing the up arrow.

When creating a new `config/automoderator` page, do so on Reddit, then rerun `init`. The `push` command does not create wiki pages.

Editing notes
-------------

* A new array is added to each rule in the local YAML file containing a list of subreddits to which it applies. These should stay sorted when modified to avoid extra updates when running `pull`. AutoModUpdater does this internally for the same purpose.
* Because `rules.yaml` is one file, precedence is shared between the subreddits. Keep this in mind when ordering the rules.
