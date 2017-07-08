#!/usr/bin/python3

import argparse
import collections
import difflib
import errno
import glob
import os
import praw
import pydoc
import readline
import sys

def concatconf(sub, myconf):
    """Combine shared and sub-specific local conf."""
    if not myconf[sub]:
        concat = myconf["all"]
    else:
        concat = "{}---\n{}".format(myconf["all"], myconf[sub])
    return concat

def gendiff(sub, myfrom, myto, fromfile, tofile):
    """Generate and page a diff for the given YAML."""
    diff = difflib.unified_diff(
            myfrom.splitlines(),
            myto.splitlines(),
            fromfile,
            tofile)
    try:
        n = next(diff)
    except:
        print("{}: up-to-date".format(sub))
        return False
    pydoc.pager("\n".join(diff))
    return True

def init(r, mypath, mycmd):
    """Create new local copy of configs."""
    os.makedirs("{}/AutoMod".format(mypath), exist_ok=True)
    liveconf = remoteconf(r, mycmd.subreddit)
    rules = sharedconf(mycmd.subreddit, liveconf)
    myconf = {}
    if ["all"] in rules.values():
        myconf["all"] = ""
    for sub in mycmd.subreddit:
        myconf[sub] = ""
    for rule in rules:
        for sub in rules[rule]:
            myconf[sub] += "---\n"
            myconf[sub] += rule
    for sub in myconf:
        path = "{}/AutoMod/{}.yaml".format(mypath, sub)
        writeyaml(path, myconf[sub][4:])

def localconf(mypath):
    """Return YAML from config directory beside ourself"""
    myyaml = glob.glob("{}/AutoMod/*.yaml".format(mypath))
    myconf = {}
    for rules in myyaml:
        sub = os.path.splitext(os.path.basename(rules))[0]
        conf = open(rules, "r")
        myconf[sub] = conf.read()
        conf.close()
    if myconf:
        return myconf
    else:
        print("No local rules")
        sys.exit(os.EX_NOINPUT)

def pull(r, mypath, mycmd):
    """Update local copy of configs."""
    oldconf = localconf(mypath)
    liveconf = remoteconf(r, list(oldconf))
    rules = sharedconf(list(liveconf), liveconf)
    myconf = {}
    if ["all"] in rules.values():
        myconf["all"] = ""
    for sub in list(liveconf):
        myconf[sub] = ""
    for rule in rules:
        for sub in rules[rule]:
            myconf[sub] += "---\n"
            myconf[sub] += rule
    for sub in list(myconf):
        myfrom = oldconf[sub]
        myto = myconf[sub][4:]
        fromfile = "{}/AutoMod/{}.yaml".format(mypath, sub)
        tofile = "/r/{}/wiki/config/automoderator".format(sub)
        update = gendiff(sub, myfrom, myto, fromfile, tofile)
        if not update:
            continue
        if verify(sub):
            path = "{}/AutoMod/{}.yaml".format(mypath, sub)
            writeyaml(path, myto)

def push(r, mypath, mycmd):
    """Update live configs from local copy."""
    myconf = localconf(mypath)
    liveconf = remoteconf(r, list(myconf))
    for sub in list(liveconf):
        try:
            myfrom = liveconf[sub].content_md.replace("\r\n", "\n")
        except:
            print("{}: trouble reading wiki page".format(sub))
            continue
        myto = concatconf(sub, myconf)
        fromfile = "/r/{}/wiki/config/automoderator".format(sub)
        tofile = "{}/AutoMod/{{all,{}}}.yaml".format(mypath, sub)
        update = gendiff(sub, myfrom, myto, fromfile, tofile)
        if not update:
            continue
        if verify(sub):
            reasons = input("Commit message: ")
            try:
                liveconf[sub].edit(myto, reasons)
            except:
                print("{}: trouble editing wiki page".format(sub))
                continue

def remoteconf(r, subs):
    """Return AutoModerator wiki pages from subreddit configs."""
    rconf = {}
    if "all" in subs:
        subs.remove("all")
    for sub in subs:
        page = r.subreddit(sub).wiki["config/automoderator"]
        rconf[sub] = page
    return rconf

def sharedconf(subs, liveconf):
    """Return full config with shared rules tagged."""
    myconf = collections.OrderedDict()
    for sub in subs:
        try:
            rules = liveconf[sub].content_md.replace("\r\n", "\n").split("---\n")
        except:
            print("{}: trouble reading wiki page".format(sub))
            continue
        if "" in rules:
            rules.remove("")
        for rule in rules:
            if rule in myconf:
                myconf[rule].append(sub)
            else:
                myconf[rule] = [sub]
    for rule in myconf:
        if len(subs) == len(myconf[rule]):
            myconf[rule] = ["all"]
    return myconf

def verify(sub):
    """Query for confirmation of sub update."""
    line = input("Update /r/{} [Y/n]: ".format(sub))
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
    ap_pull = sap.add_parser("pull", help="update local copy of configs")
    ap_push = sap.add_parser("push", help="update live configs from local copy")
    return ap.parse_args()

def writeyaml(path, rules):
    """Output a new local YAML file."""
    conf = open(path, "w")
    conf.write(rules)
    conf.close()

if __name__ == "__main__":
    mypath = os.path.dirname(os.path.realpath(__file__))
    mycmd = whatdo()
    commands = {"init": init, "pull": pull, "push": push}
    commands[mycmd.command](praw.Reddit(), mypath, mycmd)
