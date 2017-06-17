Created from https://aws.amazon.com/blogs/devops/integrating-git-with-aws-codepipeline/
Changes done to make it work under CodePipeline environment

### Contributing
While creating zip Lambda package, make sure to not provide the parent dir
For CreateSSHKey it will be `cd CreateSSHKey && zip -r ../CreateSSHKey.zip .`
