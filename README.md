# pulp-2to3-migrate

A [Pulp 3](https://pulpproject.org/) plugin to migrate from Pulp 2 to Pulp 3.

### Requirements

* /var/lib/pulp is shared from Pulp 2 machine
* access to Pulp 2 database

### Configuration
On Pulp 2 machine:

1. Make sure MongoDB listens on the IP address accesible outside, it should be configured as 
one of the `bindIP`s in /etc/mongod.conf.

2. In case /var/lib/pulp is not on a shared filesystem, configure NFS server and share 
that directory. E.g. on Fedora/CentOS:

```
$ sudo dnf install nfs-utils
$ sudo systemctl start nfs-server
$ sudo vi /etc/exports:

        /var/lib/pulp          <Pulp 3 IP address>(rw,sync,no_root_squash,no_subtree_check)
        
$ sudo exportfs -a
```

On Pulp 3 machine:
1. Mount /var/lib/pulp to your Pulp 3 storage location. By default, it's /var/lib/pulp. E.g. on 
Fedora/Centos:

```
$ sudo dnf install nfs-utils
$ sudo mount <IP address of machine which exports /var/lib/pulp>:/var/lib/pulp /var/lib/pulp
```

2. Configure your connection to MongoDB in /etc/pulp/settings.py. You can use the same configuration
 as you have in Pulp 2 (only seeds might need to be different, it depends on your setup).
 
E.g.
```python
PULP2_MONGODB = {
    'name': 'pulp_database',
    'seeds': '<your MongoDB bindIP>:27017',
    'username': '',
    'password': '',
    'replica_set': '',
    'ssl': False,
    'ssl_keyfile': '',
    'ssl_certfile': '',
    'verify_ssl': True,
    'ca_path': '/etc/pki/tls/certs/ca-bundle.crt',
}
```

### Installation

Clone the repository and install it.
```
$ git clone https://github.com/pulp/pulp-2to3-migrate.git
$ pip install -e pulp-2to3-migrate
```

### User Guide

All the commands should be run on Pulp 3 machine.

1. Create a Migration Plan
```
$ # migrate content for Pulp 2 ISO plugin
$ http POST :24817/pulp/api/v3/migration-plans/ plan='{ "plugins": [{"type": "iso", "content": 
true}]}'

HTTP/1.1 201 Created
{
    "_created": "2019-07-23T08:18:12.927007Z",
    "_href": "/pulp/api/v3/migration-plans/59f8a786-c7d7-4e2b-ad07-701479d403c5/",
    "plan": "{ \"plugins\": [{\"type\": \"iso\", \"content\": \ntrue}]}"
}

```

2. Use the ``_href`` of the created Migration Plan to run the migration
```
$ http POST :24817/pulp/api/v3/migration-plans/59f8a786-c7d7-4e2b-ad07-701479d403c5/run/

HTTP/1.1 202 Accepted
{
    "task": "/pulp/api/v3/tasks/55db2086-cf2e-438f-b5b7-cd0dbb7c8cf4/"
}

```

### Plugin Writer's Guide

If you are extending this migration tool to be able to migrate the content type of your interest
from Pulp 2 to Pulp 3, here are some guidelines.

1. Add the necessary mappings to the constants.py.
 - to PULP2_SUPPORTED_PLUGINS
 - to PULP_2TO3_MAP

2. Add a Content model to communicate with Pulp 2.
 - It has to have a field `type` which will correspond to the `_content_type_id` of your Content
 in Pulp 2. Don't forget to add it to PULP_2TO3_MAP in step 1.
 - It has to have a ForeignKey to the `pulp_2to3_migrate.app.models.Pulp2Content` model with the
 `related_name` set to `'pulp3content'`

3. Layout of the files/directories is important.
 - Create a plugin directory in `pulp_2to3_migrate.pulp2` if it doesn't exist. Directory name
  has to have the same name as you specified your plugin name in PULP2_SUPPORTED_PLUGINS in step 1.
 - This directory has to have a module named `models.py` where you define you Content model to
   for Pulp 2. Don't forget to put its name into PULP2_SUPPORTED_PLUGINS in step 1.