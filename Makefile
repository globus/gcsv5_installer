VENV_ROOT=venv
ANSIBLE_PLAYBOOK=$(VENV_ROOT)/bin/ansible-playbook
ANSIBLE_CFG=ansible/ansible.cfg
PLAYBOOK=playbook.yml

PYTHON_VERSION=3
PYTHON=$(VENV_ROOT)/bin/python$(PYTHON_VERSION)
PIP=$(VENV_ROOT)/bin/pip$(PYTHON_VERSION)
CONFIG=config.yml
SETUP=setup.py


ifeq (, $(shell command -v python$(PYTHON_VERSION)))
$(error You need to install python$(PYTHON_VERSION))
endif

ifeq (,$(wildcard $(CONFIG)))
$(error Create $(CONFIG) from the template before running make)
endif


all:
	$(error Usage: "make [setup|install]")


setup: $(VENV_ROOT)
	$(PYTHON) $(SETUP) $(CONFIG)

$(VENV_ROOT):
	python$(PYTHON_VERSION) -m venv $(VENV_ROOT)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install: $(VENV_ROOT)
	ANSIBLE_CONFIG=$(ANSIBLE_CFG) $(ANSIBLE_PLAYBOOK) $(PLAYBOOK)


.PHONY: setup install
.SILENT:
