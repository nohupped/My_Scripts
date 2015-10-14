#!/usr/bin/python
import ldap
import os
import multiprocessing
import sys
import pwd
import grp
from collections import defaultdict
import logging


# Variables
multiprocessing.log_to_stderr(logging.INFO)
adserver = "xxx.xxx.xxx.xxx"  # AD Server, will change it to accept as parameter later
# For storing top level directories for traversing in parallel
tld = [os.path.join("/", f) for f in os.walk("/").next()[1]]
exclude = ["/sys", "/proc", "/dev", "/run", "/var", "/dummy"]  # exclude directories
manager_filelist = multiprocessing.Manager()
files = manager_filelist.list()  # Initial File list
manager_attributes = multiprocessing.Manager()
current_users = manager_attributes.dict()  # Current usr list for ldap lookup
current_groups = manager_attributes.dict()  # Current grp list for ldap lookup
manager_ldapusers = multiprocessing.Manager()


def get_files(x):  # Get current file list
    print "Getting Filelist from", x
    for root, dir, file in os.walk(x):
        for name in file:
            files.append(os.path.join(root, name))
    print "Finished collecting file list from", x


def connect_ldap():
    try:
        print "Connecting to ldap"
        l = ldap.open(adserver)
        username = "cn=xxx,cn=xxx,dc=xxx,dc=xxx,dc=xxx"
        password = "xxxxxx"
        basedn = "ou=xxx,dc=xxx,dc=xxx,dc=xxx"
#   filter = "(sAMAccountName="+"girish.g"+")"
        l.simple_bind_s(username, password)
    except Exception, e:
        print e
        sys.exit(1)
    result = l.search_s(basedn, ldap.SCOPE_SUBTREE)
    return [entry for dn, entry in result if isinstance(entry, dict)]
    print "Ldapsearch gathered"


def filestat(file):
    try:
        stat = os.lstat(file)
        user = pwd.getpwuid(stat[4])[0]
        group = grp.getgrgid(stat[5])[0]
        return user, group, file
    except OSError, e:
        print e
        return None


def get_attributes():
    try:
        cores = (multiprocessing.cpu_count()*2)
    except:
        cores = 8
    print "Starting parallel execution with ", cores, "concurrency"
    pool_get_attributes = multiprocessing.Pool(cores)
    result_map = pool_get_attributes.map(filestat, files)
    pool_get_attributes.close()
    pool_get_attributes.join()
    result_user = defaultdict(lambda: defaultdict(list))
    result_group = defaultdict(lambda: defaultdict(list))
    for user, group, file in (r for r in result_map if r is not None):
        result_user[user]["file"].append(file)
        result_group[group]["file"].append(file)
    return result_user, result_group


def map_ldap_local_users(ldap_users, file_user, file_group):
    for i in ldap_users:
        try:
            username = "".join(i["sAMAccountName"])
            if username in file_user:
                file_user[username]["ldap_uidnumber"].append(["".join(i["uidNumber"])])
            else:
                pass
        except Exception, e:
            print e
            pass


def accept_input(func, *args):
    while True:
        ch = raw_input("press Y to continue, ctrl-c to exit")
        if ch != "Y":
            pass
        else:
            func(*args)
            break


def chown_files(file_user, common_users):
    for i in common_users:
        print "chowning", file_user[i]["file"], " to ", file_user[i]["ldap_uidnumber"]
        chown_MP(file_user[i]["ldap_uidnumber"], file_user[i]["file"])


def chown_MP(ldap_uidnumber, filelist):
    print ldap_uidnumber
    ldap_uidnumber = "".join("".join(map(str, l)) for l in ldap_uidnumber)
    filelist_with_uid = [(int(ldap_uidnumber), f) for f in filelist]
    print filelist_with_uid
    try:
        cores = (multiprocessing.cpu_count()*2)
    except:
        cores = 8
    pool_chown = multiprocessing.Pool(cores)
    pool_chown.map(chown_worker, filelist_with_uid)
    pool_chown.close()
    pool_chown.join()


def chown_worker(filelist_with_uid):
    print "chown", filelist_with_uid[0], filelist_with_uid[1]
    os.chown(filelist_with_uid[1], filelist_with_uid[0], -1)


def main():  # Calling all functions
    print "Starting parallel execution"
    pool_filelist = multiprocessing.Pool(processes=len(tld))
    pool_filelist.map(get_files, [x for x in tld if x not in exclude])
    pool_filelist.close()
    pool_filelist.join()
    print "Initialising concurrency and collecting file attributes"
    file_user, file_group = get_attributes()
    ldap_users = connect_ldap()
    map_ldap_local_users(ldap_users, file_user, file_group)
    users_without_ldap_uid = []
    local_only_users = []
    common_users = []
    for i in file_user:
        if "ldap_uidnumber" in file_user[i] and not file_user[i]["ldap_uidnumber"]:
            users_without_ldap_uid.append(i)
        elif "ldap_uidnumber" not in file_user[i]:
            local_only_users.append(i)
        else:
            common_users.append(i)
    print "**********Users with no UID number enabled on AD, but locally exists**********\n"
    print users_without_ldap_uid
    print "******************************************************************************\n\n"
    print "**********Local only users**********\n"
    print local_only_users
    print "************************************\n\n"
    print "**********Common Users**********\n"
    print common_users
    print "********************************\n\n"
    print "**********Files owned by common users**********\n"
    for i in common_users:
        print "## These files will be chowned to ldap uid", file_user[i]["ldap_uidnumber"], "##\n"
        print file_user[i]["file"]
    accept_input(chown_files, file_user, common_users)
    print "input accepted"
main()  # Execution
