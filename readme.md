# Into

Ansible and mergevar plugin are intended to make easy and convenient configuration management for jenkins service with Configuration as Code plugin (**JCasC**).

## Requirements

* A common part for different instances/groups should not be copied and pasted and must be easy to reuse;
* It must be easy to understand how the resulting configuration is generated and based on which values the config placeholders are resolved;
* Some configuration properties must be dynamic.

Configuration cat be built during the deployment phase and the resulting plain config files can be copied to the filesystem, where your jenkins can access them directly.

# Service configuration types

It's convenient to have different kinds of configuration and keep it in different files or git repositories:

* JCasC internal configuration. Defined only as a Ansible variables;
* JCasC global configuration;
* JCasC instance/group configuration.

## Priority indexes

There are few reserved priority indexes for different types of configuration sources:

* JCasC internal configuration. Ansible internally defined variables (see **_roles/jenkins/vars/main.yml_**) should use indexes **000-999**;
* JCasC global configuration uses indexes **1000-1999**;
* JCasC instance/group configuration uses indexes **2000-9999**.

Example of var merging order:
```
Merging vars in this order: [
'000__jenkins_global_configuration_jcasc', '001__jenkins_global_configuration_audit_jcasc', '001__jenkins_global_configuration_configure_project_authenticator_jcasc', '001__jenkins_global_configuration_disable_administrative_monitors_jcasc', '001__jenkins_global_configuration_disable_update_sites_jcasc', '001__jenkins_global_configuration_disable_usage_stat_jcasc', '001__jenkins_global_configuration_installed_plugins_jcasc', '001__jenkins_global_configuration_locale_jcasc', '001__jenkins_global_configuration_mask_passwords_jcasc',
'1000__credentials_global_yml_jcasc', '1001__etc_gerrit_yml_jcasc', '1002__etc_ldap_yml_jcasc', '1003__global_config_files_cicd-maven-settings_yml_jcasc', '1004__jobs_jcasc_yml_jcasc', '1005__jobs_seed_yml_jcasc', '1006__roles_admins_yml_jcasc', '1007__roles_anonymous_yml_jcasc', '1008__tools_ant_yml_jcasc', '1009__tools_atg_yml_jcasc', '1010__tools_docker_yml_jcasc', '1011__tools_google-cloud-sdk_yml_jcasc', '1012__tools_groovy_yml_jcasc', '1013__tools_jdk_yml_jcasc', '1014__tools_jq_yml_jcasc', '1015__tools_maven_yml_jcasc', '1016__tools_nodejs_yml_jcasc', '1017__tools_packer_yml_jcasc', '1018__tools_python_yml_jcasc', '1019__tools_sbt_yml_jcasc', '1020__tools_yarn_yml_jcasc',
'2000__roles_items-role_yml_jcasc', '2001__roles_slave-role_yml_jcasc'
]
```

# JCasC configuration builder

Current JCasC configuration builder implementation consists from the following steps:

1. User can redefine `jenkins_casc_global_config_path (defaut: "configuration/global/jcasc")` variable to specify the path where **_global configuration_** are stored;

2. User can redefine `jenkins_casc_user_config_path (default: "configuration/hosts/{{ ansible_hostname }}/jcasc")` variable to specify the path where **_instance/group configuration_** are stored;

3. In ansible execution for each found file by `jenkins_casc_global_config_path` path variable will be dynamically defined in a **sorted way** with value from current file. The name of the variable dynamically generated based on the file path with a priority;

4. In ansible execution for each found file by `jenkins_casc_user_config_path` path variable will be dynamically defined in a **sorted way** with value from current file. The name of the variable dynamically generated based on the file path with a priority;

5. After all configuration files were included and registered, ansible will merge these variables. There is an ansible plugin to merge all variables in context with a certain suffix and create a new variable (`jenkins_configuration`) that contains the result of this merge.

## JCasC search file masks

The jcasc search file masks defined in `jenkins_casc_config_files_match variable (default: .*.yml$)`

# Basic folder layout

Let’s take a look at a basic folder layout that you can keep in a dedicated repository (**_config_**).

For every jenkins instance/group, you have to create a folder with a unique name. In the instance/group directory, we will keep instance/group ***JCasC*** specific configurations (**_jcasc_** directory) and/or ***Ansible specific variables*** (**_vars_** directory).

So, let’s imagine we have 2 instances/groups: 'QA', 'BigData'.

The resulting layout will look like:

```

|-- BigData
|   |-- jcasc
|   `-- vars
|-- QA
|   |-- jcasc
|   `-- vars
```

# Configuration sources

## Jcasc

