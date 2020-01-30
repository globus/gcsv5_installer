VENV_ROOT:=.venv
PYTHON_VERSION:=3
PYTHON:=$(VENV_ROOT)/bin/python$(PYTHON_VERSION)
PIP:=$(VENV_ROOT)/bin/pip$(PYTHON_VERSION)
ANSIBLE_PLAYBOOK:=$(VENV_ROOT)/bin/ansible-playbook
PLAYBOOK:="playbook.yml"
ANSIBLE_CFG:="ansible/ansible.cfg"
CONFIG:=config.yml

all:
	$(error Usage: "make [install|clean]")


SHELL:=bash

ifeq (, $(shell command -v python$(PYTHON_VERSION)))
$(error You need to install python$(PYTHON_VERSION))
endif

ifeq (,$(wildcard $(CONFIG)))
$(error Create $(CONFIG) from the template before running make)
endif

APP_ID = $(shell $(PYTHON) scripts/yaml.py $(CONFIG) app_client_id 2> /dev/null)
APP_SECRET = $(shell $(PYTHON) scripts/yaml.py $(CONFIG) app_client_secret 2> /dev/null)
ENV = $(shell $(PYTHON) scripts/yaml.py $(CONFIG) globus_environment)

python_modules: requests ruamel.yaml

create_client: python_modules
ifeq ($(and $(APP_ID), $(APP_SECRET)),)
	@$(eval json="$(shell $(PYTHON) scripts/create_client.py $(ENV))")
	@$(eval id=$(shell $(PYTHON) scripts/json_parser.py $(json) "['client']"))
	@$(eval secret=$(shell $(PYTHON) scripts/json_parser.py $(json) "['secret']"))
	@$(PYTHON) scripts/yaml.py $(CONFIG) app_client_id=$(id)
	@$(PYTHON) scripts/yaml.py $(CONFIG) app_client_secret="$(secret)"
endif

TRANSFER_ACCESS_TOKEN =     \
          $(shell $(PYTHON) scripts/yaml.py $(CONFIG) transfer_access_token 2> /dev/null)
TRANSFER_REFRESH_TOKEN =    \
          $(shell $(PYTHON) scripts/yaml.py $(CONFIG) transfer_refresh_token 2> /dev/null)
GCS_MANAGER_ACCESS_TOKEN =  \
          $(shell $(PYTHON) scripts/yaml.py $(CONFIG) gcs_manager_access_token 2> /dev/null)
GCS_MANAGER_REFRESH_TOKEN = \
          $(shell $(PYTHON) scripts/yaml.py $(CONFIG) gcs_manager_refresh_token 2> /dev/null)

GCSV5_CLIENT_ID=$(shell $(PYTHON) scripts/yaml.py $(CONFIG) gcsv5_client_id)
TRANSFER_SCOPE:=urn:globus:auth:scope:transfer.api.globus.org:all
GCSM_SCOPE=urn:globus:auth:scope:$(GCSV5_CLIENT_ID):manage_collections
SCOPES=$(TRANSFER_SCOPE) $(GCSM_SCOPE)

create_tokens: python_modules create_client
ifeq ($(and $(TRANSFER_ACCESS_TOKEN),   \
            $(TRANSFER_REFRESH_TOKEN),  \
            $(GCS_MANAGER_ACCESS_TOKEN),\
            $(GCS_MANAGER_REFRESH_TOKEN)),)
	$(eval tokens="$(shell \
                         CLIENT_ID=$(APP_ID)         \
                         CLIENT_SECRET=$(APP_SECRET) \
                         $(PYTHON) scripts/create_tokens.py \
                                                  $(ENV) '$(SCOPES)')")
	@$(eval tat=$(shell $(PYTHON) scripts/json_parser.py $(tokens) "['access_token']"))
	@$(eval trt=$(shell $(PYTHON) scripts/json_parser.py $(tokens) "['refresh_token']"))
	@$(eval gat=$(shell $(PYTHON) scripts/json_parser.py $(tokens) "['other_tokens'][0]['access_token']"))
	@$(eval grt=$(shell $(PYTHON) scripts/json_parser.py $(tokens) "['other_tokens'][0]['refresh_token']"))
	
	@$(PYTHON) scripts/yaml.py $(CONFIG) transfer_access_token="$(tat)"
	@$(PYTHON) scripts/yaml.py $(CONFIG) transfer_refresh_token="$(trt)"
	@$(PYTHON) scripts/yaml.py $(CONFIG) gcs_manager_access_token="$(gat)"
	@$(PYTHON) scripts/yaml.py $(CONFIG) gcs_manager_refresh_token="$(grt)"
endif

install: run_playbook

run_playbook: $(ANSIBLE_PLAYBOOK) create_client create_tokens
	ANSIBLE_CONFIG=$(ANSIBLE_CFG) $(ANSIBLE_PLAYBOOK) $(PLAYBOOK)

$(ANSIBLE_PLAYBOOK): $(PIP)
	$(PIP) install ansible

$(PIP): $(VENV_ROOT)

$(VENV_ROOT):
	python$(PYTHON_VERSION) -m venv $(VENV_ROOT)
	$(PIP) install --upgrade pip

ruamel.yaml: $(PIP)
	@$(PIP) show ruamel.yaml > /dev/null 2>&1 || $(PIP) install ruamel.yaml

requests: $(PIP)
	@$(PIP) show requests > /dev/null 2>&1 || $(PIP) install requests

clean:
	@rm -rf $(VENV_ROOT)

.PHONY: clean
