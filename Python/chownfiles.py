#!/usr/bin/python
import ldap
import os
import multiprocessing
import sys
import pwd
import grp
# from collections import defaultdict

# import logging
'''
Thanks to http://code.activestate.com, the below try: except block is copied from
http://code.activestate.com/recipes/523034-emulate-collectionsdefaultdict/
for default dict backward compatibility with python versions < 1.7.x
'''
try:
    from collections import defaultdict
except:
    class defaultdict(dict):
        def __init__(self, default_factory=None, *a, **kw):
            if (default_factory is not None and not hasattr(default_factory, '__call__')):
                raise TypeError('first argument must be callable')
            dict.__init__(self, *a, **kw)
            self.default_factory = default_factory

        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                return self.__missing__(key)

        def __missing__(self, key):
            if self.default_factory is None:
                raise KeyError(key)
            self[key] = value = self.default_factory()
            return value

        def __reduce__(self):
            if self.default_factory is None:
                args = tuple()
            else:
                args = self.default_factory,
            return type(self), args, None, None, self.items()

        def copy(self):
            return self.__copy__()

        def __copy__(self):
            return type(self)(self.default_factory, self)

        def __deepcopy__(self, memo):
            import copy
            return type(self)(self.default_factory,
                              copy.deepcopy(self.items()))

        def __repr__(self):
            return 'defaultdict(%s, %s)' % (self.default_factory,
                                            dict.__repr__(self))
# Variables
# multiprocessing.log_to_stderr(logging.INFO)
# passwd = raw_input("Enter ldap passsword to bind: ")
adserver = "AD.SERVER.IP"  # AD Server
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
        for subdirname in dir:
            files.append(os.path.join(root, subdirname))
    print "Finished collecting file list from", x


def connect_ldap():  # using raw_input to avoid passing credentials as parameters and getting logged in shell history.
    import getpass
    username = raw_input("Enter username (eg: cn=username,dc=Users,dc=example,dc=com): ")
    bsdn = raw_input("Enter Basedn to search (eg: ou=OU,dc=example,dc=com): ")
    passwd = getpass.getpass('Enter ldap password to bind: ')
    try:
        print "Connecting to ldap"
        l = ldap.open(adserver)
        username = username
        password = passwd
        basedn = bsdn
#   filter = "(sAMAccountName="+"girish.g"+")"
        l.simple_bind_s(username, password)
        print "Connection established, getting users list"
    except Exception, e:
        print e
        sys.exit(1)
    result = l.search_s(basedn, ldap.SCOPE_SUBTREE)
    print "Ldapsearch gathered"
    return [entry for dn, entry in result if isinstance(entry, dict)]


def filestat(file):
    try:
        stat = os.lstat(file)
        user = pwd.getpwuid(stat[4])[0]
        group = grp.getgrgid(stat[5])[0]
        return user, group, file
    except Exception, e:
        print e
        print file
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
                file_user[username]["ldap_gidnumber"].append(["".join(i["gidNumber"])])
            else:
                pass
        except Exception, e:
            print e
            pass


def accept_input(func, *args):
    while True:
        ch = raw_input("press Y to continue, ctrl-c to exit: ")
        if ch != "Y":
            pass
        else:
            func(*args)
            break


def chown_files(file_user, common_users):
    for i in common_users:
        print 'chowning and chgrping', file_user[i]["file"], ' to ', file_user[i]["ldap_uidnumber"], " and ", file_user[i]["ldap_gidnumber"]
        chown_MP(file_user[i]["ldap_uidnumber"], file_user[i]["ldap_gidnumber"], file_user[i]["file"])


def chown_MP(ldap_uidnumber, ldap_gidnumber, filelist):
    ldap_uidnumber = "".join("".join(map(str, l)) for l in ldap_uidnumber)
    ldap_gidnumber = "".join("".join(map(str, l)) for l in ldap_gidnumber)
    filelist_with_ids = [(int(ldap_uidnumber), int(ldap_gidnumber), f) for f in filelist]
    print filelist_with_ids
    try:
        cores = (multiprocessing.cpu_count()*2)
    except:
        cores = 8
    pool_chown = multiprocessing.Pool(cores)
    pool_chown.map(chown_worker, filelist_with_ids)
    pool_chown.close()
    pool_chown.join()


def chown_worker(filelist_with_ids):
    print "chown", filelist_with_ids[0], filelist_with_ids[1]
    try:
        os.chown(filelist_with_ids[2], filelist_with_ids[0], filelist_with_ids[1])
    except Exception, e:
        print e
        pass


def main():  # Calling all functions
    ldap_users = connect_ldap()
    print "Starting parallel execution"
    pool_filelist = multiprocessing.Pool(processes=len(tld))
    pool_filelist.map(get_files, [x for x in tld if x not in exclude])
    pool_filelist.close()
    pool_filelist.join()
    # files_new = list(files)
    print "Initialising concurrency and collecting file attributes"
    file_user, file_group = get_attributes()
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
    print "**********Common Users who has files in their ownership**********\n"
    print common_users
    print "********************************\n\n"
    print "**********Files owned by common users**********\n"
    for i in common_users:
        print "## These files will be chowned to ldap uid", file_user[i]["ldap_uidnumber"], "and chgrped to ", file_user[i]["ldap_gidnumber"], "##\n"
        print file_user[i]["file"]
    accept_input(chown_files, file_user, common_users)
    print "Ownership of files changed. Please verify once."

main()  # Execution
