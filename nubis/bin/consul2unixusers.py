#!/usr/bin/python

import os
import sys
import ConfigParser
import optparse
import consul

DRYRUN=False
_config = {}

def load_config(config_file):
    global _config
    if not os.path.exists(config_file):
        print "ERROR: Config file %s not found." % config_file
        sys.exit(-1)
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    if 'consul' not in config.sections():
        print "ERROR: [consul] section not found in %s." % config_file
        sys.exit(-1)
    _config = config

def process_arguments():
    parser = optparse.OptionParser(version="%prog 0.1")
    parser.set_usage("%prog [options]\nRead users from Consul and create them")
    parser.add_option('-d', '--dry-run', action='store_true', dest='dryrun',
        help="Show, but do not execute, any commands")
    (options, args) = parser.parse_args()
    return options

def readUsersFromConsul():
    users = {}
    consul_host = _config.get('consul', 'server')
    consul_port = _config.get('consul', 'port')
    consul_scheme = _config.get('consul', 'scheme')
    consul_path = _config.get('consul', 'path')
    c = consul.Consul(host=consul_host, port=consul_port, scheme=consul_scheme)
    x = c.kv.get(consul_path, keys=True, separator='/')
    if x[1] == None:
        print "ERROR: No keys returned from Consul at %s://%s:%s/%s" % (
            consul_scheme, consul_host, consul_port, consul_path)
        sys.exit(-1)
    ldapCNs = x[1]
    for key in ldapCNs:
        uid = c.kv.get(key + 'uid')[1]["Value"]
        users[uid] = {}
        users[uid]["homeDirectory"] = c.kv.get(key + 'homeDirectory')[1]["Value"]
        users[uid]["loginShell"] = c.kv.get(key + 'loginShell')[1]["Value"]
        users[uid]["mail"] = c.kv.get(key + 'mail')[1]["Value"]
        users[uid]["uidNumber"] = c.kv.get(key + 'uidNumber')[1]["Value"]
        users[uid]["sshPublicKey"] = {}
        sshkeys = c.kv.get(key + 'sshPublicKey/', keys=True, separator='/')[1]
        for keypath in sshkeys:
            keynumber = keypath.split('/')[-1]
            users[uid]["sshPublicKey"][keynumber] = c.kv.get(keypath)
    return users

def main():
    global DRYRUN
    options = process_arguments()
    if options.dryrun:
        DRYRUN = True
        print "Dry run mode enabled."
    load_config("consul2unixusers.conf")
    userdata = readUsersFromConsul()["elim"]["homeDirectory"]

if __name__ == '__main__':
    main()
