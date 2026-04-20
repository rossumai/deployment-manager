"""Tests for hook/sync/helpers.py - git URL parser for GitHub/GitLab/Bitbucket."""

from deployment_manager.commands.hook.sync.helpers import parse_git_file_url


class TestGithubUrlParsing:
    def test_standard_blob_url(self):
        url = "https://github.com/rossumai/deployment-manager/blob/main/hooks/my_hook.py"
        repo, branch, path = parse_git_file_url(url)
        assert repo == "https://github.com/rossumai/deployment-manager.git"
        assert branch == "main"
        assert path == "hooks/my_hook.py"

    def test_deeply_nested_file_path(self):
        url = "https://github.com/u/r/blob/dev/a/b/c/d/file.py"
        _, branch, path = parse_git_file_url(url)
        assert branch == "dev"
        assert path == "a/b/c/d/file.py"

    def test_www_prefix(self):
        url = "https://www.github.com/u/r/blob/main/file.py"
        repo, _, _ = parse_git_file_url(url)
        assert repo is not None


class TestGitlabUrlParsing:
    def test_standard_blob_url_with_dash(self):
        url = "https://gitlab.com/mygroup/myrepo/-/blob/main/hooks/my_hook.py"
        repo, branch, path = parse_git_file_url(url)
        assert repo == "git@gitlab.com:mygroup/myrepo.git"
        assert branch == "main"
        assert path == "hooks/my_hook.py"

    def test_custom_gitlab_instance(self):
        # Custom GitLab: must have `gitlab` in hostname AND `.` for domain
        url = "https://gitlab.mycompany.com/group/repo/-/blob/prod/file.py"
        repo, branch, path = parse_git_file_url(url)
        assert repo == "git@gitlab.mycompany.com:group/repo.git"
        assert branch == "prod"


class TestBitbucketUrlParsing:
    def test_standard_src_url(self):
        url = "https://bitbucket.org/u/r/src/master/hooks/my_hook.py"
        repo, branch, path = parse_git_file_url(url)
        assert repo == "git@bitbucket.org:u/r.git"
        assert branch == "master"
        assert path == "hooks/my_hook.py"


class TestUnknownHost:
    def test_returns_none_tuple(self):
        url = "https://unknown-host.com/u/r/blob/main/file.py"
        repo, branch, path = parse_git_file_url(url)
        assert (repo, branch, path) == (None, None, None)

    def test_malformed_url(self):
        repo, branch, path = parse_git_file_url("not a url at all")
        assert (repo, branch, path) == (None, None, None)
