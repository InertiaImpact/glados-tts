@Library('shared-jenkins-pipelines') _

// source:
// https://git.sudo.is/ben/shared-jenkins-pipelines/src/branch/main/vars/poetry.groovy

poetry(
    docker: true,
    dockreg: "git.sudo.is/ben",

    pip_publish: true,
    pip_repo_url: "https://git.sudo.is/api/packages/ben/pypi",

    pip_publish_tags_only: false
    //push_git_tag: true

)
