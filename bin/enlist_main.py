#! /usr/bin/python
import sys
import os
import os.path
import shutil
import re
import subprocess

cwd = "./"
verbose = False


# OS Helpers

def call(args):
	if verbose:
		print " ".join(args)
	return subprocess.call(args)


def check_output(args):
	if verbose:
		print " ".join(args)
	return subprocess.check_output(args)



# CONFIGURATION

class Config:
	name=None
	checkout=None
	repo=None
	path=None
	url=None
	branch=None

	def debug_print(self):
		print "[%s]\n\trepo=%s\n\tpath=%s\n\turl=%s\n\tbranch=%s\n\tcheckout=%s\n" % (self.name, self.repo, self.path, self.url, self.branch, self.checkout)

	def validate(self):
		if self.checkout is not None:
			if self.checkout.startswith("svn"):
				self.repo = "svn"
			if self.checkout.startswith("git"):
				self.repo = "git"
			m = re.search("\\shttps?://\\S*", self.checkout)
			if m is not None:
				self.url = m.string[m.start():m.end()].strip()

		if self.repo is None and self.checkout is not None:
			if self.checkout.startswith("svn"):
				self.repo = "svn"
			if self.checkout.startswith("git"):
				self.repo = "git"

		if self.path is None:
			self.path = self.name

# ENLIST

def enlist(config):
	os.chdir(cwd)
	if not os.path.isdir(config.path):
		os.makedirs(config.path)
	if config.repo == "git":
		enlist_git(config)
		switch_git(config)
	elif config.repo == "svn":
		enlist_svn(config)
		switch_svn(config)
	os.chdir(cwd)


def enlist_git(config):
	if os.path.isdir(config.path + "/.git"):
		check(config)
		return
	call(["git", "clone", config.url, config.path])
	if not None == config.branch:
		call(["git", "checkout", config.branch])


def enlist_svn(config):
	if os.path.isdir(config.path + "/.svn"):
		check(config)
		return
	call(["svn", "checkout", config.url, config.path])


# CHECK

def check(config):
	os.chdir(cwd)
	if not os.path.isdir(config.path):
		print "directory does not exist: " + config.path
		return False
	ok = True
	if config.repo == "git":
		ok = check_git(config)
	elif config.repo == "svn":
		ok = check_svn(config)
	os.chdir(cwd)
	return ok


def check_git(config):
	os.chdir(config.path)
	if not os.path.isdir(".git"):
		print "directory does not appear to have a git enlistment: " + os.getcwd()
		return False
	url = check_output(["git", "config", "--get", "remote.origin.url"])
	url = url.strip()
	if url != config.url:
		print "wrong remote url: %s" % (url)
		return False

	if config.branch is not None:
		branches = check_output(["git", "branch"])
		branches = branches.split("\n")
		found = False
		for branch in branches:
			if not branch.startswith("*"):
				continue
			branch = branch[2:]
			if branch == config.branch:
				found = True
			elif branch != config.branch:
				print "expected to find branch '%s' found '%s'" % (config.branch, branch)
				return False
		if not found:
			print "couldn't find current branch for %s" % (config.path)
			return False

	return True


def check_svn(config):
	os.chdir(config.path)
	if not os.path.isdir(".svn"):
		print "directory does not appear to have a subversion enlistment: " + os.getcwd()
		return False

	info = check_output(["svn", "info"])
	url = None
	for line in info.split("\n"):
		if not line.startswith("URL: "):
			continue
		line = line[5:]
		url = line.strip()
	if url != config.url:
		print "wrong remote url: %s" % (url)
		return False
	return True


# SWITCH

def switch_svn(config):
	call(["svn", "switch", config.url])
	return


def switch_git(config):
	if config.branch is None:
		print "no branch specified for " + config.name
		return
	os.chdir(config.path)
	call(["git", "checkout", config.branch])
	return


# MAIN

def parse_property(line):
	i = line.find("=")
	if -1==i:
		return (None,None)
	return line[:i].strip(), line[i+1:].strip()


def parse_configuration_file(config_file):
	configs = []
	config = None

	f = open(config_file,"r")
	for line in f.readlines():
		line = line.strip()
		if line.startswith("#") or line=="":
			continue
		if line.startswith("[") and line.endswith("]"):
			if config is not None:
				configs.append(config)
			config = Config()
			config.name = line[1:len(line)-1]
		if config is None:
			continue
		(key,value) = parse_property(line)
		if key=="checkout":
			config.checkout = value
		elif key=="repo":
			config.repo = value
		elif key=="url":
			config.url = value
		elif key=="branch":
			config.branch = value
	f.close()

	if config is not None:
		configs.append(config)
	for config in configs:
		config.validate()
	return configs


def main(argv):
	global cwd
	global verbose
	cwd = os.getcwd()

	config_file = None
	command = "check"
	for arg in argv:
		if arg=="enlist" or arg=="check" or arg=="sync":
			command = arg
		elif arg=="-v":
			verbose = True
		else:
			config_file = arg

	if config_file is None:
		if os.path.isfile(".mrconfig"):
			config_file = ".mrconfig"
			if verbose:
				"using configuration file .mrconfig"

	if config_file is None or command is None:
		print "Usage: enlist.py [enlist|check|sync] {config file}"
		sys.exit(1)

	configs = parse_configuration_file(config_file)

	if verbose:
		for config in configs:
			config.debug_print()

	if "enlist"==command:
		if ".mrconfig" != config_file:
			shutil.copyfile(config_file,".mrconfig")
		for config in configs:
			enlist(config)

	if "sync"==command:
		print "NYI"

	if "check"==command:
		OK = True
		for config in configs:
			ret = check(config)
			if not ret:
				OK = False
		if OK:
			print "looks good"


if __name__ == "__main__":
	main(sys.argv)
