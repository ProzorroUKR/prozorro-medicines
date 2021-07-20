IMAGE ?= "medicines:latest"
IMAGE_TEST ?= "medicines:test"
GIT_STAMP ?= $(shell git describe --tags)

docker-build: $(FETCH_TEST_DATA)
	docker build --build-arg version=$(GIT_STAMP) -t $(IMAGE) .
	docker build --target=test --build-arg version=$(GIT_STAMP) -t $(IMAGE_TEST) .

version:
	$(eval GIT_TAG ?= $(shell git describe --abbrev=0))
	$(eval VERSION ?= $(shell read -p "Version: " VERSION; echo $$VERSION))
	echo "Tagged release $(VERSION)\n" > Changelog-$(VERSION).txt
	git log --oneline --no-decorate --no-merges $(GIT_TAG)..HEAD >> Changelog-$(VERSION).txt
	git tag -a -e -F Changelog-$(VERSION).txt $(VERSION)

dev-auth-secret:
	kubectl create secret generic medicines-dev-auth --from-file=auth=dev-auth

dev-auth-secret-delete:
	kubectl delete secret medicines-dev-auth

dev-config-secret:
	kubectl create secret generic medicines-dev-medicines-secret --from-env-file=dev-env

dev-config-secret-delete:
	kubectl delete secret medicines-dev-medicines-secret

dev-update:
	helm3 upgrade -i medicines-dev helm/prozorro-medicines --namespace dev-prozorro -f dev-values.yml

dev-delete:
	helm3 uninstall medicines-dev

secret:
	curl --header "X-Vault-Token: $$VAULT_TOKEN" -X GET $(VAULT_ADDR)/v1/asur/data/$(vault-name) | jq -r '.data.data | to_entries [] | [.key, .value] | @tsv' | sed -e "s/\t/=/g" > env
	kubectl create secret generic $(name) --from-env-file=env --dry-run=client -o yaml | kubectl apply -f - -n $(namespace)


dev-trigger-crawler:
	kubectl create job --from=cronjob/medicines-dev-prozorro-medicines crawler-`date '+%d%m%Y%H%M%S'`
