#!/usr/bin/python
#if __name__ == '__main__':
#	print "Use as module"
import re, pprint, MySQLdb, warnings
import _mysql_exceptions ## To import mysql exceptions from /usr/lib/pymodules/python2.6/
warnings.filterwarnings('ignore', category = MySQLdb.Warning)

###Connection
db = MySQLdb.connect(host = "localhost", user = "root", passwd = "qazplm123")
cursor = db.cursor()

def populate_forward(zonefile):

	try:
		cursor.execute("drop database ddns_search_tmp")
		cursor.execute("create database ddns_search_tmp")
	except _mysql_exceptions.OperationalError:
		cursor.execute("create database ddns_search_tmp")

	cursor.execute("use ddns_search_tmp")	
	warnings.resetwarnings()
###
	create_table = """CREATE TABLE RECORD_SEARCH( id INT NOT NULL AUTO_INCREMENT, DOMAIN VARCHAR(100) NOT NULL, RECORD VARCHAR(100) NOT NULL, RECORD_POINTS_TO VARCHAR(100) NOT NULL, PRIORITY_MX VARCHAR(10) NOT NULL, TTL VARCHAR(100) NOT NULL, GENERATED_ON TIMESTAMP, PRIMARY KEY ( id ));"""
	cursor.execute(create_table)


	origin = re.compile("^\$ORIGIN.*")
	re_skip = re.compile("(\d+\s+?\;\s+serial|\d+\s+?\;\s+refresh|\d+\s+?\;\s+retry|\d+\s+?\;\s+expire|\d+\s+?\;\s+minimum|\s+?\)|\s+?NS\s+?localhost|IN\s+SOA)") ##Skip SOA and serial part
	origin_skip = re.compile("^\$ORIGIN\ \.$") ##Skip parent domain
	ttl = re.compile("^\$TTL.*")
	default_ttl = None
	primary_key = None
	value = []
	multiple_record = None
	committed_records = []
	rolledback_records = []
	count = 0
	rollback = 0
	#f = open (zonefile, 'r')

	with open(zonefile) as f:
		data_zones = f.readlines()

	for line in data_zones:

		if origin.search(line):
			if origin_skip.search(line):
				continue
			else:
				line = re.sub("\$ORIGIN\s+", ".", line)
				line = re.sub("\.\n", "", line)
				primary_key = line
				value = []
				multiple_record = None
				continue
		elif ttl.search(line):
#			if not bool(primary_key):
#				continue
#			else:
				default_ttl = line 
				default_ttl = re.sub(';.*', "", default_ttl)
				default_ttl = re.sub('\s+|\n|\$', '', default_ttl)
				value = []
				multiple_record = None
				continue
		else:
			if not bool(primary_key):
				continue
			else:
				if re_skip.search(line):
					continue
				value = line.strip()
				#print value
			value = value.split() 
			if value[0] == "A" or value[0] == "CNAME" or value[0] == "MX": ##Manage entries with multiple A records
				value.insert(0, multiple_record)# Manage entries with multiple A records
			multiple_record = value[0]
			value[0] = value[0] + primary_key
			#if "CNAME" in value:
			#	value[-1] = value[-1] + primary_key
			#print value
			if not "MX" in value:
				value.insert(2, "NA")
			insert_record = "INSERT INTO RECORD_SEARCH ( DOMAIN, RECORD, RECORD_POINTS_TO, PRIORITY_MX, TTL ) VALUES ('%s', '%s', '%s', '%s', '%s')" % (value[0], value[1], value[3], value[2], default_ttl)
	#		print insert_record
			try:
				cursor.execute(insert_record)
				db.commit()
				committed_records.append(insert_record)
				#print committed_records
				count += 1
			except:
				db.rollback()
				rolledback_records.append(insert_record)
	#			print rolledback_records
				rollback += 1
	warnings.filterwarnings('ignore', category = MySQLdb.Warning)
	cursor.execute("DROP DATABASE IF EXISTS ddns_search;")
	cursor.execute("CREATE DATABASE ddns_search;")
	cursor.execute("RENAME table ddns_search_tmp.RECORD_SEARCH TO ddns_search.RECORD_SEARCH;")
	return str(count) + " entries added and " + str(rollback) + " entries rolled back in forward zone"
	warnings.resetwarnings()
	#db.close()

