====================================
Bartokit.Elasticsearch Release Notes
====================================

.. contents:: Topics

v0.1.0
======

Major Changes
-------------

- added support for python 2.7 to beat modules
- first version published
- first version published
- modified role user management by adding a dedicated api user

Minor Changes
-------------

- added enforcing or not mode
- added logging directive to beats roles
- added module plugin to manage ingest pipeline
- added module plugin to manage logstash pipeline
- added module plugin to manage role mapping
- added module plugin to manage roles
- code linting and documentation review
- first working version for kibana role
- fixed enforce keystore content configuration
- fixed role mapping module plugin idempotency
- fixed role module plugin drop role

v0.0.19
=======

v0.0.18
=======

v0.0.17
=======

v0.0.16
=======

v0.0.15
=======

v0.0.14
=======

New Modules
-----------

- bartokit.elastic.elasticsearch_ingest_pipelines - This module allow to managepipeline of an Elasticsearch installation
- bartokit.elastic.elasticsearch_logstash_pipelines - This module allow to managepipeline of an Elasticsearch installation

v0.0.13
=======

New Modules
-----------

- bartokit.elastic.elasticsearch_role_mappings - This module allow to manage roless of an Elasticsearch installation
- bartokit.elastic.elasticsearch_roles - This module allow to manage roless of an Elasticsearch installation

v0.0.12
=======

New Modules
-----------

- bartokit.elastic.kibana_keystore - This module allow to manage the kibana keystore.

v0.0.11
=======

v0.0.10
=======

v0.0.9
======

v0.0.8
======

v0.0.7
======

v0.0.6
======

v0.0.5
======

New Modules
-----------

- bartokit.elastic.beat_keystore - This module allow to manage the beats keystore.
- bartokit.elastic.beat_modules - This module allow to manage the beat modules.

v0.0.4
======

New Modules
-----------

- bartokit.elastic.elasticsearch_users - This module allow to manage user of an Elasticsearch installation

v0.0.3
======

Major Changes
-------------

- Added molecule test scenario

New Plugins
-----------

Test
~~~~

- bartokit.elastic.validate_configuration - Validate a yaml against provided schema

New Modules
-----------

- bartokit.elastic.elasticsearch_index_lifecycle_policies - This module allow to manage index lifecycle policies of an Elasticsearch installation
- bartokit.elastic.elasticsearch_index_templates - This module allow to manage index templates of an Elasticsearch installation

v0.0.2
======

v0.0.1
======

New Plugins
-----------

Filter
~~~~~~

- bartokit.elastic.dictofdict2listofdict - transform a dictionary containing a dictionary to a list of dict

New Modules
-----------

- bartokit.elastic.elasticsearch_component_templates - This module allow to manage component templates of an Elasticsearch installation
- bartokit.elastic.elasticsearch_info - This module extract informations from an elasticsearch installation
- bartokit.elastic.elasticsearch_keystore - This module allow to manage the elasticsearch keystore.
