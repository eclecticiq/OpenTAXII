# Example Makefile for creating the docker image

.PHONY: build push 

REG:="eclecticiq"
IMAGE:="opentaxii"

all: build push

build:
	docker  build -t $(REG)/$(IMAGE) ../.

push:
	docker push $(REG)/$(IMAGE) ../.
