# Configuration
NAMESPACE = v-ics
SCADA_KUBE_DIR = ./scada-lts/kubernetes
PLC_KUBE_DIR = ./openplc/kubernetes

# Kubernetes manifests
DATABASE = $(SCADA_KUBE_DIR)/database.yaml
DATABASE_CLAIM = $(SCADA_KUBE_DIR)/database-pvc.yaml
DATABASE_CONFIG = $(SCADA_KUBE_DIR)/database-config.yaml
DATABASE_SECRET = $(SCADA_KUBE_DIR)/database-secret.yaml
SCADALTS = $(SCADA_KUBE_DIR)/scadalts.yaml
SCADALTS_CLAIM = $(SCADA_KUBE_DIR)/scadalts-pvc.yaml
OPENPLC_YAML = $(PLC_KUBE_DIR)/openplc.yaml
COMBINED_YAML = ./scada-lts-development.yaml

# Helm charts
SCADA_LTS_CHART = .$(SCADA_KUBE_DIR)/scadalts-chart
OPENPLC_CHART = $(PLC_KUBE_DIR)/openplc-chart

.PHONY: all deploy-scada-lts deploy-openplc clean combine

all: deploy-scada-lts deploy-openplc

deploy-scada-lts:
	@kubectl create namespace $(NAMESPACE) || true
	@helm upgrade --install scadalts $(SCADA_LTS_CHART) -n $(NAMESPACE)

deploy-openplc: 
	@echo "Deploying OpenPLC instances..."
	@for i in $(shell seq 1 $(NUM_INSTANCES)); do \
		instance_name="openplc-instance$$i"; \
		values_file="$(PLC_KUBE_DIR)/openplc-values/instance$$i.yaml"; \
		helm upgrade --install $$instance_name $(OPENPLC_CHART) -n $(NAMESPACE) -f $$values_file; \
	done

combine:
	@echo "Combining YAML files into $(COMBINED_YAML)..."
	@cat $(DATABASE_CLAIM) $(DATABASE_CONFIG) $(DATABASE_SECRET) $(DATABASE) $(SCADALTS_CLAIM) $(SCADALTS) > $(COMBINED_YAML)
	@echo "OpenPLC instance configurations will need to be added manually to $(COMBINED_YAML)"

clean:
	@helm uninstall scadalts -n $(NAMESPACE) || true
	@for i in $(shell seq 1 $(NUM_INSTANCES)); do \
		instance_name="openplc-instance$$i"; \
		helm uninstall $$instance_name -n $(NAMESPACE) || true; \
	done
	@kubectl delete namespace $(NAMESPACE) || true
	@rm -f $(COMBINED_YAML)  # Remove the combined YAML file