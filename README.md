### Introduction
Integrates 3rd party git providers (Github, Bitbucket, GitHub Enterprise or GitLab) with AWS S3, and deploy via CodeDeploy or CodePipeline.

The project consists of 3 Cloudformation templates each of which can be deployed independent of each other.
1. `git_intgrtn_aws_s3_main.json`: Creates integration between AWS S3 and 3rd party git providers.
2. `codedeploy_main.json`: Creates EC2 with pre-installed CodeDeploy agent and all other required resources. (**Repository must contain a valid `appspec.yml`**)
3. `ecs_main.json`: Creates AWS CodePipeline that will deploy from S3. (**Deployment via CodePipeline works only under AWS ECS**)


### PreRequisites
* ACM verified certificate
* EC2 KeyPair
* IAM user attached with Administrator policy
* Repository hosted in Github/Bitbucket/GitHub Enterprise or GitLab
* DNS NS records hosted in Route53


### Architectural Overview
![Architectural diagram](https://github.com/droidlabour/git_intgrtn_aws_s3/raw/master/cloudcraft.png)

1. `git_intgrtn_aws_s3_main.json`:

    Webhooks notify a remote service by issuing an HTTP POST when a commit is pushed to the repository. [AWS Lambda](http://aws.amazon.com/lambda) receives the HTTP POST through [Amazon API Gateway](https://aws.amazon.com/api-gateway), and then downloads a copy of the repository. It places a zipped copy of the repository into a versioned S3 bucket. [AWS CodePipeline](http://aws.amazon.com/codepipeline) can then use the zip file in S3 as a source; the pipeline will be triggered whenever the Git repository is updated.

    There are two methods you can use to get the contents of a repository. Each method exposes Lambda functions that have different security and scalability properties.

    - **Zip download** uses the Git provider's HTTP API to download an already-zipped copy of the current state of the repository.
        - No need for external libraries.
        - Smaller Lambda function code.
        - Large repo size limit (500 MB).

    - **Git pull** uses SSH to pull from the repository. The repository contents are then zipped and uploaded to S3.
        - Efficient for repositories with a high volume of commits, because each time the API is triggered, it downloads only the changed files.
        - Suitable for any Git server that supports hooks and SSH; does not depend on personal access tokens or OAuth2.
        - More extensible because it uses a standard Git library.

2. `codedeploy_main.json` creates
    * Multi-AZ, load balanced and auto scaled (CPU Utilization) pre-installed with **CodeDeploy Agent**, **Docker** and **docker-compose**.
    * AWS CodeDeploy Application and DeploymentGroup.
    * Trigger CodeDeploy on `s3:ObjectCreated:*`

3. `ecs_main.json` creates
    * ECS Cluster
    * ECR Repository
    * ECS Service and Task Definition
    * CodePipeline with CodeBuild and Deployment using Cloudformation

4. `buildspec.yml` can be used to build on AWS CodeBuild.

### Deploying to region other then us-east-1
1. Create zip file for `AddS3LambdaNotification`, `CreateSSHKey`, `DeleteBucketContents`, `GitPull`, `LambdaStageCodePipeline` and `ZipDownload` directories
Note: While creating zip, make sure to not provide the parent dir
Example: For `CreateSSHKey` it will be `cd CreateSSHKey && zip -r ../CreateSSHKey.zip . && cd ..`
2. Upload all the zip files to an S3 Bucket under `git_intgrtn_aws_s3` directory in the same region where you want the stack to be deployed.
