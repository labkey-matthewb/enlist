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
		print "$", " ".join(args)
	return subprocess.call(args)


def check_output(args):
	if verbose:
		print "$", " ".join(args)
	return subprocess.check_output(args, stderr=subprocess.STDOUT)



# CONFIGURATION

class Config:
	name=None
	checkout=None
	repo=None
	path=None
	url=None
	branch=None

	def debug_print(self):
		print "[%s]\n\trepo=%s\n\tpath=%s\n\turl=%s\n\tbranch=%s" % (self.name, self.repo, self.path, self.url, self.branch)


	def validate(self):
		if self.checkout:
			if self.checkout.startswith("svn"):
				self.repo = "svn"
			if self.checkout.startswith("git"):
				self.repo = "git"
			m = re.search("\\s(https?://\\S*)", self.checkout)
			if m:
				self.url = m.group(1)
			m = re.search("\\s(-b|--branch)\\s*(\\S*)", self.checkout)
			if m:
				self.branch = m.group(2)

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


def enlist_sanity_check(configs):
	root = find_repository_root()
	if root and not compare_paths(cwd,root):
		print "! this does not seem to be a repository root"
		sys.exit(1)
	#TODO: check if parent is a repository, etc.
	return True


def find_repository_root():
	global cwd
	info = None
	working_copy = None

	# could be more general, but just handle svn case
	try:
		info = check_output(["svn", "info"])
		working_copy = None
		for line in info.split("\n"):
			if line.startswith("Working Copy Root Path: "):
				return line[len("Working Copy Root Path: "):].strip()
	except subprocess.CalledProcessError:
		None

	try:
		info = check_output(["git", "rev-parse", "--show-toplevel"])
		return info.strip()
	except subprocess.CalledProcessError:
		None

	return None


def compare_paths(a,b):
	a = os.path.normpath(a)
	b = os.path.normpath(b)
	return a.lower() == b.lower()

# CHECK

def check(config):
	os.chdir(cwd)
	if not os.path.isdir(config.path):
		print "! directory does not exist: " + config.path
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
		print "! directory does not appear to have a git enlistment: " + os.getcwd()
		return False
	url = check_output(["git", "config", "--get", "remote.origin.url"])
	url = url.strip()
	if not compare_url(url,config.url):
		print "! wrong remote url: %s" % (url)
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
				print "! expected to find branch '%s' found '%s'" % (config.branch, branch)
				return False
		if not found:
			print "! couldn't find current branch for %s" % (config.path)
			return False

	return True


def check_svn(config):
	os.chdir(config.path)
	if not os.path.isdir(".svn"):
		print "! directory does not appear to have a subversion enlistment: " + os.getcwd()
		return False

	info = check_output(["svn", "info"])
	url = None
	for line in info.split("\n"):
		if not line.startswith("URL: "):
			continue
		line = line[5:]
		url = line.strip()
	if not compare_url(url,config.url):
		print "! wrong remote url: %s" % (url)
		return False
	return True


def compare_url(a,b):
	a = a.lower()
	b = b.lower()
	if a.startswith("http://"):
		a = a[7:]
	elif a.startswith("https://"):
		a = a[8:]
	if b.startswith("http://"):
		b = b[7:]
	elif b.startswith("https://"):
		b = b[8:]
	if a.startswith("www."):
		a = a[4:]
	if b.startswith("www."):
		b = b[4:]
	return a.lower() == b.lower()


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
	for arg in argv[1:]:
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
	enlist_sanity_check(configs)

	if "enlist"==command:
		if ".mrconfig" != config_file:
			shutil.copyfile(config_file,".mrconfig")
		for config in configs:
			if verbose:
				config.debug_print()
			enlist(config)
			if verbose:
				print

	if "check"==command:
		OK = True
		for config in configs:
			if verbose:
				config.debug_print()
			ret = check(config)
			if not ret:
				OK = False
			if verbose:
				print
		if OK:
			print "looks good"


if __name__ == "__main__":
	main(sys.argv)
