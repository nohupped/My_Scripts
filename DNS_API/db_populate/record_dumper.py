#!/usr/bin/python
import os, time, re, subprocess, tempfile
from db_populate import populate_forward
from db_populate import populate_ptr
#print dir(populate)
exclude_list = ['"." {', '"localhost" {', '"127.in-addr.arpa" {', '"0.in-addr.arpa" {', '"255.in-addr.arpa" {' ] ##Exclude the domains
file_list = []
forward_zones = []
ptr_zones = []
conf_dir = "/home/girish.g/"
journal = re.compile("^[a-zA-Z0-9_\-\.]+\.jnl$") # Find journal files
#arpa_journal = re.compile("^[0-9]+[a-zA-Z0-9_\-\.]+\.jnl$")
before = dict ([(f, None) for f in os.listdir (conf_dir)])

def pass_file(file_list): ###Freeze and thaw zones
	for line in file_list:
		if journal.search(line):
			line = re.sub("\.jnl", "", line)
			print "thawing" + line + "\n"
			subprocess.call(['/bin/echo', "thaw", line])

def combine_zones():  ###Combine all the zones based on PTR or Forward zones
	with open("/home/girish.g/named.conf.default-zones") as f:
		files = f.read()
		#print files
		files = re.compile("zone").split(files)
		#files = files.split("^$")
		for line in files:
			if any(exclude in line for exclude in exclude_list) or "file" not in line: ##Exclude unwanted zones
				continue
			elif "arpa" in line:    #Filter PTR zones
				zonefile = re.compile('\s+?file\s+?\"(.*)\"')
				zonefilesearch = zonefile.search(line)
				global ptr_zones
				ptr_zones.append(zonefilesearch.group(1))
			else:  ##Filter forward lookup zones
				zonefile = re.compile('\s+?file\s+?\"(.*)\"')
				zonefilesearch = zonefile.search(line)
				global forward_zones
				forward_zones.append(zonefilesearch.group(1))
	#	print str(ptr_zones)
	#	print str(forward_zones)
		##Create tmp file to write combined data
		tmp_filename_ptr = '/tmp/ptr_zones.%s.txt' % os.getpid()
		tmp_filename_forward = '/tmp/forward_zones.%s.txt' % os.getpid()
		temp_ptr = open(tmp_filename_ptr, 'w+b')
		#print temp_ptr
		with open(temp_ptr.name, 'w') as outfile_ptr:
			for fname in ptr_zones:
				with open(fname) as infile:
					for line in infile:
						outfile_ptr.write(line)
		temp_forward = open(tmp_filename_forward, 'w+b')
		#print temp_forward
		with open(temp_forward.name, 'w') as outfile_forward:
			for fname in forward_zones:
				with open(fname) as infile:
					for line in infile:
						outfile_forward.write(line)
		output_forward = populate_forward(temp_forward.name)	
		output_ptr = populate_ptr(temp_ptr.name)
		print output_forward
		print output_ptr
		ptr_zones = []
		forward_zones = []
		os.remove(temp_ptr.name)
		os.remove(temp_forward.name)
		#for line in files:
	#		return line
while 1:
	time.sleep (1)
	after = dict ([(f, None) for f in os.listdir (conf_dir)])
	added = [f for f in after if not f in before]
	if added: 
		pass_file(added)
		combine_zones() ##Push it under the above if
	before = after
