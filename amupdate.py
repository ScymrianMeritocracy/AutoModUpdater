#!/usr/bin/python

import argparse
import bisect
import collections
import difflib
import os
import praw
import pydoc
import readline
import ruamel.yaml
import sys

try:
    input = raw_input
except NameError:
    pass

def concatconf(sub, conf):
    """Return concatented rule list from loaded configs."""
    list = ""
    first = True
    for rule in conf:
        if sub in conf[rule] or sub == "all":
            if first:
                first = False
            else:
                list += "---\n"
            list += "{}\n".format(rule)
            if sub == "all":
                list += "subreddits: ["
                list += ", ".join(conf[rule])
                list += "]\n"
    return list.rstrip()

def dumprules(r, subs):
    """Return mapping of rules to subreddits from sub configs."""
    live = collections.OrderedDict()
    for sub in subs:
        page = r.subreddit(sub).wiki["config/automoderator"]
        try:
            rules = page.content_md.replace("\r\n", "\n").split("\n---\n")
        except:
            print("{}: trouble reading wiki page".format(sub))
            continue
        if "" in rules:
            rules.remove("")
        for rule in rules:
            chomped = rule.rstrip()
            if chomped in live:
                if sub not in live[chomped]:
                    bisect.insort_left(live[chomped], sub)
            else:
                live[chomped] = [sub]
    return live

def gendiff(sub, myfrom, myto, myfromfile, mytofile):
    """Generate and page a diff for the given YAML."""
    diff = difflib.unified_diff(
            myfrom.splitlines(),
            myto.splitlines(),
            fromfile=myfromfile,
            tofile=mytofile,
            lineterm="")
    try:
        first = next(diff)
    except:
        print("{}: up-to-date".format(sub))
        return False
    pydoc.pager("{}\n{}".format(first, "\n".join(diff)))
    return True

def init(r, mypath, mycmd):
    """Create new local config from rule mapping."""
    mycmd.subreddit.sort()
    live = dumprules(r, mycmd.subreddit)
    writeyaml(mypath, live)

def loadrules(mypath):
    """Return mapping of rules from config file beside ourself."""
    local = collections.OrderedDict()
    path = "{}/rules.yaml".format(mypath)
    try:
        with open(path, "r") as conf:
            key, value = "", []
            for line in conf:
                if line.startswith("subreddits"):
                    value = ruamel.yaml.safe_load(line)["subreddits"]
                    value.sort()
                elif line.startswith("---"):
                    local[key.rstrip()] = value
                    key = ""
                else:
                    key += line
            local[key.rstrip()] = value
        return local
    except:
        print("Trouble reading local rules")
        sys.exit(os.EX_IOERR)

def modinit(r, mypath, mycmd):
    """Init with all subreddits moderated."""
    subs = []
    mod = r.user.moderator_subreddits()
    for sub in mod:
        subs.append(sub.display_name)
    subs.sort()
    live = dumprules(r, subs)
    writeyaml(mypath, live)

def pull(r, mypath, mycmd):
    """Update local copy of configs."""
    local = loadrules(mypath)
    subs = sublist(local)
    live = dumprules(r, subs)
    myfrom = concatconf("all", local)
    myto = concatconf("all", live)
    update = gendiff("rules.yaml", myfrom, myto, "rules.yaml", "Reddit")
    if update and verify("rules.yaml"):
        writeyaml(mypath, live)

def push(r, mypath, mycmd):
    """Update live configs from local copy."""
    local = loadrules(mypath)
    subs = sublist(local)
    live = dumprules(r, subs)
    for sub in subs:
        myfrom = concatconf(sub, live)
        myto = concatconf(sub, local)
        myfromfile = "/r/{}/wiki/config/automoderator".format(sub)
        update = gendiff(sub, myfrom, myto, myfromfile, "rules.yaml")
        if update and verify(sub):
            reasons = input("Commit message: ")
            try:
                r.subreddit(sub).wiki["config/automoderator"].edit(myto, reasons)
            except:
                print("{}: trouble editing wiki page".format(sub))
                continue

def sublist(conf):
    """Return list of subreddits from loaded configs."""
    subs = set()
    for rule in conf:
        for sub in conf[rule]:
            subs.add(sub)
    subs = list(subs)
    subs.sort()
    return subs

def verify(dest):
    """Query for confirmation of sub update."""
    line = input("Update {} [Y/n]: ".format(dest))
    readline.remove_history_item(readline.get_current_history_length() - 1)
    if line == "Y":
        return True

def whatdo():
    """Handle argument parsing."""
    ap = argparse.ArgumentParser(__file__)
    sap = ap.add_subparsers(dest="command", help="operation to perform")
    sap.required = True
    ap_init = sap.add_parser("init", help="create new local copy of configs")
    ap_init.add_argument("subreddit", nargs="+", help="a subreddit name")
    ap_modinit = sap.add_parser(
            "modinit",
            help="create new local copy of configs from all moderated")
    ap_pull = sap.add_parser("pull", help="update local copy of configs")
    ap_push = sap.add_parser("push", help="update live configs from local copy")
    return ap.parse_args()

def writeyaml(mypath, conf):
    """Output a local YAML file."""
    path = "{}/rules.yaml".format(mypath)
    rules = open(path, "w")
    rules.write(concatconf("all", conf))
    rules.write("\n")
    rules.close()

if __name__ == "__main__":
    mypath = os.path.dirname(os.path.realpath(__file__))
    mycmd = whatdo()
    commands = {"init": init, "modinit": modinit, "pull": pull, "push": push}
    commands[mycmd.command](praw.Reddit(), mypath, mycmd)
