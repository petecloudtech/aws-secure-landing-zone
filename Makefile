.PHONY: fmt validate test

fmt:
	terraform fmt -recursive terraform

validate:
	terraform -chdir=terraform init -backend=false -input=false
	terraform -chdir=terraform validate -no-color

test:
	python3 -m unittest discover -s tests -v
