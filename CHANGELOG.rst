====================================
Bartokit.Elasticsearch Release Notes
====================================

.. contents:: Topics

v0.1.4
======

Major Changes
-------------

- added logstash role

Minor Changes
-------------

- added support for all beats (except winlogbeat) dashbaord import
- improved dataview management

New Modules
-----------

- bartokit.elastic.logstash_keystore - This module allow to manage the logstash keystore.

v0.1.3
======

Release Summary
---------------

beat_dashboards_setup delete dashboard bug fixed

Bugfixes
--------

- fixed beat_dashboards_setup module bug that delete also custom dashboards

v0.1.2
======

Release Summary
---------------

added first beat setup feature

Major Changes
-------------

- added metricbeat dashboard task in kibana role

New Modules
-----------

- bartokit.elastic.beat_dashboards_setup - This module allow to import beat dashboards into kibana

v0.1.1
======

Release Summary
---------------

added support for beat module setup

Major Changes
-------------

- elastic role - added a task to perform setup of beats index setup

New Modules
-----------

- bartokit.elastic.beat_index_management_setup - This module allow to create beat base index structure

v0.1.0
======

Major Changes
-------------

- added support for python 2.7 to beat modules
- modified role user management by adding a dedicated api user

Minor Changes
-------------

- added enforcing or not mode
- added logging directive to beats roles
- code linting and documentation review
- first working version for kibana role
- fixed enforce keystore content configuration
- fixed role mapping module plugin idempotency
- fixed role module plugin drop role

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

- bartokit.elastic.elasticsearch_role_mappings - This module allow to manage roles of an Elasticsearch installation
- bartokit.elastic.elasticsearch_roles - This module allow to manage roles of an Elasticsearch installation

v0.0.12
=======

New Modules
-----------

- bartokit.elastic.kibana_keystore - This module allow to manage the kibana keystore.

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
