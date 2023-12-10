# APP_NAME=$(shell basename $(shell pwd))
# PWD=$(shell pwd)
# APP_LOG=/var/log/gms-${APP_NAME}.log
# IMAGE_NAME=device-manager
# include ../../deploy/docker_config
# export CGO_ENABLED=0

lambda:
	rm -rf file_upload_to_s3.zip
	mkdir -p awsLambda/package
	cp -r ./dependency/* awsLambda/package
	cp ./file_upload_to_s3.py awsLambda/package
	cd awsLambda/package; zip -r file_upload_to_s3.zip .; mv file_upload_to_s3.zip ..
	rm -rf awsLambda/package
