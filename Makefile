-include .env

CI_COMMIT_SHORT_SHA ?= $(shell git rev-parse --short HEAD)
IMAGE ?= "medicines:latest"
IMAGE_TEST ?= "medicines:test"
GIT_STAMP ?= $(shell git describe)
HELM ?= helm3

ifdef CI
  REBUILD_IMAGES_FOR_TESTS =
else
  REBUILD_IMAGES_FOR_TESTS = docker-build
endif


run: docker-build
	docker-compose --file=docker-compose.yml up -d

stop:
	docker-compose --file=docker-compose.yml stop

docker-build: $(FETCH_TEST_DATA)
	docker build --build-arg version=$(GIT_STAMP) -t $(IMAGE) .
	docker build --target=test --build-arg version=$(GIT_STAMP) -t $(IMAGE_TEST) .

helm-build:
	$(HELM) package helm/prozorro-medicines --app-version=$(GIT_STAMP) --version=$(GIT_STAMP)

helm-install: docker-build
	helm install medicines helm/prozorro-medicines

helm-uninstall:
	helm uninstall medicines

version:
	$(eval GIT_TAG ?= $(shell git describe --abbrev=0))
	$(eval VERSION ?= $(shell read -p "Version: " VERSION; echo $$VERSION))
	echo "Tagged release $(VERSION)\n" > Changelog-$(VERSION).txt
	git log --oneline --no-decorate --no-merges $(GIT_TAG)..HEAD >> Changelog-$(VERSION).txt
	git tag -a -e -F Changelog-$(VERSION).txt $(VERSION)


dev-upgrade:
	helm3 upgrade -i asur-dev helm/customs-asur --namespace asur-dev -f dev-values.yml

secret:
	curl --header "X-Vault-Token: $$VAULT_TOKEN" -X GET $(VAULT_ADDR)/v1/asur/data/$(vault-name) | jq -r '.data.data | to_entries [] | [.key, .value] | @tsv' | sed -e "s/\t/=/g" > env
	kubectl create secret generic $(name) --from-env-file=env --dry-run=client -o yaml | kubectl apply -f - -n $(namespace)
