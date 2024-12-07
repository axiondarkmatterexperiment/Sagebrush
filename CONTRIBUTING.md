# Contributing to Sagebrush

## Workflow

See the sections following this one for details on Git conventions and CI/CD

### Adding a feature

This also applies to fixing a bug that only exists on the develop branch.

1. Create a feature branch
2. Develop **and test** your feature; for example:
    1. Do initial development
    2. Push your branch to GitHub
    3. Create a *draft* [pull request](https://github.com/axiondarkmatterexperiment/Sagebrush/pulls) (PR) to merge your branch into the *develop* branch
    4. Perform any tests on your feature
    5. Make sure the `test_docker` job completes in GitHub Actions
    6. If necessary, make more changes and repeat 2.4 and 2.5
3. Continue steps 2.4 through 2.6 until your feature works
4. **Do not skip testing**
5. Convert your PR into a non-draft PR
6. Get your work reviewed
7. Ensure that the `test_docker` and `build_and_push` jobs complete in GitHub Actions
8. Once approved, repository owner will merge your branch into the develop branch

### Making a hotfix

1. Create a hotfix branch
2. Develop **and test** your fix; for example:
    1. Do initial development
    2. Push your branch to GitHub
    3. Create a *draft* [pull request](https://github.com/axiondarkmatterexperiment/Sagebrush/pulls) (PR) to merge your branch into the *main* branch
    4. Perform any tests on your feature
    5. Make sure the `test_docker` job completes in GitHub Actions
    6. If necessary, make more changes and repeat 2.4 and 2.5
3. Continue steps 2.4 through 2.6 until your feature works
4. **Do not skip testing**
5. Convert your PR into a non-draft PR
6. Get your work reviewed
7. Ensure that the `test_docker` and `build_and_push` jobs complete in GitHub Actions
8. Once approved, repository owner will merge your branch into the main branch, and merge that into the develop branch; create a new tag

## Git Conventions

We use the [Git Flow](https://nvie.com/posts/a-successful-git-branching-model) convention for branching.  For most purposes, the modifications you're making should be classified either as a hotfix, or a feature:

* Hotfix: fixing a bug in released code (i.e. on the main branch).  Gets merged into main and typically results in incrementing the patch version number.
* Feature: adding a new capability to the code or fixing a bug in the develop branch (but not the main branch).  Gets merged into the develop branch and can either result in incrementing the minor or patch version numbers.

Feature and hotfix branches should be short-lived.  If you're doing long-term development, where the main and/or develop branches might diverge significantly from your branch while you do the work, it's best to break your work into multiple shorter stages and merge back into develop for each stage.

Releases will be performed by the repository owner(s).

## CI/CD

We use GitHub actions for our CI/CD purposes.  The main workflow consists of two jobs, `test_docker` and `build_and_push`:

* `test_docker`: runs for draft pull requests, pull requests, and pushes to the main and develop branches.  Builds the Sagebrush Docker image, dev version, for the AMD64 platform.
* `build_and_push`: runs for pull requests (non-draft), and pushes to the main and develop branches.  Builds Sagebrush Docker images, both dev and prod versions, for the AMD64 and ARM64 platforms.  For pushes to the main and develop branches, the images are pushed to GitHub Container Registry.
