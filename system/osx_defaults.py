#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION= '''
---
module: osx_defaults
short_description: set/retrieve user defaults on Mac OS X
description:
    -  Reads, writes, and delete Mac OS X user defaults, requires that
       the defaults utility is present
options:
  name:
    required: true
    default: None
    aliases: ['domain']
    description:
      - Set of defaults, usually corresponds to an individual application
  key:
    required: false
    default: None
    description:
      - Property to access, always a string.
  value:
    required: false
    default: None
    description:
      - Value to assign.
  type:
    required: false
    default: None
    description:
      - type of the value, only used when writing. Usually this can be inferred from the content of the value. Useful if you need to save "true", "false" or an integer as a string.
  state:
    required: false
    default: get
    choices: [ 'read', 'present', 'absent' ]
    description:
      - defines which state you want to do.
        C(read) retrieves the current value for a C(key) (default)
        C(present) set C(name) to C(value), default if value is set
        C(absent) deletes the key
author: Joseph Anthony Pasquale Holsten
'''

EXAMPLES = '''
# Obtain the defaults of ...
- osx_defaults: name=NSGlobalDomain

# set key foo to value bar
- osx_defaults: domain=NSGlobalDomain key=foo value=bar

# type=int
- osx_defaults: name=NSGlobalDomain key=KeyRepeat value=0
# type=bool
- osx_defaults: name=com.apple.driver.AppleBluetoothMultitouch.trackpad key=Clicking value=true
# type=string
- osx_defaults: name=com.apple.finder key=FXPreferredViewStyle value=Nlsv

# remove key foo
- osx_defaults: name=NSGlobalDomain key=foo state=absent
'''

# TODO: support add a k-v to dictionary string -> string
# defaults write com.apple.mail NSUserKeyEquivalents -dict-add "Send" -string "@\\U21a9"


def read_defaults(module, domain, key):
    cmd = [ module.get_bin_path('defaults', True) ]
    cmd.append('read %s ' % domain)
    if key:
      cmd.append(key)
    return { key : _run_defaults(module, cmd, check_rc=False) }


def delete_defaults(module, domain, key):
    cmd = [ module.get_bin_path('defaults', True) ]
    cmd.append('delete %s ' % domain)
    if key:
      cmd.append(key)
    return { key : _run_defaults(module, cmd, check_rc=False) }

def write_defaults(module, domain, key, value, type=None):
    cmd = [ module.get_bin_path('defaults', True) ]
    cmd.append('write %s %s' % (domain, key))
    if type is None:
      if value == 'true' or value == 'false' :
          type = 'bool'
      elif re.search('\d+', value):
          type = 'int'
      else:
          type = 'str'
    cmd.append('-%s %s' % (type, value))

    return { key : _run_defaults(module, cmd, check_rc=False) }


def _run_defaults(module, cmd, check_rc=True):
    (rc, out, err) = module.run_command(' '.join(cmd), check_rc=check_rc)
    res = out.strip()
    if res == '':
        return None
    else:
        return res

def _debool(val):
    if val == 'true':
        res = '1'
    elif val == 'false':
        res = '0'
    else:
        res = val
    return res

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True, aliases=['domain']),
            key = dict(required=False, default=None), 
            value = dict(required=False, default=None), 
            type = dict(required=False, default=None), 
            state = dict(required=False, default='read', choices=[ 'read', 'present', 'all', 'keys', 'absent' ], type='str'),
        ),
        supports_check_mode=False
    )
    domain = module.params.get('name')
    key = module.params.get('key')
    value = module.params.get('value')
    type = module.params.get('value')
    state = module.params.get('state')

    changed = False
    msg = ""
    res = {}
   
    if (state == 'present' or value is not None):
        current=read_defaults(module, domain, key)
        if current is None or not key in current or _debool(value) != current[key]:
          if not module.check_mode:
            res = write_defaults(module, domain, key, value, type)
          changed=True
        res=current
        msg="%s set to %s" % (key, value)
    elif state == 'absent':
        current=read_defaults(module, domain, key)
        if current is not None and key in current and current[key] is not None:
          if not module.check_mode:
            res = delete_defaults(module, domain, key)
          changed=True
        res=current
        msg="%s removed" % (key)
    else:
        res = read_defaults(module, domain, key)
        msg = "returning %s" % key


    module.exit_json(changed=changed, msg=msg, defaults=res)

from ansible.module_utils.basic import *

main()
