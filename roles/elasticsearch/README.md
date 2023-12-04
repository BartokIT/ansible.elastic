elasticsearch
=========

A role to manage Elasticsearch cluster for Red Hat-like machines.

The scope of this role is to create an enforced configuration mechanism that maintain only the configurations set by the automation and remove others managed by hand.


Role Variables
--------------

This role use a main variable to globally define the behaviour of the role.

This variable allow to specify a list of actions within the following:

```yaml
r_elasticsearch_actions:
 - install
 - configure
 - stop
 - upgrade
 - start
 - uninstall
 - restart_on_configuration_change
```


Example Playbook
----------------

This example install and configure an Elasticsearch cluster:

    - name: Install and configure Elasticsearch
      hosts: all
      gather_facts: false
      tasks:

        - name: Read configurations
          ansible.builtin.set_fact:
            r_elasticsearch_cluster_name: cluster
            r_elasticsearch_node_rack: simple
            r_elasticsearch_cluster_nodes:
              host: master1
              name: master1
              roles:
               - master
              host: master2
              name: master2
              roles:
               - master
              host: master3
              name: master3
              roles:
               - master

        - name: Call Elasticsearch role
          ansible.builtin.include_role:
            name: bartokit.elastic.elasticsearch
          vars:
            r_elasticsearch_actions:
              - install
              - configure
              - start
              - restart_on_configuration_change
            r_elasticsearch_configure_actions:
              - folders
              - main_files
              - keystore
              - ssl
              - enforce_keystore
              - component_template



License
-------

GLP3