Inside the instance/group **jcasc folder**, you can create a configuration in a [JCasC format.](https://github.com/jenkinsci/configuration-as-code-plugin/blob/master/README.md)

You can split configuration among several files and/or directories. No matter how many files or directories are used, after the configuration build for each config type, a single result file will be generated.

```
QA/
|-- jcasc
|   `-- roles
|       |-- admins.yml
|       `-- items-role.yml
`-- vars
```

Inside _QA/jcasc/roles/items-role.yml_ we've stored configuration that describes role-based authorization:
```
---
jenkins:
  authorizationStrategy:
    roleBased:
      roles:
        items:
        - name: "QA-Jobs-Role"
          pattern: "QA-.*"
          permissions:
          - "Job/Build"
          - "Credentials/Create"
          - "Gerrit/ManualTrigger"
          - "Credentials/View"
          - "Credentials/Update"
          - "Gerrit/Retrigger"
```

Inside _QA/jcasc/roles/admins.yml_ we've stored configuration what assigned user **_tkma0lx_** into **_adminGlobalRole_** (NB: the **_adminGlobalRole_** role is a part of _global_ jcasc configuration).

```
---
jenkins:
  authorizationStrategy:
    roleBased:
      roles:
        global:
        - name: "adminGlobalRole"
          assignments:
            - mylocaladmin
```

Lets locally build jcasc configuration with the following command:

```
ansible-playbook \
  -c local -i 'localhost,' \
  --become-user=*** \
  -t jcasc \
  -e jenkins_casc_user_config_path=../config/hosts/QA/jcasc/ \
  -e jenkins_casc_config_path=/tmp/j/ \
  -e jenkins_process_user=*** \
  -e jenkins_process_group=*** \
  jenkins-master.yml
```

Where:
* `jenkins_casc_user_config_path` path to instance/group **jcasc configuration folder**;
* `jenkins_casc_config_path` path where to store resulting configuration;
* `jenkins_process_user` configuration file user owner;
* `jenkins_process_group` configuration file group owner.

The resulting jcasc configuration will look like:
```
/tmp/j
`-- 01-jenkins.yml
```

Content:
```
...
jenkins:
...
  authorizationStrategy:
    roleBased:
      roles:

        global:
        - assignments:
          - admin
          - mylocaladmin
          name: adminGlobalRole
          pattern: .*
          permissions:
          - Overall/Administer

        items:
        - name: QA-Jobs-Role
          pattern: QA-.*
          permissions:
          - Job/Build
          - Credentials/Create
          - Gerrit/ManualTrigger
          - Credentials/View
          - Credentials/Update
          - Gerrit/Retrigger
...      
```

## Vars

To override Ansible role specific variables you have to create `.yml` file in the instance/group **vars folder**.

```
QA/
|-- jcasc
|   `-- roles
|       |-- admins.yml
|       `-- items-role.yml
`-- vars
    |-- jenkins_color_theme.yml
    `-- jenkins_plugins.yml
```

Inside _QA/vars/jenkins_color_theme.yml_ we've stored configuration what controls `jenkins_color_theme` variable value
```
jenkins_color_theme: deep-orange
```

And _QA/vars/jenkins_plugins.yml_ what controls `jenkins_plugins`:
```
jenkins_plugins:
  chucknorris: "1.2"
```

# Ansible mergevar plugin

An Ansible plugin to merge all variables in context with a certain suffix and create a new variable that contains the result of this merge (`merged_var_name`).

```
- merge_vars:
    suffix_to_merge: jcasc
    merged_var_name: jenkins_configuration
    additional_merge_tree:
      - jenkins/globalNodeProperties
    additional_merge_by_key:
      - jenkins/authorizationStrategy/roleBased/roles/agents: name
      - jenkins/authorizationStrategy/roleBased/roles/global: name
      - jenkins/authorizationStrategy/roleBased/roles/items: name
```

The variables that you want to merge must be suffixed with `suffix_to_merge value`. They can be defined anywhere in the inventory, or by any other means; as long as they're in the context for the running play, they'll be merged.

## Complex structures
### Additional_merge_tree

There are `additional_merge_tree` logic implemented, that makes possible merge specified keys (`jenkins/globalNodeProperties` in example above) twice (for each element in list) based on dict key (only dict merging implemented):

Without `additional_merge_tree` (based on MERGE_ADDITIVE logic only) results would be:
```
"globalNodeProperties": [
        {
          "envVars": {
              "env": [
                  {
                      "key": "PYTHONUNBUFFERED",
                      "value": "1"
                  }
              ]
          }
        },
        {
            "envVars": {
                "env": [
                    {
                        "key": "GERRIT_URL",
                        "value": "***"
                    }
                ]
            }
        }
    ]
},
```

The "envVars" dict here defined twice (that is **correct** because globalNodeProperties has a "list" type), but this is not what we actually expect.

With `additional_merge_tree` logic:
```
"globalNodeProperties": [
    {
        "envVars": {
            "env": [
                {
                    "key": "PYTHONUNBUFFERED",
                    "value": "1"
                },
                {
                    "key": "GERRIT_URL",
                    "value": "***"
                }
            ]
        }
    }
],
```

The "envVars" dict was merged by the same keys.

### Additional_merge_by_key

The `additional_merge_by_key` makes possible to merge more complex structures based on the `key` value.

```
...
additional_merge_by_key:
  - jenkins/authorizationStrategy/roleBased/roles/agents: name
...
```

`jenkins/authorizationStrategy/roleBased/roles/agents` this is a path and `name` this is a key name.

For example, to merge following configurations into the one structure:
```
---
jenkins:
  authorizationStrategy:
    roleBased:
      roles:
        global:
        - name: "adminGlobalRole"
          assignments:
            - admin
          pattern: ".*"
          permissions:
          - "Overall/Administer"
```

```
---
jenkins:
  authorizationStrategy:
    roleBased:
      roles:
        global:
        - name: "adminGlobalRole"
          assignments:
            - mylocaladmin
```

The `additional_merge_by_key` logic will group the same data based by `key` and `key value`(key: `name:` and value `"adminGlobalRole"`).

Result:

```
jenkins:
  agentProtocols:
  - JNLP4-connect
  - Ping
  authorizationStrategy:
    roleBased:
      roles:
        global:
        - assignments:
          - admin
          - mylocaladmin
          name: adminGlobalRole
          pattern: .*
          permissions:
          - Overall/Administer
```

# Ansible tags

Plays and tasks have optional tags attributes where you can specify a list of tags
* `install` tasks related to install packages, copy jenkins war, copy scripts, etc.;
* `settings` tasks related to configuration aspects, including `jcasc`, `plugins` tasks;
* `image` TBD
* `plugins` tasks related to plugins configuration aspects;
* `plugins_install` tasks related to plugins installation aspects;
* `rebuild-war` tasks related to install plugins into jenkins war bundle;
*  `jcasc` tasks related to jcasc configuration builder.

# Ansible role variables

Available variables are listed below, along with default values (see defaults/main.yml):

* `jenkins_updates_url` - The URL to use for Jenkins plugin updates and update-center information.
* `jenkins_connection_delay`, `jenkins_connection_retries` - Amount of time and number of times to wait for plugin installation. Total time to wait = delay * retries;
* `jenkins_connection_timeout`: Maximum  time  in  seconds  that you allow the connection to the `jenkins_updates_url` to take;
* `jenkins_home`: Jenkins needs some disk space to perform builds and keep archives;
* `jenkins_install_dir`: Install jenkins war to this directory;
* `jenkins_env_file`: Jenkins systemd service environment file;
* `jenkins_init_d_dir`: Path to store jenkins init.d groovy scripts;
* `jenkins_log_dir`: Jenkins log directory;
* `jenkins_cache_dir`: Jenkins cache directory;
* `jenkins_hostname`: Jenkins hostname address;
* `jenkins_http_port`: Jenkins to listen on http port;
* `jenkins_https_port`: Jenkins to listen on https port;
* `jenkins_url_prefix`: Jenkins URL prefix;
* `jenkins_url`: Jenkins URL address;
* `jenkins_color_theme`: Jenkins theme;
* `jenkins_casc_config_path`: Path where to store resulting jcasc configuration;
* `jenkins_rebuild_war`: Install plugin into jenkins war bundle or not;
* `jenkins_casc_global_config_path`: Directly where **_global configuration_** are stored
* `jenkins_casc_user_config_path`: Directly where **_instance/group configuration_** are stored;
* `jenkins_casc_config_files_match`: The jcasc search file masks;
* `jenkins_email`: Jenkins email;
* `jenkins_java_cmd`: Java executable bin path;
* `jenkins_java_memory_options`: Java memory options;
* `jenkins_java_jmx_options`: Java jmx options;
* `jenkins_java_network_options`: Java networking options;
* `jenkins_java_gc_options`: Java GC options;
* `jenkins_other_options`: Java another options;
* `jenkins_java_debug`: Java debug options;
* `jenkins_war_options`: Jenkins war options;
* `jenkins_proxy_host`: Proxy host;
* `jenkins_proxy_port`: Proxy port;
* `jenkins_proxy_user`: Proxy user;
* `jenkins_proxy_pass`: Proxy pass;
* `jenkins_proxy_exceptions`: No_proxy hosts;
* `jenkins_plugins`: Jenkins plugins for **_instance/group_**;
* `jenkins_global_plugins`: Jenkins plugins for **_global configuration_**;
* `jenkins_process_user`: Jenkins user to execute jenkins proccess and jenkins files owner;
* `jenkins_process_group`: Jenkins group to execute jenkins proccess and jenkins files owner.

# Ansible playbook variables

* `var_dir` - include ansible variables from this directory.
