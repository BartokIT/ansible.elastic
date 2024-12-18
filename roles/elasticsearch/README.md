bartokit.elastic.elasticsearch
=========

A role to manage Elasticsearch cluster for Red Hat-like machines.

The scope of this role is to create an enforced configuration mechanism that maintain only the configurations set by the automation and remove others managed by hand.


## Role Variables


This role use a main variable to globally define the behaviour of the role.

This variable allow to specify a list of actions within the following:

```yaml
r_elasticsearch_actions:
 - install                                 # install the product
 - configure                               # configure files and resources of Elasticsearch
 - stop                                    # stop Elasticsearch
 - upgrade
 - start                                   # start Elasticsearch
 - uninstall
 - restart_on_configuration_change
```

## Install

_action = install_

To install Elasticsearch populate the variable `r_elasticsearch_version` with the version requested.
Here an example of a playbook to install

This example install and configure an Elasticsearch cluster:

```yaml
- name: Install and configure Elasticsearch
  hosts: elastic
  gather_facts: false
  tasks:
    - name: Install Elasticsearch
      ansible.builtin.include_role:
        name: bartokit.elastic.elasticsearch
      vars:
        r_elasticsearch_actions:
          - install
        r_elasticsearch_version: '8.13.2'
```

## Configure


_action = configure_

There are two operating mode controlled by the boolean variable `r_elasticsearch_enforce`:
- **false** ensure only that the specified resources (users, roles, .. ) are present and if present the configuration is enforced
- **true**  ensure that only the specified resources are present by removing the others and set the configuration for the remaining (_default behaviour_)

Suppose that you have the ingest pipeline named _pipeline1_ and _pipeline2_ and you launch the following playbook:

```yaml
- name: Install and configure Elasticsearch
  hosts: elastic
  gather_facts: false
  tasks:
    - name: Install Elasticsearch
      ansible.builtin.include_role:
        name: bartokit.elastic.elasticsearch
      vars:
        r_elasticsearch_enforce: true
        r_elasticsearch_actions:
          - configure
        r_elasticsearch_configure_actions:
          - ingest_pipelines
        r_elasticsearch_ingest_pipelines:
          pipeline1:
            processors:
              - append:
                  field: "field1"
                  value:
                    - "value1"
```
the `r_elasticsearch_enforce` parameter ensure that the pipeline1 will have the specified processors and the pipeline2 will be removed as not provided inside the configurations.

The configuration flow is controlled by the `r_elasticsearch_configure_actions` variable that allow the following values:
  - initial
  - sysctl
  - folders
  - main_files
  - keystore
  - enforce_keystore
  - ssl
  - component_template
  - index_template
  - ilm_policies
  - users
  - roles
  - role_mappings
  - enforce_user_password
  - ingest_pipelines
  - logstash_pipelines
  - beats_index_management

### Main file configuration


# Start/Stop/Restart
----------------

To restart Elasticsearch it is sufficient to select both the stop and start actions or if you want to just stop or start, choose only the needed action.

This is the example playbook:

```yaml
- name: Install and configure Elasticsearch
  hosts: elastic
  gather_facts: false
  tasks:
    - name: Install Elasticsearch
      ansible.builtin.include_role:
        name: bartokit.elastic.elasticsearch
      vars:
        r_elasticsearch_actions:
          - stop
          - start

# License
-------

GLP3
