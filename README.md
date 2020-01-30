# What is a GCSv5 installer?
GCSv5 installation and configuration is a lengthy, involved process requiring human-in-the-middle interactions. The official process is useful for one-off and first time installations but has a couple of limitations: (1) due to the amount of interactivity in the installation process, repeatable installations with the exact same configuration are cumbersome and (2) automation of the installation is non trivial. This repo was created to address both of those concerns.

The GCSv5 installer repo will house tooling that helps to automate repeatable installations whose configurations are defined in text files. This idea was born out of the need to automate endpoint installation with identitical configurations for internal system testing. But we also recognize that this functionality has wide appeal from the Globus community for integration into configuration management deployments.

**GCSv5 has its own officially-supported [installation procedures](https://docs.globus.org/globus-connect-server-v5-installation-guide/)**. This installer does not replace that process and it is likely that updates to this installer repo will lag feature releases of GCSv5.

# What is included in the repo?
The repo includes an example endpoint configuration with supporting scripts and build system to trivialize reproduction of the example configuration. 

|  |  |
|--|--|
|ansible/ | Ansible config files and globus-connect-server role. For Ansible experts only |
|scripts/ | Supporting scripts to simplify build process |
|playbook.yml | Example endpoint configuration |
|config_template.yml | Example of how to export configuration values from the playbook|
|Makefile | Build system that ties the scripting to the installer|
  
# Why Ansible in the initial release?
Since this repo was created for the purpose of automating repeatable installation for system testing, it is desireable that the tools chosen have as little impact on the person performing the tests as possible. This means that the tester should be able to set a few configuration values, run the tests and have the tests complete without issue and without requiring an in-depth understanding of the tooling. Ansible was chosen because it can be fully installed into a Python virtual environment and executed remotely without prior installaton on the target node. Plus, it has been integrated into the tooling so that the tester need only understand YAML syntax which is a far cry simpler than learning a new configuration management system; Ansible is complete transparent.

**Contributions for other configuration management system are welcome.** Those contributions are not required to fit into the Makefile/script automation available for Ansible in this initial release. In fact, I suspect that over time the repo will evolve away from the test-focus nature and become a central location for configuration management contributions.

# How do I use this for installations?

1. Git clone the repo to your installation node
    ```shell
    $ git clone https://github.com/globus/gcsv5_installer.git
    ```
2. Check that this repo supports your target system. Look in [ansible/roles/globus-connect-server/tasks] for a file named `install_<your system type>`. 
3. Make sure Python3 is installed on your system.
4. Review `playbook.yml`. This file defines the configuration of the endpoint all the way through to collection creation and optional ACL creation. Normally, `playbook.yml` is only modified by admins or developers that need communicate a repeatable configuration. 
5. Copy `config_template.yml` to `config.yml` and fillout the required values. Note that if you make changes to `playbook.yml`, some of the options in `config.yml` may no longer be necessary. The values you provide in `config.yml` are identitical to the values you would provide in `/etc/globus-connect-server.conf` in the official GCSv5 installation process.
6. Run `make install`. Phase 1 of the process is setup which will generate any necessary tokens needed for completion of the installation. Watch for an authorization prompt similar to what you may see when using `globus cli` or `oauth ssh`. The prompt will ask you to cut-n-paste an authorization link and paste back the resulting authorization code. Once that completes, phase 2 of the process performs the installation which is not interactive.

**NOTE:** If is likely that the installation may fail when trying to configure a collection due to some allocation processing in current releases of GCSv5. It is safe to re run `make install` to attempt to complete the installation. In fact, the installation process is idempotent, you can re run it as often as you like without negative side effects.
