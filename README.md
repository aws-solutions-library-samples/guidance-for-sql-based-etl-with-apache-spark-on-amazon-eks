# SQL-based ETL with Apache Spark on Amazon EKS
This is a project developed with Python [CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html) for the solution - SQL based ETL with a declarative framework powered by Apache Spark. 

We introduce a quality-aware design to increase data process productivity, by leveraging an open-source [Arc data framework](https://arc.tripl.ai/) for a user-centred declarative ETL solution. Additionally, we take considerations of the needs and expected skills from customers in data analytics, and accelerate their interaction with ETL practice in order to foster simplicity, while maximizing efficiency.

This solution collects anonymous operational metrics to help AWS improve the
quality of features of the solution. For more information, including how to disable
this capability, please see the [implementation guide](https://docs.aws.amazon.com/solutions/latest/sql-based-etl-with-apache-spark-on-amazon-eks/collection-of-operational-metrics.html).

## Overview
![](source/images/architecture.png)

### Test job in Jupyter
![](source/images/run_jupyter.gif)

### Submit Spark job by Argo workflow tool
![](source/images/submit_job_in_argo.gif)

#### Table of Contents
* [Prerequisites](#Prerequisites)
* [Deploy Infrastructure](#Deploy-infrastructure)
  * [CFN Deploy](#Deploy-CFN)
  * [Customization](#Customization)
  * [CDK Deploy](#Deploy-via-CDK)
  * [Troubleshooting](#Troubleshooting)
* [Post Deployment](#Post-Deployment)
  * [Test ETL job in Jupyter Notebook](#Test-job-in-Jupyter-notebook)
  * [Submit & Orchestrate Job](#Submit--orchestrate-job)
    * [Submit on Argo UI](#Submit-a-job-on-argo-ui)
    * [Submit by Argo CLI](#Submit-a-job-by-argo-cli)
    * [Submit a Native Spark Job](#Submit-a-native-job-with-spark-operator)
      * [Execute a PySpark Job](#Execute-a-pyspark-job)
      * [Self-recovery Test](#Self-recovery-test)
      * [Cost Savings with Spot](#Check-Spot-instance-usage-and-cost-savings)
      * [Autoscaling & Dynamic Resource Allocation](#Autoscaling---dynamic-resource-allocation)
* [Useful commands](#Useful-commands)  
* [Clean Up](#clean-up)
* [Security](#Security)
* [License](#License)

## Prerequisites 
1. Python 3.6 or later. Download Python [here](https://www.python.org/downloads/).
2. AWS CLI version 1.
  Windows: [MSI installer](https://docs.aws.amazon.com/cli/latest/userguide/install-windows.html#install-msi-on-windows)
  Linux, macOS or Unix: [Bundled installer](https://docs.aws.amazon.com/cli/latest/userguide/install-macos.html#install-macosos-bundled)
3. The AWS CLI can communicate with services in your deployment account. Otherwise, run the following script to setup your AWS account access from a command line tool.
```bash
aws configure
```
## Deploy Infrastructure

Download the project:
```bash
git clone https://github.com/aws-solutions-library-samples/guidance-for-sql-based-extraction-transformation-and-loading-with-apache-spark-on-amazon-eks.git
cd guidance-for-sql-based-extraction-transformation-and-loading-with-apache-spark-on-amazon-eks
```

This project is set up like a standard Python project. The `source/cdk.json` file tells where the application entry point is. The provisioning takes about 30 minutes to complete. See the `troubleshooting` section if you have any deployment problem. 

Two ways to deploy:
1. AWS CloudFormation template (CFN) 
2. [AWS Cloud Development Kit (AWS CDK)](https://docs.aws.amazon.com/cdk/latest/guide/home.html).

[*^ back to top*](#Table-of-Contents)
### Deploy CFN


  |   Region  |   Launch Template |
  |  ---------------------------   |   -----------------------  |
  |  ---------------------------   |   -----------------------  |
  **us-east-1**| [![Deploy to AWS](source/images/00-deploy-to-aws.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?stackName=SparkOnEKS&templateURL=https://blogpost-sparkoneks-us-east-1.s3.amazonaws.com/sql-based-etl/aws-solution-v2/sql-based-etl-with-apache-spark-on-amazon-eks.template) 

* Option1: Deploy with default (recommended). The default region is **us-east-1**. 
To launch the solution in a different AWS Region, deploy the solution by following the `Customization` section. 

* Option2: To ETL your own data, input the parameter `datalakebucket` by your S3 bucket. 
`NOTE: the S3 bucket must be in the same region as the deployment region.`

### Customization
You can customize the solution, such as remove a Jupyter timeout setting, then generate the CFN in your region: 
```bash
export BUCKET_NAME_PREFIX=<my-bucket-name> # bucket where the customized CFN templates will reside
export AWS_REGION=<your-region>
export SOLUTION_NAME=sql-based-etl
export VERSION=aws-solution-v2 # version number for the customized code

./deployment/build-s3-dist.sh $BUCKET_NAME_PREFIX $SOLUTION_NAME $VERSION

# create the bucket where customized code will reside
aws s3 mb s3://$BUCKET_NAME_PREFIX-$AWS_REGION --region $AWS_REGION

# Upload deployment assets to the S3 bucket
aws s3 cp ./deployment/global-s3-assets/ s3://$BUCKET_NAME_PREFIX-$AWS_REGION/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control
aws s3 cp ./deployment/regional-s3-assets/ s3://$BUCKET_NAME_PREFIX-$AWS_REGION/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control

echo -e "\nIn web browser, paste the URL to launch the template: https://console.aws.amazon.com/cloudformation/home?region=$AWS_REGION#/stacks/quickcreate?stackName=SparkOnEKS&templateURL=https://$BUCKET_NAME_PREFIX-$AWS_REGION.s3.amazonaws.com/$SOLUTION_NAME/$VERSION/sql-based-etl-with-apache-spark-on-amazon-eks.template\n"
```

[*^ back to top*](#Table-of-Contents)
### Deploy via CDK

CDK deployment requires Node.js (>= 10.3.0) and AWS CDK Toolkit. To install Node.js visit the [node.js](https://nodejs.org/en/) website. To install CDK toolkit, follow the [instruction](https://cdkworkshop.com/15-prerequisites/500-toolkit.html). If it's the first time to deploy an AWS CDK app into an AWS account, also you need to install a [“bootstrap stack”](https://cdkworkshop.com/20-typescript/20-create-project/500-deploy.html) to your CloudFormation.

See the `troubleshooting` section, if you have a problem to deploy the application via CDK.
 
Two reasons to deploy the solution by AWS CDK:
1. CDK provides local debug feature and fail fast.
2. Convenient to customize the solution with a quicker test response. For example remove a nested stack CloudFront and enable TLS in ALB.
 
Limitation:
The CDK deployment doesn't support pre or post-deployment steps, such as zip up a lambda function.

```bash
python3 -m venv .env
```
If you are in a Windows platform, you would activate the virtualenv like this:
 
```
% .env\Scripts\activate.bat
```
After the virtualenv is created, you can use the followings to activate your virtualenv and install the required dependencies.
```bash
source .env/bin/activate
pip install -e source
```
 
* Option1: Deploy with default (recommended)
```bash
cd source
cdk deploy --require-approval never
```
* Option2: If ETL your own data, use the parameter datalakebucket
By default, the deployment creates a new S3 bucket containing sample data and ETL job config. 
If use your own data to build an ETL, replace the `<existing_datalake_bucket>` to your S3 bucket. `NOTE: your bucket must be in the same region as the deployment region.`
```bash
cd source
cdk deploy --parameters datalakebucket=<existing_datalake_bucket>
```

[*^ back to top*](#Table-of-Contents)
## Troubleshooting

1. If you see the issue `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1123)`, most likely it means no default certificate authority for your Python installation on OSX. Refer to the [answer](https://stackoverflow.com/questions/52805115/0nd) installing `Install Certificates.command` should fix your local environment. Otherwise, use [Cloud9](https://aws.amazon.com/cloud9/details/) to deploy the CDK instead.

2. If an error appears during the CDK deployment: `Failed to create resource. IAM role’s policy must include the "ec2:DescribeVpcs" action`. The possible causes are: 1) you have reach the quota limits of Amazon VPC resources per Region in your AWS account. Please deploy to a different region or a different account. 2) based on this [CDK issue](https://github.com/aws/aws-cdk/issues/9027), you can retry without any changes, it will work. 3) If you are in a branch new AWS account, manually delete the AWSServiceRoleForAmazonEKS from IAM role console before the deployment. 

[*^ back to top*](#Table-of-Contents)
## Post-deployment
The script defaults two inputs:

```bash
export stack_name="${1:-SparkOnEKS}"
export region="${2:-us-east-1}"
```
Run the script with defaults if the CloudFormation stack name and AWS region are unchanged. Otherwise, input the parameters.

```bash
#use default
./deployment/post-deployment.sh
```

```bash
#use different CFN name or region
./deployment/post-deployment.sh <cloudformation_stack_name> <aws_region>
```

[*^ back to top*](#Table-of-Contents)
### Test job in Jupyter notebook

1. Login with the details from the above script output. Or look up from the [Secrets Manager console](https://console.aws.amazon.com/secretsmanager/). 

Use the default server size unless your workload requires more powerful compute.

NOTE: The notebook session refreshes every 30 minutes. You may lose your work if it hasn't saved on time. The notebook allows you to download and is configurable, ie. you can disable it in order to improve your data security.

2. Open a sample job `guidance-for-sql-based-extraction-transformation-and-loading-with-apache-spark-on-amazon-eks/source/example/notebook/scd2-job.ipynb` on the Jupyter notebook instance. Click “Refresh” button if the file doesn’t appear. 

3. [FYI] The source [contacts data](/deployment/app_code/data/) was generated by a [python script](https://raw.githubusercontent.com/cartershanklin/hive-scd-examples/master/merge_data/generate.py). The job outputs a table to support the [Slowly Changing Dimension Type 2](https://www.datawarehouse4u.info/SCD-Slowly-Changing-Dimensions.html) business need.

![](source/images/fake_data.gif)

4. Execute each block and observe the result. You will get a hands-on experience on how the SQL-based ETL job works powered by Apache SparkSQL.

5. [FYI] To demonstrate the best practice in DataDevOps, the JupyterHub is configured to synchronize the latest code from a github repo. In real practice, you must save all changes to a source repository, in order to save and trigger your ETL pipelines.

6. Run a query in [Athena console](https://console.aws.amazon.com/athena/) to see if it is a SCD2 type table. 
```bash
SELECT * FROM default.deltalake_contact_jhub WHERE id=12
```

[*^ back to top*](#Table-of-Contents)
### Submit & Orchestrate job

1. Check your connection. If no access to EKS or no argoCLI installed, run the [post-deployment script](#run-a-script) again.
```bash
kubectl get svc && argo version --short
```
2. Login to the Argo website. Run the script again to get a new login token if timeout.
```bash
# use your CFN stack name if it is different
export stack_name=<cloudformation_stack_name>
ARGO_URL=$(aws cloudformation describe-stacks --stack-name $stack_name --query "Stacks[0].Outputs[?OutputKey=='ARGOURL'].OutputValue" --output text)
LOGIN=$(argo auth token)
echo -e "\nArgo website:\n$ARGO_URL\n" && echo -e "Login token:\n$LOGIN\n"
```
3. Click `Workflows` side menu and the `SUBMIT NEW WORKFLOW` button.

4. [OPTIONAL] Type `argo server` in command line tool to run Argo locally. By doing so, you can avoid the session timeout. The URL is `http://localhost:2746`.

[*^ back to top*](#Table-of-Contents)
### Submit a job on Argo UI
<details>
<summary>Argo Workflow Definition</summary>
An open source container-native workflow tool to orchestrate parallel jobs on Kubernetes. Argo Workflows is implemented as a Kubernetes CRD (Custom Resource Definition). It triggers time-based or event-based workflows via configuration files.
</details>
<details>
<summary>Sample Job Introduction</summary>
Let's take a look at a [sample job](https://github.com/tripl-ai/arc-starter/tree/master/examples/kubernetes/nyctaxi.ipynb) developed in Jupyter Notebook.  It uses a thin Spark wrapper called [Arc](https://arc.tripl.ai/) to create an ETL job in a codeless, declarative way. The opinionated standard approach enables the shift in data ownership to analysts who understand business problem better, simplifies data pipeline build and enforces the best practice in Data DevOps or GitOps. Additionally, we can apply a product-thinking to the declarative ETL as a [self-service service](https://github.com/melodyyangaws/aws-service-catalog-reference-architectures/blob/customize_ecs/ecs/README.md), which is highly scalable, predictable and reusable.

In this example, we extract the `New York City Taxi Data` from [AWS Open Data Registry](https://registry.opendata.aws/nyc-tlc-trip-records-pds/), ie. a public S3 bucket `s3://nyc-tlc/trip data`, then transform the data from CSV to parquet file format, followed by a SQL based validation step to ensure the typing transformation is done correctly. Finally, query the optimized data filtered by a flag column.
</details>

1. Choose `Edit using full workflow options`. Replace the content by the followings, then `CREATE`. 
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: nyctaxi-job-
  namespace: spark
spec:
  serviceAccountName: arcjob
  entrypoint: nyctaxi
  nodeselector:
    kubernetes.io/arch: amd64
  templates:
  - name: nyctaxi
    dag:
      tasks:
        - name: step1-query
          templateRef:
            name: spark-template
            template: sparklocal
          arguments:
            parameters:
            - name: jobId
              value: nyctaxi  
            - name: tags
              value: "project=sqlbasedetl, owner=myowner, costcenter=66666"  
            - name: configUri
              value: https://raw.githubusercontent.com/tripl-ai/arc-starter/master/examples/kubernetes/nyctaxi.ipynb
            - name: image
              value: ghcr.io/tripl-ai/arc:arc_4.2.0_spark_3.3.4_scala_2.12_hadoop_3.3.2_4.2.1_slim
            - name: parameters
              value: "--ETL_CONF_DATA_URL=s3a://nyc-tlc/csv_backup \
              --ETL_CONF_JOB_URL=https://raw.githubusercontent.com/tripl-ai/arc-starter/master/examples/kubernetes"

```
2. Click a pod (dot) to check the job status and application logs.
![](source/images/3-argo-log.png)

[*^ back to top*](#Table-of-Contents)
### Submit a job by Argo CLI
Let's submit the same scd2 job tested in the Jupyter notebook earlier. 
To demonstrate Argo's orchestration advantage with a job dependency feature, the single notebook was broken down into 3 files, ie. 3 ETL jobs, stored in [deployment/app_code/job/](deployment/app_code/job). It only takes about 5 minutes to complete all jobs.
<details>
<summary>manifest file</summary>
The [manifest file](/source/example/scd2-job-scheduler.yaml) defines where the Jupyter notebook file (job configuration) and input data are. 
</details>
<details>
<summary>Jupyter notebook</summary>
The [Jupyter notebook](/source/example/notebook/scd2-job.ipynb) specifies what need to do in a CloudFormation-like/declarative approach. It tells Spark what to do, not how to do it.
</details>
<details>
<summary>Delta lake</summary>
An open source storage layer on top of parquet file, to bring the ACID transactions to your modern data architecture. In the example, we will create a table to support the [Slowly Changing Dimension Type 2](https://www.datawarehouse4u.info/SCD-Slowly-Changing-Dimensions.html) format. You will have a hands-on experience to do the SQL-based ETL to achieve the incremental data load in Data Lake.
</details>

1. Submit and check the progress in Argo console. 
```bash
# get s3 bucket from CFN output
export stack_name=<cloudformation_stack_name>
app_code_bucket=$(aws cloudformation describe-stacks --stack-name $stack_name --query "Stacks[0].Outputs[?OutputKey=='CODEBUCKET'].OutputValue" --output text)
argo submit source/example/scd2-job-scheduler.yaml -n spark --watch -p codeBucket=$app_code_bucket
```
![](source/images/3-argo-job-dependency.png)

2. The job outputs a [Delta Lake](https://delta.io/) table in [Athena](https://console.aws.amazon.com/athena/). Run the query to check if it has the same outcome as your test result in the Jupyter notebook. 
```bash
SELECT * FROM default.contact_snapshot WHERE id=12
```
[*^ back to top*](#Table-of-Contents)
### Submit a native job with Spark operator
Previously, we have run the CloudFormation-like ETL job defined in Jupyter notebook. They are powered by the [Arc data framework](https://arc.tripl.ai/). It significantly simplifies and accelerates the data application development with zero line of code. 

In this example, we will reuse the Arc docker image, because it contains an open-source Spark distribution. Let's run a native Spark job that is defined by k8s's CRD [Spark Operator](https://operatorhub.io/operator/spark-gcp). It saves efforts on DevOps operation, as the way of deploying Spark application follows the same declarative approach in k8s. It is consistent with other business applications CICD deployment processes.
  The example demonstrates:
  * Save cost with [Amazon EC2 Spot instance](https://aws.amazon.com/ec2/spot/) type
  * Dynamically scale a Spark application - via [Dynamic Resource Allocation](https://spark.apache.org/docs/3.0.0-preview/job-scheduling.html#dynamic-resource-allocation)
  * Self-recover after losing a Spark driver
  * Monitor a job on Spark WebUI

#### Execute a PySpark job

Submit a PySpark job [deployment/app_code/job/wordcount.py](deployment/app_code/job/wordcount.py) to EKS as usual. 
```bash
# get the s3 bucket from CFN output
export stack_name=<cloudformation_stack_name>
app_code_bucket=$(aws cloudformation describe-stacks --stack-name $stack_name --query "Stacks[0].Outputs[?OutputKey=='CODEBUCKET'].OutputValue" --output text)

# dynamically map an s3 bucket to the Spark job (one-off)
kubectl create -n spark configmap special-config --from-literal=codeBucket=$app_code_bucket

# submit the job to Spark Operator
kubectl apply -f source/example/native-spark-job-scheduler.yaml
```
Check the job progress:
```bash
kubectl get pod -n spark
# watch progress on SparkUI if the job was submitted from local computer
kubectl port-forward word-count-driver 4040:4040 -n spark
# go to `localhost:4040` from your web browser
```
Run the job again if necessary:
```bash
kubectl delete -f source/example/native-spark-job-scheduler.yaml
kubectl apply -f source/example/native-spark-job-scheduler.yaml
```

[*^ back to top*](#Table-of-Contents)
#### Self-recovery test
We should always keep in mind that Spark driver is a single point of failure for a Spark application. If driver dies, all other linked components will be discarded too. Outside of Kubernetes, it requires extra effort to set up a job rerun, in order to provide the fault tolerance capability. However, it is much simpler in Amazon EKS. Just few lines of retry definition without coding.

![](source/images/4-k8s-retry.png)

Let's test the self-recovery against a running Spark job triggered by the previous step. If the job is completed before this test, re-run the same job.

1. Spark Driver test - manually destroy the entire EC2 instance running the driver:
```bash
# monitor the driver restart progress
kubectl get po -n spark -w
```
```bash
# in a second terminal, locate the EC2 host
ec2_host_name=$(kubectl describe pod word-count-driver -n spark | grep "Successfully assigned" | awk '{print $9}')
# manually delete
kubectl delete node $ec2_host_name
# Did the driver come back?
```

See the demonstration simulating a Spot interruption scenario: 
![](source/images/driver_interruption_test.gif)

2. Spark Executor test - delete an executor with the "exec-1" suffix, once it's running
```bash
# replace the placeholder
exec_name=$(kubectl get pod -n spark | grep "exec-1" | awk '{print $1}')
kubectl delete -n spark pod $exec_name --force
# check the log, has it come back with a different number suffix? 
kubectl logs word-count-driver -n spark
```
![](source/images/executor_interruption_test.png)

[*^ back to top*](#Table-of-Contents)
#### Check Spot instance usage and cost savings
Navigate to the [Spot Requests console](https://console.aws.amazon.com/ec2/home?#SpotInstances) -> click on the "Savings summary" button. It will show you how much running cost you have just saved.

![](source/images/4-spot-console.png)

#### Autoscaling & Dynamic resource allocation
The job will finish off with 20 Spark executors/pods on approx. 7 spot EC2 instances. It takes 10 minutes to process and aggregate a large dataset. Based on the resource allocation strategy defined by the [job manifest file](source/example/native-spark-job-scheduler.yaml), it runs 3 executors or 1 driver + 2 executors per EC2 spot instance. 

Once the job is kicked in, you will see the scaling is triggered instantly. It creates a Spark cluster from 0 to 15 executors first. Eventually, the Spark cluster scales to 20 executors, driven by the Dynamic Resource Allocation feature in Spark.

The autoscaling is configured to be balanced across two AZs.
```bash
kubectl get node --label-columns=eks.amazonaws.com/capacityType,topology.kubernetes.io/zone
kubectl get pod -n spark
```
![](source/images/4-auto-scaling.png)

If you are concerned about the job performance, simply fit it into a single AZ by adding the Spark Config to the job submit: 
```yaml
--conf spark.kubernetes.node.selector.topology.kubernetes.io/zone=<availability zone>
```

[*^ back to top*](#Table-of-Contents)
## Useful commands

 * `kubectl get pod -n spark`                         list running Spark jobs
 * `argo submit source/example/nyctaxi-job-scheduler.yaml`  submit a spark job via Argo
 * `argo list --all-namespaces`                       show all jobs scheduled via Argo
 * `kubectl delete pod --all -n spark`                delete all Spark jobs
 * `kubectl apply -f source/app_resources/spark-template.yaml` create a reusable Spark job template

[*^ back to top*](#Table-of-Contents)
## Clean up
Navigate to the source code root directory, and run the clean-up script with your CloudFormation stack name. The default value is 'SparkOnEKS'.If an error "(ResourceInUse) when calling the DeleteTargetGroup operation" occurs, simply run the script again.

The script defaults two inputs:

```bash
export stack_name="${1:-SparkOnEKS}"
export region="${2:-us-east-1}"
```
Run the script with defaults if the CloudFormation stack name and AWS region are unchanged. Otherwise, run it with your parameters.

```bash
cd guidance-for-sql-based-extraction-transformation-and-loading-with-apache-spark-on-amazon-eks
#use default
./deployment/delete_all.sh
```

```bash
#use different CFN name or region
./deployment/delete_all.sh <cloudformation_stack_name> <aws_region>
```

Go to the [CloudFormation console](https://console.aws.amazon.com/cloudformation/home?region=us-east-1), manually delete the remaining resources if needed.

[*^ back to top*](#Table-of-Contents)
## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License. See the [LICENSE](LICENSE.txt) file.
