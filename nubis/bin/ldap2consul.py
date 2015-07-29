#!/usr/bin/python

import os
import sys
import ConfigParser
import ldap
import consul

_config = {}

def load_config(config_file):
    global _config
    if not os.path.exists(config_file):
        print "ERROR: Config file %s not found." % config_file
        sys.exit(-1)
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    if 'ldap' not in config.sections():
        print "ERROR: [ldap] section not found in %s." % config_file
        sys.exit(-1)
    _config = config

def getLDAPUsers(ldap_conn):
    searchbase = _config.get('ldap', 'searchbase')
    searchfilter = _config.get('ldap', 'searchfilter')
    attribute = _config.get('ldap', 'attribute')
    try:
        result_set = []
        sid = ldap_conn.search(searchbase, ldap.SCOPE_SUBTREE, searchfilter)
        result_type, result_data = ldap_conn.result(sid, 0)
        users = result_data[0][1]["member"]
    except ldap.LDAPError, e:
        print e
    return users

def getUserData(ldap_conn, user):
    searchbase = user
    searchfilter = user
    attribute = ["sshPublicKey", "uid"]
    sid = ldap_conn.search(searchbase, ldap.SCOPE_BASE, attrlist=attribute)
    result_type, result_data = ldap_conn.result(sid, 0)
    if result_data[0][1].has_key("uid"):
        username = result_data[0][1]["uid"][0]
    else:
        username = ""
    if result_data[0][1].has_key("sshPublicKey"):
        sshkeys = result_data[0][1]["sshPublicKey"]
    else:
        sshkeys = []
    return username, sshkeys

def main():
    userdata = {}
    load_config("ldap2consul.conf")
    server = _config.get('ldap', 'server')
    binduser = _config.get('ldap', 'binduser')
    bindpass = _config.get('ldap', 'bindpass')
    ldap_conn = ldap.open(server)
    ldap_conn.simple_bind(binduser, bindpass)
    users = getLDAPUsers(ldap_conn)
    #print getSSHKeysForUser(ldap_conn, "mail=dparsons@mozilla.com,o=com,dc=mozilla")
    #print getUsernameForUser(ldap_conn, "mail=dparsons@mozilla.com,o=com,dc=mozilla")
    #print getUserData(ldap_conn, "mail=dparsons@mozilla.com,o=com,dc=mozilla")
    for user in users:
        data = getUserData(ldap_conn, user)
        userdata[user] = data
    print userdata
    consul_host = _config.get('consul', 'server')
    consul_port = _config.get('consul', 'port')
    consul_scheme = _config.get('consul', 'scheme')

    c = consul.Consul(host=consul_host, port=consul_port, scheme=consul_scheme)

if __name__ == '__main__':
    main()
