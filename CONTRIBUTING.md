# Contributing <!-- omit in TOC -->

First of all, thank you for contributing to Meilisearch! The goal of this document is to provide everything you need to know in order to contribute to Meilisearch and its different integrations.

- [Hacktoberfest](#hacktoberfest-2022)
- [Assumptions](#assumptions)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Git Guidelines](#git-guidelines)
- [Release Process (for internal team only)](#release-process-for-internal-team-only)

## Hacktoberfest 2022

It's [Hacktoberfest month](https://hacktoberfest.com)! 🥳

Thanks so much for participating with Meilisearch this year!

1. We will follow the quality standards set by the organizers of Hacktoberfest (see detail on their [website](https://hacktoberfest.digitalocean.com/resources/qualitystandards)). Our reviewers will not consider any PR that doesn’t match that standard.
2. PRs reviews will take place from Monday to Thursday, during usual working hours, CEST time. If you submit outside of these hours, there’s no need to panic; we will get around to your contribution.
3. There will be no issue assignment as we don’t want people to ask to be assigned specific issues and never return, discouraging the volunteer contributors from opening a PR to fix this issue. We take the liberty to choose the PR that best fixes the issue, so we encourage you to get to it as soon as possible and do your best!

You can check out the longer, more complete guideline documentation [here](https://github.com/meilisearch/.github/blob/main/Hacktoberfest_2022_contributors_guidelines.md).

## Assumptions

1. **You're familiar with [GitHub](https://github.com) and the [Pull Request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests)(PR) workflow.**
2. **You've read the Meilisearch [documentation](https://docs.meilisearch.com) and the [README](/README.md).**
3. **You know about the [Meilisearch community](https://docs.meilisearch.com/resources/contact.html). Please use this for help.**

## How to Contribute

1. Make sure that the contribution you want to make is explained or detailed in a GitHub issue! Find an [existing issue](https://github.com/meilisearch/meilisearch-gcp/issues/) or [open a new one](https://github.com/meilisearch/meilisearch-gcp/issues/new).
2. Once done, [fork the meilisearch-gcp repository](https://help.github.com/en/github/getting-started-with-github/fork-a-repo) in your own GitHub account. Ask a maintainer if you want your issue to be checked before making a PR.
3. [Create a new Git branch](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-and-deleting-branches-within-your-repository).
4. Make the changes on your branch.
5. [Submit the branch as a PR](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork) pointing to the `main` branch of the main meilisearch-gcp repository. A maintainer should comment and/or review your Pull Request within a few days. Although depending on the circumstances, it may take longer.<br>
 We do not enforce a naming convention for the PRs, but **please use something descriptive of your changes**, having in mind that the title of your PR will be automatically added to the next [release changelog](https://github.com/meilisearch/meilisearch-gcp/releases/).

## Development Workflow

### Setup <!-- omit in toc -->

```bash
pip3 install -r requirements.txt
```

### Tests and Linter <!-- omit in toc -->

Each PR should pass the tests and the linter to be accepted.

```bash
# Linter
pylint tools
```

## Git Guidelines

### Git Branches <!-- omit in TOC -->

All changes must be made in a branch and submitted as PR.
We do not enforce any branch naming style, but please use something descriptive of your changes.

### Git Commits <!-- omit in TOC -->

As minimal requirements, your commit message should:
- be capitalized
- not finish by a dot or any other punctuation character (!,?)
- start with a verb so that we can read your commit message this way: "This commit will ...", where "..." is the commit message.
  e.g.: "Fix the home page button" or "Add more tests for create_index method"

We don't follow any other convention, but if you want to use one, we recommend [this one](https://chris.beams.io/posts/git-commit/).

### GitHub Pull Requests <!-- omit in TOC -->

Some notes on GitHub PRs:

- [Convert your PR as a draft](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/changing-the-stage-of-a-pull-request) if your changes are a work in progress: no one will review it until you pass your PR as ready for review.<br>
  The draft PR can be very useful if you want to show that you are working on something and make your work visible.
- The branch related to the PR must be **up-to-date with `main`** before merging. If it's not, you have to rebase your branch. Check out this [quick tutorial](https://gist.github.com/curquiza/5f7ce615f85331f083cd467fc4e19398) to successfully apply the rebase from a forked repository.
- All PRs must be reviewed and approved by at least one maintainer.
- The PR title should be accurate and descriptive of the changes.

## Release Process (for internal team only)

⚠️ The [cloud-scripts](https://github.com/meilisearch/cloud-scripts) repository should be upgraded to the new version before this repository can be updated and released.

The release tags of this package follow exactly the Meilisearch versions.<br>
It means that, for example, the `v0.17.0` tag in this repository corresponds to the GCP image running Meilisearch `v0.17.0`.

This repository currently does not provide any automated way to test the GCP Meilisearch image.<br>
**Please, follow carefully the steps in the next sections before any release.**

### Set your environment <!-- omit in TOC -->

After cloning this repository, install python dependencies with the following command:

```bash
pip3 install -r requirements.txt
```

Before running any script, make sure to [set your GCP credentials](https://cloud.google.com/docs/authentication/getting-started) locally. Make sure that youhave access to the project `meilisearchimage`, or ask a maintainer for a Service Account access.<br>

### Test before Releasing <!-- omit in TOC -->

1. Add your SSH key to the Compute Engine platform, on the [metadata section](https://console.cloud.google.com/compute/metadata/sshKeys?project=meilisearchimage&authuser=1&folder&organizationId=710828868196). Set the name of the user defined on your SSH key as a value for the `SSH_USER` variable in the [`tools/config.py`](tools/config.py) script. (I.E. If your SSH key finishes by `myname@mylaptop` use `myname` as the value of `SSH_USER`)

2. In [`tools/config.py`](tools/config.py), update the `MEILI_CLOUD_SCRIPTS_VERSION_TAG` variable value with the new Meilisearch version you want to release, in the format: `vX.X.X`. If you want to test with a Meilisearch RC, replace it by the right RC version tag (`vX.X.XrcX`).

3. Run the [`tools/build_image.py`](tools/build_image.py) script to build the GCP custom image without analytics:

```bash
python3 tools/build_image.py --no-analytics
```

This command will create an GCP Compute Instance on Meilisearch's account and configure it in order to prepare the Meilisearch custom image. It will then create an Image, which should be ready to be published in the following steps. The instance will automatically be terminated after the custom image creation.<br>
The image name will be `Meilisearch-vX-X-X-ubuntu-X--lts-build--XX-XX-XXXX`.

4. Test the image: create a new GCP Compute instance based on the new image `Meilisearch-vX-X-X-ubuntu-X--lts-build--XX-XX-XXXX`, and make sure everything is running smoothly. Remember to check the following checkboxes: `Allow HTTP traffic` and `Allow HTTPS traffic`. Connect via SSH to the droplet and test the configuration script that is run automatically on login. Use the same username defined in the step 1 and in the SSH key you have set on GCP.<br>
🗑 Don't forget to destroy the Droplet after the test.

5. When you are ready to create the final image to release juste remove the `--no-analytics` option

```bash
python3 tools/build_image.py
```

### Publish the GCP image and Release <!-- omit in TOC -->

⚠️ The GCP image should never be published with a `RC` version of Meilisearch.

Once the tests in the previous section have been done:

1. Set the image name that you TESTED and you want to publish as the value of the `PUBLISH_IMAGE_NAME` in [`tools/config.py`](tools/config.py). Use the exact name of the IMAGE that you built in the previous step: `Meilisearch-vX-X-X-ubuntu-X--lts-build--XX-XX-XXXX`. 

2. Run the [`tools/publish_image.py`](tools/publish_image.py) script to export and publish the GCP image:

```bash
python3 tools/publish_image.py
```

3. Commit your changes on a new branch.

4. Open a PR from the branch where changes where done and merge it.

5. Create a git tag on the last `main` commit:

```bash
git checkout main
git pull origin main
git tag vX.X.X
git push origin vX.X.X
```

⚠️ If changes where made to the repository between your testing branch was created and the moment it was merged, you should consider building the image and testing it again. Some important changes may have been introduced, unexpectedly changing the behavior of the image that will be published to the Marketplace.

### Clean old GCP images <!-- omit in TOC -->

Make sure that the last 2 versions of the Meilisearch image are available and public. Our goal is to always offer the latest Meilisearch version to GCP users, but we are keeping the previous version in case there is a bug or a problem in the latest one. Any other older version of the image must be deleted.

To proceed to delete older images that should no longer be available, use the GCP user interface, since this task hasn't yet been automated.

### Update the GCP image between two Meilisearch Releases  <!-- omit in TOC -->

It can happen that you need to release a new GCP image but you cannot wait for the new Meilisearch release.<br>
For example, the `v0.17.0` is already pushed but you find out you need to fix the installation script: you can't wait for the `v0.18.0` release and need to re-publish the `v0.17.0` GCP image.

In this case:

- Apply your changes and reproduce the testing process (see [Test before Releasing](#test-before-releasing)).
- Delete the current tag remotely and locally:

```bash
git push --delete origin vX.X.X
git tag -d vX.X.X
```

- Publish the GCP image again (see [Publish the GCP image and Release](#publish-the-gcp-image-and-release))

<hr>

Thank you again for reading this through, we can not wait to begin to work with you if you made your way through this contributing guide ❤️
