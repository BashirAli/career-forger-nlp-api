
# GCP Cloud Template API
This repository is a templated web service which can be deployed as a Cloud Run service on GCP.
It can be used as a REST API for consumers or as a PubSub subscriber. It is based on the FastAPI framework, 
and has the ability to use Pydantic models for request and response validation, as well as the Open API Specification for consumer endpoints.

# Building the API
The basics of building the skeleton of the API:
1. Run poetry init
2. Run poetry lock once you have added your packages to your pyproject.toml
3. Build Dockerfile to use your pyproject.toml packages
4. Build docker-compose.yml (if needed) to build your emulators
5. Write your code and copy it in to your Dockerfile


# API Local Development
### 1. Build and Run Local Test
```commandline
docker-compose -f docker-compose-local.yml build career-forger-nlp-api-local && docker-compose -f docker-compose-local.yml up career-forger-nlp-api-local
```
**_NOTE:_**  There is a postman collection in the repo which can be used to test the endpoints, but 
you need to add your IP address in to the compose file for it to work


### 2. Build and Run Unit and Integration Tests
```commandline
docker-compose -f docker-compose.yml up --build 
```

#### a. Integration Tests
With the Docker Compose dev instance running:
```commandline
docker exec career-forger-nlp-api-dev /bin/sh -c "poetry run pytest /home/appuser/tests/integration_tests/"
```

#### b. Unit Tests
With the Docker Compose dev instance running:
```commandline
docker exec career-forger-nlp-api-dev /bin/sh -c "poetry run pytest /home/appuser/tests/unit_tests/"
```

# Deploying to GCP Dev Environment
For actually deploying to the dev environment
```
gcloud run deploy career-forger-nlp-api-<your-name> \
 --image europe-west2-docker.pkg.dev/<GAR_NAME>:<VERSION_NUMBER> \
 --platform managed \
 --project <PROJECT_ID> \
 --region europe-west2 \
 --ingress=internal-and-cloud-load-balancing \
 --no-allow-unauthenticated \
 --service-account=<SA>.iam.gserviceaccount.com \
 --set-env-vars "GCP_PROJECT_ID=<PROJECT_ID>" --set-env-vars "NLP_BUCKET=<PROJECT_ID>-dummy_bucket" \
 --min-instances=3 \
 --max-instances=10 \
 --concurrency=100 \
 --memory=2Gi \
 --cpu=4 \
 --vpc-connector serverless-conn-ew2 --vpc-egress all-traffic
```

### Pydantic Model Updates
The following line updates your Pydantic models based on the OpenAPI Spec provided
```commandline
datamodel-codegen  --input openapi/gcp_cloud_run_template_api.yaml --output src/pydantic_model/api_model.py  --output-model-type pydantic_v2.BaseModel
```

# Pushing Docker Image and Deploying to Dev
To deploy your Cloud Run API, you need to build and push your Docker image first to your container registry. 
For GCP it means either ```Container Registry (CR)``` or ```Artefact Registry (AR)```

1. Build your docker image
```
docker build -t {CR_HOST_NAME}/{GCP_PROJECT_ID}/{NAME_OF_IMG}:{VERSION} {PATH TO DOCKERFILE AND CODE}
OR 
docker build -t {AR_HOST_NAME}/{GCP_PROJECT_ID}/{AR_FOLDER_NAME}/{NAME_OF_IMG}:{VERSION} {PATH TO DOCKERFILE AND CODE}


E.g. docker build -t europe-west2-docker.pkg.dev/prj-vo-aa-s-dss-sandbox/centralised-alerts-poc/centralised-alerts-poc:v01 .

```
**_Note:_** You may need to pull your parent image in to local first. This is done by 
```
docker pull {CR_HOST_NAME}/{GCP_PROJECT_ID}/{NAME_OF_IMG}:{VERSION} 
OR 
docker pull {AR_HOST_NAME}/{GCP_PROJECT_ID}/{AR_FOLDER_NAME}/{NAME_OF_IMG}:{VERSION}

E.g. docker pull europe-docker.pkg.dev/prj-vo-aa-s-dss-sandbox/hello-world-parent-image/hello-world-parent-image:latest
```

2. Push your built image to container/artefact registry
```
docker push {CR_HOST_NAME}/{GCP_PROJECT_ID}/{NAME_OF_IMG}:{VERSION} 
OR 
docker push {AR_HOST_NAME}/{GCP_PROJECT_ID}/{AR_FOLDER_NAME}/{NAME_OF_IMG}:{VERSION}

E.g. docker push europe-west2-docker.pkg.dev/prj-vo-aa-s-dss-sandbox/centralised-alerts-poc/centralised-alerts-poc:v01
```
**_Note:_** If you're having permissions issues to push to ```AR```, execute: ```gcloud auth configure-docker {REGION}-docker.pkg.dev```

3. Deploy this pushed Image to CLoud Run
```
gcloud run deploy centralised-alerts-poc \
 --image europe-west2-docker.pkg.dev/prj-vo-aa-s-dss-sandbox/centralised-alerts-poc/centralised-alerts-poc:v02 \
 --platform managed \
 --project prj-vo-aa-s-dss-sandbox \
 --ingress=internal-and-cloud-load-balancing \
 --no-allow-unauthenticated \
 --service-account=centralised-alerts-poc@prj-vo-aa-s-dss-sandbox.iam.gserviceaccount.com \
 --set-env-vars "GCP_PROJECT_ID=prj-vo-aa-s-dss-sandbox" \
 --min-instances=3 \
 --max-instances=20 \
 --concurrency=100 \
 --memory=2Gi \
 --cpu=4 \
 --vpc-connector serverless-conn-ew2 --vpc-egress all-traffic
```


### Examples

```
gcloud auth configure-docker europe-docker.pkg.dev

docker pull europe-docker.pkg.dev/prj-vo-aa-s-dss-sandbox/hello-world-parent-image/hello-world-parent-image:latest

docker build -t europe-west2-docker.pkg.dev/prj-vo-aa-s-dss-sandbox/hello-world/hello-world:v01 .

docker push europe-west2-docker.pkg.dev/prj-vo-aa-s-dss-sandbox/hello-world/hello-world:v01
```