def populate_ptr(zonefile):
	cursor.execute("use ddns_search_tmp")
	create_table = """CREATE TABLE RECORD_SEARCH_PTR( id INT NOT NULL AUTO_INCREMENT, IP VARCHAR(20) NOT NULL, RECORD VARCHAR(100) NOT NULL, IP_POINTS_TO VARCHAR(100) NOT NULL, TTL VARCHAR(100) NOT NULL, GENERATED_ON TIMESTAMP, PRIMARY KEY ( id ));"""
	try:
		cursor.execute(create_table)
	except _mysql_exceptions.OperationalError:
		cursor.execute("drop table RECORD_SEARCH_PTR")
		cursor.execute(create_table)

	origin = re.compile("^\$ORIGIN.*")
	re_skip = re.compile("(\d+\s+?\;\s+serial|\d+\s+?\;\s+refresh|\d+\s+?\;\s+retry|\d+\s+?\;\s+expire|\d+\s+?\;\s+minimum|\s+?\)|\s+?NS\s+?localhost|IN\s+SOA)") ##Skip SOA and serial part
	origin_skip = re.compile("^\$ORIGIN\ \.$") ##Skip parent domain
	ttl = re.compile("^\$TTL.*")
	default_ttl = None
	primary_key = None
	value = []
	multiple_record = None
	committed_records_ptr = []
	rolledback_records_ptr = []
	count_ptr = 0
	rollback_ptr = 0
	with open(zonefile) as f:
		data_zones = f.readlines()
	for line in data_zones:
		if origin.search(line):
			if origin_skip.search(line):
				continue
			else:
				line = re.sub("\$ORIGIN\s+", ".", line).strip()
	#			line = ".".join(re.sub("\.in\-addr\.arpa\.", "", line).split(".")[::-1])
				line = re.sub("\.$","", ".".join(re.sub("\.in\-addr\.arpa\.", "", line).split(".")[::-1]))
#				print line
				primary_key = line
				value = []
				multiple_record = None
				continue
		elif ttl.search(line):
			default_ttl = line
			default_ttl = re.sub(';.*', "", default_ttl)
			default_ttl = re.sub('\s+|\n|\$', '', default_ttl)
			value = []
			multiple_record = None
			continue
		else:
			if not bool(primary_key):
				continue
			else:
				if re_skip.search(line):
					continue
				value = line.strip()
				value = value.split()
				if value[0] == "PTR":
					value.insert(0, multiple_record)
				multiple_record = value[0]
				value[0] = primary_key + "." + value[0]
				#print len(value)
				insert_record = "INSERT INTO RECORD_SEARCH_PTR ( IP, RECORD, IP_POINTS_TO, TTL ) VALUES ('%s', '%s', '%s', '%s')" % (value[0], value[1], value[2], default_ttl)
#				print insert_record
				try:
					cursor.execute(insert_record)
					db.commit()
					committed_records_ptr.append(insert_record)
					count_ptr += 1
				except:
					db.rollback()
					rolledback_records_ptr.append(insert_record)
					rollback_ptr += 1
	cursor.execute("DROP TABLE IF EXISTS ddns_search.RECORD_SEARCH_PTR")
	cursor.execute("RENAME table ddns_search_tmp.RECORD_SEARCH_PTR TO ddns_search.RECORD_SEARCH_PTR;")
	return str(count_ptr) + " entries added and " + str(rollback_ptr) + " entries rolled back in PTR zone"
