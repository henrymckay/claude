"""Refuse, before it runs, a call that breaks secure-project's or use-git's hard rules.

A ``PreToolUse`` hook. It reads the hook's JSON on standard input, which is untrusted:
the command, the paths and the cwd may be anything a prompt injection wrote. It never
passes them to a shell, runs git only with list arguments, a time budget and the
repository's hooks, filters, attributes, pager, fsmonitor and external diff out of reach,
and treats a call it cannot check in time as one it must guard.

It guards a force-push or a rewrite of pushed history and the destructive git commands,
deleting a repository or a hosted store, printing a secret, committing a secret, a push to
a remote the standing grant does not name, a change to the grant, and a change to the
configuration that would run code outside the sandbox. It answers ``ask`` when a person
may be present and ``deny`` when nobody is. It is a guard against slips, not a boundary:
a determined command can still get past a parser, which is why an unattended run's
boundary is the run profile.

Runs under any Python from 3.9, the oldest ``python3`` a supported machine ships. It runs
before every tool call, so ``glob``, ``subprocess`` and ``time`` work is deferred to the
checks that need it, and its records are named tuples, since ``dataclasses`` imports
``inspect``, which costs about 120 ms a call under that Python.
"""

from __future__ import annotations

import itertools
import json
import os
import pathlib
import re
import shlex
import sys
import time
import typing

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import grant as grant_

_ALIAS_DEPTH: typing.Final = 5
_DIFF_LIMIT: typing.Final = 4 * 1024 * 1024
_FILE_LIMIT: typing.Final = 512 * 1024
_GIT_CALLS: typing.Final = 30
_GIT_TIMEOUT: typing.Final = 4.0
_GLOB_LIMIT: typing.Final = 200
_INPUT_LIMIT: typing.Final = 1024 * 1024
_NEST_DEPTH: typing.Final = 6
_SECONDS: typing.Final = 20.0
_UNTRACKED_LIMIT: typing.Final = 300

_ANCHORS: typing.Final = frozenset(
    "aws cat curl gcloud gh git glab gsutil http https printenv rclone rm rsync "
    "security wget wrangler".split()
)
_GIT_BUILTINS: typing.Final = frozenset(
    "add am annotate apply archive bisect blame branch bundle cat-file check-ignore "
    "checkout cherry cherry-pick citool clean clone commit config count-objects describe "
    "diff difftool fetch filter-branch filter-repo format-patch fsck gc grep gui help "
    "http-push init log ls-files ls-remote ls-tree maintenance merge merge-base mergetool "
    "mv notes pull push range-diff rebase reflog remote repack replace request-pull reset "
    "restore rev-list rev-parse revert rm send-pack shortlog show show-branch show-ref "
    "sparse-checkout stash status submodule switch symbolic-ref tag update-index "
    "update-ref var verify-commit verify-tag version whatchanged worktree write-tree".split()
)
_GIT_VALUE_OPTIONS: typing.Final = frozenset(
    (
        "-C",
        "-c",
        "--git-dir",
        "--work-tree",
        "--namespace",
        "--exec-path",
        "--config-env",
    )
)
_INTERPRETERS: typing.Final = frozenset(
    "bun deno node osascript perl php python python3 ruby uvx".split()
)
_GRANT_READERS: typing.Final = frozenset(("cat", "head", "tail", "wc", "less"))
_PRINTERS: typing.Final = frozenset("echo logger print printf say tee".split())
_READERS: typing.Final = frozenset(
    "awk base64 bat cat column cp cut dd diff grep head hexdump jq less more nl od open "
    "openssl pbcopy rg scp sed sort strings tac tail tar uniq vi view vim xxd yq zip".split()
)
_RESERVED: typing.Final = frozenset(
    "! { } if then else elif fi do done while until for in case esac function select "
    "time coproc".split()
)
_SHELLS: typing.Final = frozenset("ash bash dash fish ksh sh zsh".split())
_WRAPPERS: typing.Final = frozenset(
    "builtin caffeinate chronic command doas env exec flock ionice nice nohup script "
    "stdbuf sudo timeout unbuffer watch xargs".split()
)
_PUSH_DANGER: typing.Final = (
    "--delete",
    "--force",
    "--force-if-includes",
    "--force-with-lease",
    "--mirror",
    "--prune",
)
_SECRET_FILE: typing.Final = re.compile(
    r"(^|/)("
    r"\.env|\.env\.(?!example$|sample$|template$|dist$)[\w.-]+|[\w.-]+\.env|\.envrc"
    r"|\.netrc|\.pypirc|\.npmrc|\.pgpass|\.dockercfg|\.git-credentials|\.vault-token"
    r"|\.boto|\.s3cfg|\.my\.cnf|\.terraformrc|kubeconfig|token\.json"
    r"|credentials(\.(json|toml|ya?ml|ini|cfg|conf|txt|xml))?|secrets?(\.(json|toml|ya?ml|ini|env|txt))?|application_default_credentials\.json"
    r"|[^/]*service[-_]?account[^/]*\.json|[^/]*\.tfstate(\.backup)?"
    r"|id_[a-z0-9_]+(?<!\.pub)|[^/]*\.(pem|key|p12|pfx|keystore|jks|ppk)"
    r")$"
    r"|(^|/)\.ssh/(?!known_hosts$|config$)[^/]+(?<!\.pub)$"
    r"|(^|/)secrets?/|(^|/)\.kube/config$|(^|/)\.docker/config\.json$"
    r"|(^|/)gh/hosts\.yml$|(^|/)\.claude/\.credentials\.json$|(^|/)\.aws/credentials$",
    re.IGNORECASE,
)
_SECRET_NAMES: typing.Final = (
    ".env",
    ".env.local",
    ".env.production",
    ".envrc",
    ".git-credentials",
    ".netrc",
    ".pgpass",
    ".pypirc",
    "credentials",
    "credentials.json",
    "grant.json",
    "id_ed25519",
    "id_rsa",
    "secrets.json",
    "server.key",
    "server.pem",
)
_SECRET_MENTION: typing.Final = re.compile(
    r"(?<![\w-])(\.env(?![\w.-]*\.(example|sample|template|dist)\b)\b|\.envrc|\.netrc"
    r"|\.pypirc|\.pgpass|\.git-credentials|id_(rsa|dsa|ecdsa|ed25519)|\.ssh/"
    r"|\.aws/credentials|gh/hosts\.yml|\.credentials\.json|\.docker/config\.json)",
    re.IGNORECASE,
)
_SECRET_NAME: typing.Final = (
    r"[A-Za-z_]*(TOKEN|SECRET|PASS(WORD|WD)?|API_?KEY|ACCESS_KEY|PRIVATE_KEY"
    r"|CREDENTIALS?|_PAT|_KEY)(?![A-Za-z0-9_])"
)
_SECRET_VARIABLE: typing.Final = re.compile(
    r"\$\{?!|\$\{?" + _SECRET_NAME, re.IGNORECASE
)
_SECRET_VALUE: typing.Final = re.compile(
    r"AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}"
    r"|(?<![A-Za-z0-9_-])(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{22,}"
    r"|glpat-[A-Za-z0-9_-]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}|sk-ant-[A-Za-z0-9_-]{20,}"
    r"|sk-(proj-)?[A-Za-z0-9_-]{32,}|[sr]k_live_[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{35}"
    r"|eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+"
    r"|[a-z][a-z0-9+.-]*://[^\s:/@'\"$]+:[^\s@/'\"$]{3,}@(?!localhost|127\.0\.0\.1)"
    r"|(?i:(?:api_?key|secret|token|password|passwd|pass|pwd)[\"']?\s*[:=]\s*[\"']?)"
    r"(?=[A-Za-z0-9_\-/+.]*[0-9])(?=[A-Za-z0-9_\-/+.]*[A-Za-z])[A-Za-z0-9_\-/+.]{16,}"
)
_ENV_DUMP: typing.Final = re.compile(
    r"print\s*\(\s*(dict\s*\()?\s*os\.environ\s*\)|os\.environ\.(items|copy|keys|values)"
    r"|json\.dumps\s*\(\s*(dict\s*\()?\s*os\.environ|from\s+os\s+import\s+environ"
    r"|process\.env\s*\)|process\[\s*[\"']env[\"']\s*\]|JSON\.stringify\s*\(\s*process\.env"
    r"|Object\.\w+\s*\(\s*process\.env|ENV\.(to_h|each|inspect|to_a)|%ENV|\b(p|puts|pp)\s+ENV\b"
    r"|getenv\s*\(\s*\)|\$_ENV|\$_SERVER",
)
_CODE_FORCE: typing.Final = re.compile(
    r"push[\"',\s\]]+.{0,40}?(-f\b|--force|--mirror|--delete|\+refs|[\"']\+)",
    re.IGNORECASE | re.DOTALL,
)
_CODE_DELETE: typing.Final = re.compile(
    r"(rmtree|unlink|remove|rm\s+-\w*r)\W.{0,80}?\.git\b", re.IGNORECASE | re.DOTALL
)
_DESTRUCTIVE_SQL: typing.Final = re.compile(
    r"\b(drop\s+\w+|truncate\b|delete\s+from|create\s+or\s+replace\s+(table|schema|database)"
    r"|detach\b|alter\s+\w+\s+\S+\s+rename|update\s+\S+\s+set)\b",
    re.IGNORECASE,
)
_REMOTE_SQL: typing.Final = re.compile(
    r"md:|motherduck|(postgres(ql)?|mysql)://(?!localhost|127\.0\.0\.1)|\bbq\b|snowsql"
    r"|\bpsql\b(?!.*(localhost|127\.0\.0\.1))",
    re.IGNORECASE,
)
_GIT_VARIABLES: typing.Final = (
    "CONFIG|DIR|WORK_TREE|EXEC_PATH|SSH|ALTERNATE|INDEX_FILE|OBJECT_DIRECTORY"
    "|TEMPLATE_DIR|ASKPASS|PROXY_COMMAND|EXTERNAL_DIFF|PAGER|EDITOR|SEQUENCE_EDITOR"
)
_GIT_ENVIRONMENT: typing.Final = re.compile(
    r"(?<![A-Za-z0-9_$])GIT_(" + _GIT_VARIABLES + r")\w*"
    r"(?=\s*=|\s*$|\s*[;&|)\s])"
)
_PUSH_CONFIG: typing.Final = re.compile(
    r"^(remote\.[^.]+\.(push|pushurl|url|mirror)|url\..+\.(pushinsteadof|insteadof)"
    r"|remote\.pushdefault|branch\.[^.]+\.(pushremote|remote)|push\.default)$",
    re.IGNORECASE,
)
_RUNS_CODE_CONFIG: typing.Final = re.compile(
    r"^(alias\..+|filter\..+|core\.(hookspath|fsmonitor|pager|sshcommand|editor"
    r"|attributesfile|gitproxy|askpass)|diff\..+\.(command|textconv)|credential\..*"
    r"|include\.path|includeif\..+)$",
    re.IGNORECASE,
)
_CONFIG_FILE: typing.Final = re.compile(
    r"(^|/)(\.git/(config|hooks/.*|info/attributes)|\.gitattributes|\.claude/settings[^/]*"
    r"\.json|\.claude/hooks/.*|\.mcp\.json|\.gitconfig)$"
)
_MCP_DESTRUCTIVE: typing.Final = re.compile(
    r"(^|_)(delete|drop|trash|destroy|purge|revoke|wipe|clear|erase|remove)(?!_(labels?|tags?))"
    r"(_|$)"
)
_MCP_HIDDEN_DELETE: typing.Final = re.compile(
    r"\"(?i:trashed)\"\s*:\s*true|\"(delete|remove|clear)[A-Z]\w*\"\s*:"
)
_AWS_GLOBAL: typing.Final = frozenset(
    "--profile --region --output --endpoint-url --query --color --ca-bundle "
    "--cli-read-timeout --cli-connect-timeout".split()
)
_STORE_DELETES: typing.Final = (
    ("aws", "dynamodb", "delete-table"),
    ("aws", "rds", "delete-db-cluster"),
    ("aws", "rds", "delete-db-instance"),
    ("aws", "s3", "rb"),
    ("aws", "s3api", "delete-bucket"),
    ("aws", "s3api", "delete-object"),
    ("aws", "s3api", "delete-objects"),
    ("fly", "apps", "destroy"),
    ("flyctl", "apps", "destroy"),
    ("gcloud", "sql", "instances", "delete"),
    ("gcloud", "storage", "buckets", "delete"),
    ("gcloud", "storage", "rm"),
    ("gh", "repo", "delete"),
    ("glab", "repo", "delete"),
    ("gsutil", "rb"),
    ("gsutil", "rm"),
    ("heroku", "apps:destroy"),
    ("netlify", "sites:delete"),
    ("rclone", "delete"),
    ("rclone", "deletefile"),
    ("rclone", "purge"),
    ("rclone", "rmdirs"),
    ("supabase", "projects", "delete"),
    ("vercel", "remove"),
    ("wrangler", "d1", "delete"),
    ("wrangler", "delete"),
    ("wrangler", "kv", "namespace", "delete"),
    ("wrangler", "r2", "bucket", "delete"),
)
_CREDENTIAL_PRINTS: typing.Final = (
    ("aws", "configure", "export-credentials"),
    ("aws", "configure", "get"),
    ("aws", "sts", "get-session-token"),
    ("gcloud", "auth", "print-access-token"),
    ("gcloud", "auth", "print-identity-token"),
    ("gh", "auth", "token"),
    ("heroku", "auth:token"),
    ("keyring", "get"),
    ("op", "read"),
    ("security", "dump-keychain"),
    ("security", "find-generic-password"),
    ("security", "find-internet-password"),
    ("vault", "kv", "get"),
    ("vault", "read"),
)


class OutOfTime(Exception):
    """The guard ran out of its time or git budget before it finished checking."""


class Call(typing.NamedTuple):
    """One tool call as the hook sees it, every field from untrusted input."""

    cwd: pathlib.Path
    permission_mode: str
    tool_input: dict[str, typing.Any]
    tool_name: str


class Context(typing.NamedTuple):
    """What the checks share: the grant, who can answer, and the remaining budget."""

    deadline: float
    git_calls: list[int]
    grant: grant_.Grant | None
    unattended: bool


class Line(typing.NamedTuple):
    """A command line split into simple commands, with what it carries besides."""

    bodies: list[str]
    commands: list[list[str]]


def _spend(context: Context) -> None:
    """Fail when the guard has used up its time.

    :param context: The shared budget.
    :raises OutOfTime: Past the deadline.
    """
    if time.monotonic() > context.deadline:
        raise OutOfTime


def _git(
    context: Context, cwd: pathlib.Path, *arguments: str, allow_fail: bool = False
) -> str:
    """Return a read-only git command's output, run safely in an untrusted repository.

    Command-line settings outrank every config file, so the repository's hooks, pager,
    fsmonitor and attributes file cannot run anything; content filters are refused by
    the callers that would read the work tree (``_worktree_safe``).

    :param context: The shared budget.
    :param cwd: The repository folder.
    :param arguments: The git subcommand and its arguments.
    :param allow_fail: Return empty output for a non-zero exit rather than raise.
    :returns: Its standard output, cut to the diff limit.
    :raises RuntimeError: If git cannot run or fails.
    :raises OutOfTime: If the budget is spent.
    """
    import subprocess  # noqa: PLC0415 - deferred to keep ordinary calls fast

    _spend(context)
    context.git_calls[0] += 1
    if context.git_calls[0] > _GIT_CALLS:
        raise OutOfTime
    command = [
        "git",
        "-c", "core.fsmonitor=false",
        "-c", "core.hooksPath=/dev/null",
        "-c", "core.pager=cat",
        "-c", "core.attributesFile=/dev/null",
        "-c", "diff.external=",
        "-c", "credential.helper=",
        "--no-pager",
        "-C", str(cwd),
        *arguments,
    ]  # fmt: skip
    environment = {
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "HOME": os.environ.get("HOME", "/nonexistent"),
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    }
    remaining = max(0.5, min(_GIT_TIMEOUT, context.deadline - time.monotonic()))
    try:
        done = subprocess.run(
            command,
            capture_output=True,
            check=False,
            env=environment,
            stdin=subprocess.DEVNULL,
            timeout=remaining,
        )
    except (OSError, subprocess.TimeoutExpired) as failure:
        raise RuntimeError(f"git {arguments[0]} could not run") from failure
    if done.returncode != 0 and not allow_fail:
        raise RuntimeError(f"git {arguments[0]} failed")
    return (
        ""
        if done.returncode != 0
        else done.stdout[:_DIFF_LIMIT].decode("utf-8", "replace")
    )


def _worktree_safe(context: Context, cwd: pathlib.Path) -> bool:
    """Return whether git may read the work tree here without running a content filter.

    :param context: The shared budget.
    :param cwd: The repository folder.
    :returns: False where any config the repository sees defines a filter driver.
    """
    found = _git(context, cwd, "config", "--get-regexp", r"^filter\.", allow_fail=True)
    return not found.strip()


def _normalise(text: str) -> str:
    """Return a command line with continuations joined and ``$IFS`` read as a space.

    :param text: The command line.
    :returns: The text the shell would split.
    """
    text = text.replace("\\\r\n", "").replace("\\\n", "")
    text = re.sub(r"\$\(\s*pwd\s*\)|`\s*pwd\s*`", "$PWD", text)
    return re.sub(r"\$\{?IFS([^}\s]*\})?", " ", text)


def _strip_heredocs(text: str) -> tuple[str, list[str]]:
    """Return a command with its terminated here-document bodies removed, and the bodies.

    A body is data to the shell, and an apostrophe in it would otherwise break
    tokenising; an opener with no terminating line is left in place, so a ``<<`` inside
    quotes or a comment hides nothing.

    :param text: The command text.
    :returns: The text without bodies, and each body.
    """
    lines = text.split("\n")
    kept: list[str] = []
    bodies: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        for match in re.finditer(
            r"(?<!<)<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1(?!<)", line
        ):
            end = next(
                (
                    i
                    for i in range(index, len(lines))
                    if lines[i].strip() == match.group(2)
                ),
                None,
            )
            if end is None:
                continue
            bodies.append("\n".join(lines[index:end]))
            index = end + 1
    return "\n".join(kept), bodies


def _expand_braces(word: str) -> list[str]:
    """Return a word's brace expansion, for one level of ``pre{a,b}post``.

    :param word: A word from a command.
    :returns: The words the shell would produce, or the word itself.
    """
    match = re.fullmatch(r"([^{}]*)\{([^{}]*,[^{}]*)\}([^{}]*)", word)
    if not match:
        return [word]
    return [
        f"{match.group(1)}{part}{match.group(3)}" for part in match.group(2).split(",")
    ]


def _split(text: str) -> Line:
    """Return a command line's simple commands and here-document bodies.

    :param text: The command line.
    :returns: The simple commands, each as its words, quotes removed and braces expanded.
    :raises ValueError: If the text cannot be tokenised, such as an unclosed quote.
    """
    stripped, bodies = _strip_heredocs(_normalise(text))
    lexer = shlex.shlex(
        stripped.replace("\n", " ; "), posix=True, punctuation_chars=";&|()<>"
    )
    lexer.whitespace_split = True
    lexer.commenters = ""
    commands: list[list[str]] = [[]]
    for token in lexer:
        if token and set(token) <= set(";&|()"):
            commands.append([])
        elif token and token != "$":
            commands[-1].extend(_expand_braces(token.strip("`")))
    return Line(bodies=bodies, commands=[command for command in commands if command])


def _unwrap(words: list[str]) -> tuple[list[str], list[str]]:
    """Return a command's leading assignments, and its words from the real command name on.

    ``FOO=1 env -i /usr/bin/git push`` gives ``FOO=1`` and ``git push``; reserved words
    such as ``then``, ``do``, ``{`` and ``!`` are dropped, so ``if x; then git push`` is
    read as ``git push``.

    :param words: A simple command's words.
    :returns: The assignments, and the words with the command's path removed.
    """
    assignments: list[str] = []
    rest = list(words)
    while rest:
        head = rest[0]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", head):
            assignments.append(head)
            rest = rest[1:]
            continue
        name = os.path.basename(head.lstrip("\\"))
        if name in _RESERVED:
            rest = rest[1:]
            continue
        if name in _WRAPPERS and any(not word.startswith("-") for word in rest[1:]):
            rest = rest[1:]
            while rest and (
                rest[0].startswith("-")
                or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", rest[0])
                or re.match(r"^\d+(\.\d+)?[smhd]?$", rest[0])
            ):
                takes_value = rest[0] in (
                    "-u",
                    "-n",
                    "-s",
                    "-k",
                    "-g",
                    "-C",
                    "-I",
                    "-L",
                    "-P",
                    "-q",
                    "-c",
                )
                rest = rest[2:] if takes_value else rest[1:]
            continue
        if name == "uv" and len(rest) > 1 and rest[1] == "run":
            rest = rest[2:]
            while rest and rest[0].startswith("-"):
                rest = (
                    rest[2:]
                    if rest[0] in ("--with", "--python", "-p", "--project")
                    else rest[1:]
                )
            continue
        return assignments, [name, *rest[1:]]
    return assignments, []


def _expand_path(word: str, cwd: pathlib.Path) -> str:
    """Return a path word with the variables a delete most often hides behind replaced.

    :param word: The word as written.
    :param cwd: The folder the command runs in.
    :returns: The word with ``$PWD``, ``$(pwd)``, ``$HOME`` and ``~`` expanded.
    """
    home = os.path.expanduser("~")
    word = re.sub(r"\$\{?PWD\}?|\$\(pwd\)|`pwd`", str(cwd), word)
    word = re.sub(r"\$\{?HOME\}?", home, word)
    return os.path.expanduser(word)


def _resolve(cwd: pathlib.Path, path: str) -> pathlib.Path:
    """Return a path from a command, made absolute against the command's folder.

    :param cwd: The folder the command runs in.
    :param path: The path as written.
    :returns: The absolute, normalised path, not resolved through symlinks.
    """
    expanded = pathlib.Path(_expand_path(path, cwd))
    return pathlib.Path(
        os.path.normpath(expanded if expanded.is_absolute() else cwd / expanded)
    )


def _glob(cwd: pathlib.Path, word: str) -> list[str]:
    """Return what a word names after glob expansion, bounded.

    :param cwd: The folder the command runs in.
    :param word: The word.
    :returns: The matches, or the word's own path where nothing matches or it has no glob.
    """
    import glob  # noqa: PLC0415 - deferred to keep ordinary calls fast

    pattern = str(_resolve(cwd, word))
    if not re.search(r"[*?\[]", word):
        return [pattern]
    return list(itertools.islice(glob.iglob(pattern), _GLOB_LIMIT)) or [pattern]


def _read_small(path: pathlib.Path) -> str:
    """Return a small regular file's text, or nothing.

    :param path: The file, from untrusted input.
    :returns: Its text, or empty where it is missing, a symlink, too large or unreadable.
    """
    try:
        if (
            path.is_file()
            and not path.is_symlink()
            and path.stat().st_size <= _FILE_LIMIT
        ):
            return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return ""
    return ""


def _is_secret_path(path: str) -> bool:
    """Return whether a path names, or as a glob could name, a file that holds a secret.

    :param path: The path as written or resolved.
    :returns: True for ``.env`` files, keys, credential stores and the like, and for a
        pattern such as ``.env*`` or ``.en?`` one of them would match.
    """
    import fnmatch  # noqa: PLC0415 - deferred to keep ordinary calls fast

    path = path.replace("\\", "/")
    if _SECRET_FILE.search(path):
        return True
    name = path.rsplit("/", 1)[-1]
    return bool(re.search(r"[*?\[]", name)) and any(
        fnmatch.fnmatch(candidate, name) for candidate in _SECRET_NAMES
    )


def _starts_with(words: list[str], prefix: tuple[str, ...]) -> bool:
    """Return whether a command's non-option words begin with a sequence.

    :param words: The command's words.
    :param prefix: The words to look for, in order.
    :returns: True where they lead the command, options between them allowed.
    """
    plain: list[str] = []
    skip = False
    for word in words:
        if skip:
            skip = False
        elif word.split("=")[0] in _AWS_GLOBAL:
            skip = "=" not in word
        elif not word.startswith("-"):
            plain.append(word)
    return tuple(plain[: len(prefix)]) == prefix


def _is_pushed(context: Context, cwd: pathlib.Path) -> bool:
    """Return whether the current commit is on any remote-tracking branch.

    :param context: The shared budget.
    :param cwd: The repository folder.
    :returns: True where a rewrite from here would change pushed history.
    """
    return bool(_git(context, cwd, "branch", "-r", "--contains", "HEAD").strip())


def _push_urls(context: Context, cwd: pathlib.Path, target: str) -> list[str]:
    """Return every URL a push goes to.

    :param context: The shared budget.
    :param cwd: The repository folder.
    :param target: The remote name or URL the command named, empty for the default.
    :returns: Each push URL, after ``insteadOf`` rewriting, local paths made absolute.
    :raises RuntimeError: If git cannot resolve them.
    """
    if target and ("/" in target or ":" in target):
        urls = [target]
    else:
        if not target:
            upstream = _git(
                context, cwd, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{push}",
                allow_fail=True,
            )  # fmt: skip
            target = upstream.strip().split("/", 1)[0] or "origin"
        urls = _git(
            context, cwd, "remote", "get-url", "--push", "--all", target
        ).split()
    return [
        url
        if re.match(r"^([a-z][a-z0-9+.-]*://|[^/:]+:)", url, flags=re.IGNORECASE)
        else str(_resolve(cwd, url))
        for url in urls
    ]


def _check_push(
    sub: str, arguments: list[str], cwd: pathlib.Path, context: Context
) -> list[str]:
    """Return the findings for a push, its forcing options, refspecs and targets.

    :param sub: ``push``, ``send-pack`` or ``http-push``.
    :param arguments: The words after it.
    :param cwd: The repository folder.
    :param context: The grant and whether anyone is present.
    :returns: A reason per rule the push breaks.
    """
    findings: list[str] = []
    positional: list[str] = []
    repo = ""
    skip = ""
    for word in arguments:
        if skip:
            repo = word if skip == "--repo" else repo
            skip = ""
            continue
        option = word.split("=", 1)[0]
        if (
            option in ("-o", "--push-option", "--repo", "--receive-pack", "--exec")
            and "=" not in word
        ):
            skip = option
        elif option == "--repo":
            repo = word.split("=", 1)[1]
        elif word.startswith("--"):
            if len(option) >= 5 and any(
                full.startswith(option) for full in _PUSH_DANGER
            ):
                findings.append(f"a force-push or remote deletion ({word})")
        elif word.startswith("-") and len(word) > 1:
            if set(word[1:]) & {"f", "d"}:
                findings.append(f"a force-push or remote deletion ({word})")
        else:
            positional.append(word)
    target = repo or (positional[0] if positional else "")
    refspecs = positional[1:] if not repo else positional
    findings += [
        f"a force-push or remote deletion (refspec {refspec})"
        for refspec in refspecs
        if refspec.startswith(("+", ":"))
    ]
    if sub != "push":
        return [*findings, f"a low-level push (git {sub})"]
    remote = (
        "origin" if not target else ("" if "/" in target or ":" in target else target)
    )
    if remote:
        configured = _git(
            context,
            cwd,
            "config",
            "--get-all",
            f"remote.{remote}.push",
            allow_fail=True,
        )
        if any(line.startswith("+") for line in configured.split()):
            findings.append(f"a push whose configured refspec forces ({remote})")
        mirror = _git(
            context, cwd, "config", "--get", f"remote.{remote}.mirror", allow_fail=True
        )
        if mirror.strip().lower() == "true":
            findings.append(f"a push to a mirror remote ({remote})")
    if context.grant is None and not context.unattended:
        return findings
    try:
        urls = _push_urls(context, cwd, target)
    except RuntimeError:
        return [*findings, "a push whose remote could not be resolved"]
    allowed = context.grant.remotes if context.grant else ()
    where = f"grant {context.grant.path}" if context.grant else "no standing grant"
    for url in urls or ["(none)"]:
        key = grant_.remote_key(url, bare_is_host=False)
        if key is None or key not in allowed:
            findings.append(
                f"a push to {key or url!r}, which the {where} does not name"
            )
    return findings


def _check_rewrite(
    sub: str, arguments: list[str], cwd: pathlib.Path, context: Context
) -> list[str]:
    """Return the findings for a git command that rewrites history or discards work.

    A rewrite of commits nobody else has is ordinary local work, so it is guarded only
    where the current commit is already on a remote-tracking branch; the commands
    ``use-git`` calls destructive are guarded wherever they run.

    :param sub: The git subcommand.
    :param arguments: The words after it.
    :param cwd: The repository folder.
    :param context: The shared budget.
    :returns: A reason per rule the command breaks.
    """
    flags = {word.split("=")[0] for word in arguments if word.startswith("-")}
    short = "".join(
        word[1:]
        for word in arguments
        if word.startswith("-") and not word.startswith("--")
    )
    if sub == "clean":
        forced = "f" in short or any(
            "--force".startswith(f) and len(f) > 3 for f in flags
        )
        dry = "n" in short or any(
            "--dry-run".startswith(f) and len(f) > 3 for f in flags
        )
        return (
            ["a git clean that deletes untracked files"] if forced and not dry else []
        )
    if sub == "reset" and flags & {"--hard", "--keep", "--merge"}:
        return [f"a hard reset ({sorted(flags & {'--hard', '--keep', '--merge'})[0]})"]
    if sub == "branch" and (
        flags & {"--force", "-D", "-M", "-C"} or {"f", "D", "M", "C"} & set(short)
    ):
        return ["deleting or force-moving a branch"]
    if sub == "switch" and (flags & {"--force-create", "-C"} or "C" in short):
        return ["force-moving a branch (git switch -C)"]
    if sub == "checkout" and "B" in short:
        return ["force-moving a branch (git checkout -B)"]
    if sub == "stash" and arguments[:1] in (["drop"], ["clear"]):
        return ["dropping stashed work"]
    if sub in ("filter-branch", "filter-repo", "update-ref", "replace"):
        return [f"git {sub}, which rewrites refs or history"]
    if sub == "rebase" and flags & {
        "--abort",
        "--quit",
        "--continue",
        "--skip",
        "--edit-todo",
        "--show-current-patch",
    }:
        return []
    if sub == "commit" and not any(
        f.startswith("--am") and "--amend".startswith(f) for f in flags
    ):
        return []
    if sub == "reset":
        moving = [
            w
            for w in arguments
            if not w.startswith("-") and w != "HEAD" and not _resolve(cwd, w).exists()
        ]
        if not moving or "--" in arguments:
            return []
    if sub not in ("rebase", "commit", "reset"):
        return []
    try:
        pushed = _is_pushed(context, cwd)
    except RuntimeError:
        return [f"git {sub}, which could not be checked against pushed history"]
    return [f"git {sub}, a rewrite of history already pushed"] if pushed else []


def _scan_content(text: str, *, where: str) -> list[str]:
    """Return a finding where text added to a commit looks like a secret.

    :param text: The added lines or a file's content.
    :param where: What the text is, for the finding.
    :returns: One finding, or none.
    """
    return (
        [f"committing what looks like a secret value ({where})"]
        if _SECRET_VALUE.search(text)
        else []
    )


def _check_commit(
    arguments: list[str], cwd: pathlib.Path, context: Context, *, adds: bool
) -> list[str]:
    """Return the findings for what a commit could record: the index, the tracked changes and,
    after a ``git add`` in the same command line, the untracked files too.

    :param arguments: The words after ``commit``.
    :param cwd: The repository folder.
    :param context: The shared budget.
    :param adds: Whether the command line runs ``git add`` first, which the hook cannot see.
    :returns: A reason where the commit would carry a secret or a secret file.
    """
    del arguments
    try:
        staged_names = _git(
            context, cwd, "diff", "--cached", "--name-only", "--no-renames"
        ).split("\n")
        staged = _git(
            context, cwd, "diff", "--cached", "--no-ext-diff", "--no-textconv", "-U0"
        )
        if not _worktree_safe(context, cwd):
            return [
                "a commit in a repository with a content filter, which the guard will not run"
            ]
        tracked_names = _git(context, cwd, "diff", "--name-only", "--no-renames").split(
            "\n"
        )
        tracked = _git(context, cwd, "diff", "--no-ext-diff", "--no-textconv", "-U0")
        untracked = (
            _git(context, cwd, "ls-files", "--others", "--exclude-standard").split("\n")
            if adds
            else []
        )
    except RuntimeError:
        return ["a commit whose content could not be scanned for secrets"]
    findings = [
        f"committing a secret file ({name})"
        for name in [*staged_names, *tracked_names, *untracked]
        if name and _is_secret_path(name)
    ]
    added = "\n".join(
        line
        for line in f"{staged}\n{tracked}".split("\n")
        if line.startswith("+") and not line.startswith("+++")
    )
    findings += _scan_content(added, where="the staged or tracked changes")
    for name in [n for n in untracked if n][:_UNTRACKED_LIMIT]:
        _spend(context)
        findings += _scan_content(_read_small(cwd / name), where=name)
    return findings


def _check_config(arguments: list[str]) -> list[str]:
    """Return the findings for ``git config``: settings that run code or move a push, and
    reads of a stored credential.

    :param arguments: The words after ``config``.
    :returns: A reason per guarded setting.
    """
    reading = any(
        word in ("--get", "--get-all", "--get-regexp", "--list", "-l")
        for word in arguments
    )
    keys = [word.lower() for word in arguments if not word.startswith("-")][:1]
    if reading:
        if any("credential" in w.lower() or "token" in w.lower() for w in arguments):
            return ["reading a credential from git config"]
        return []
    findings: list[str] = []
    for key in keys:
        if _PUSH_CONFIG.match(key):
            findings.append(f"changing where or how git pushes ({key})")
        if _RUNS_CODE_CONFIG.match(key):
            findings.append(
                f"changing git configuration that runs commands or defines aliases ({key})"
            )
    return findings


def _check_git(
    words: list[str],
    assignments: list[str],
    cwd: pathlib.Path,
    context: Context,
    depth: int,
    *,
    adds: bool,
) -> list[str]:
    """Return the findings for a git command, its global options, environment and aliases.

    :param words: The command's words, starting with ``git``.
    :param assignments: Variables set in front of it.
    :param cwd: The folder the command runs in.
    :param context: The grant, whether anyone is present and the budget.
    :param depth: How deep in nested commands this is.
    :param adds: Whether the command line runs ``git add``.
    :returns: A reason per rule the command breaks.
    """
    findings: list[str] = []
    if any(
        re.match(r"^GIT_(CONFIG|DIR|WORK_TREE|EXEC_PATH|SSH|ALTERNATE)", a)
        for a in assignments
    ):
        findings.append(
            "git run with its configuration or repository set from the environment"
        )
    rest = words[1:]
    inline_aliases: dict[str, str] = {}
    while rest and rest[0].startswith("-"):
        option = rest[0]
        name = option.split("=", 1)[0]
        if name in _GIT_VALUE_OPTIONS and "=" not in option:
            value = rest[1] if len(rest) > 1 else ""
            rest = rest[2:]
        else:
            value = option.split("=", 1)[1] if "=" in option else ""
            rest = rest[1:]
        if name in ("-C", "--work-tree"):
            cwd = _resolve(cwd, value)
        elif name == "--git-dir":
            cwd = _resolve(cwd, value).parent
        elif name in ("-c", "--config-env"):
            key, _, setting = value.partition("=")
            if key.lower().startswith("alias."):
                inline_aliases[key[len("alias.") :].lower()] = setting
            elif _PUSH_CONFIG.match(key) or _RUNS_CODE_CONFIG.match(key):
                findings.append(f"git run with {key} overridden on its command line")
    if not rest:
        return findings
    sub, arguments = rest[0], rest[1:]
    for _ in range(_ALIAS_DEPTH):
        if sub in _GIT_BUILTINS:
            break
        alias = inline_aliases.get(sub.lower())
        if alias is None:
            try:
                alias = _git(
                    context, cwd, "config", "--get", f"alias.{sub}", allow_fail=True
                ).strip()
            except RuntimeError:
                alias = ""
        if not alias:
            break
        if alias.startswith("!"):
            return [
                *findings,
                *_check_shell(
                    f"{alias[1:]} {shlex.join(arguments)}", cwd, context, depth + 1
                ),
            ]
        expanded = shlex.split(alias)
        sub, arguments = expanded[0], [*expanded[1:], *arguments]
    if sub in ("push", "send-pack", "http-push"):
        findings += _check_push(sub, arguments, cwd, context)
    findings += _check_rewrite(sub, arguments, cwd, context)
    if sub == "commit":
        findings += _check_commit(arguments, cwd, context, adds=adds)
    if sub == "config":
        findings += _check_config(arguments)
    if sub == "add":
        named = [
            path
            for word in arguments
            if not word.startswith("-")
            for path in _glob(cwd, word)
        ]
        findings += [
            f"staging a secret file ({os.path.basename(p)})"
            for p in named
            if _is_secret_path(p)
        ]
        if any(word in ("-A", "--all", ".", "*", ":/") for word in arguments):
            try:
                untracked = _git(
                    context, cwd, "ls-files", "--others", "--exclude-standard"
                ).split("\n")
            except RuntimeError:
                untracked = []
            findings += [
                f"staging a secret file ({name})"
                for name in untracked
                if name and _is_secret_path(name)
            ]
    if sub in ("show", "cat-file", "diff", "grep", "log", "blame", "archive") and any(
        _is_secret_path(word.split(":", 1)[-1])
        for word in arguments
        if not word.startswith("-")
    ):
        findings.append("printing a secret file through git")
    if sub == "credential" and arguments[:1] == ["fill"]:
        findings.append("printing a stored credential")
    if sub in ("checkout", "restore", "rm", "mv", "stash", "apply") and any(
        grant_.FILE_NAME in word.lower() for word in arguments
    ):
        findings.append("changing the standing grant")
    return findings


def _check_remove(arguments: list[str], cwd: pathlib.Path) -> list[str]:
    """Return the findings for ``rm`` deleting a repository or a home, root or working folder.

    :param arguments: The words after ``rm``.
    :param cwd: The folder the command runs in.
    :returns: A reason per guarded target.
    """
    flags = "".join(word.lstrip("-") for word in arguments if word.startswith("-"))
    if not ({"r", "R"} & set(flags) or "recursive" in flags):
        return []
    home = pathlib.Path(os.path.expanduser("~"))
    findings: list[str] = []
    for word in (w for w in arguments if not w.startswith("-")):
        if (
            sum(
                1 for part in pathlib.PurePath(word).parts if re.search(r"[*?\[]", part)
            )
            > 1
        ):
            findings.append(f"a recursive delete over a wide pattern ({word})")
            continue
        for match in _glob(cwd, word):
            target = pathlib.Path(os.path.normpath(match))
            if target in (pathlib.Path("/"), home) or target in home.parents:
                findings.append(f"deleting {target}")
            elif (
                target.name == ".git"
                or (target / ".git").exists()
                or all((target / part).exists() for part in ("HEAD", "objects", "refs"))
            ):
                findings.append(f"deleting the repository at {target}")
            elif target == cwd or target in cwd.parents:
                findings.append(f"deleting the folder the session works in ({target})")
    return findings


def _method(arguments: list[str]) -> str:
    """Return the HTTP method a ``curl``, ``wget`` or ``gh api`` command names.

    :param arguments: The command's words after its name.
    :returns: The method in upper case, or empty.
    """
    for index, word in enumerate(arguments):
        if word in ("-X", "--request", "--method") and index + 1 < len(arguments):
            return arguments[index + 1].upper()
        if word.startswith(("--request=", "--method=")):
            return word.split("=", 1)[1].upper()
        if re.match(r"^-[A-Za-z]*X", word) and not word.startswith("--"):
            tail = word.split("X", 1)[1]
            if tail:
                return tail.upper()
            if index + 1 < len(arguments):
                return arguments[index + 1].upper()
    return ""


def _check_code(text: str) -> list[str]:
    """Return the findings for code an interpreter or a shell will run from a string.

    :param text: The code.
    :returns: A reason per guarded pattern.
    """
    findings: list[str] = []
    if _SECRET_MENTION.search(text):
        findings.append("a script reading a secret file")
    if _ENV_DUMP.search(text):
        findings.append("a script printing every environment variable")
    if _CODE_FORCE.search(text):
        findings.append("a script that force-pushes")
    if _CODE_DELETE.search(text):
        findings.append("a script that deletes a repository")
    if re.search(r"grant\.json", text, re.IGNORECASE):
        findings.append("a script touching the standing grant")
    if re.search(r"\bgit\b", text) and re.search(r"[\"'\s]push[\"'\s]", text):
        findings.append(
            "a script that pushes, which the guard cannot check against the grant"
        )
    return findings


def _check_words(
    words: list[str],
    assignments: list[str],
    cwd: pathlib.Path,
    context: Context,
    depth: int,
    *,
    adds: bool,
) -> list[str]:
    """Return the findings for one simple command.

    :param words: The command's words, wrappers removed.
    :param assignments: Variables set in front of it.
    :param cwd: The folder the command runs in.
    :param context: The grant, whether anyone is present and the budget.
    :param depth: How deep in nested commands this is.
    :param adds: Whether the command line runs ``git add``.
    :returns: A reason per rule the command breaks.
    """
    name, arguments = words[0], words[1:]
    findings: list[str] = []
    if name in _SHELLS or name in ("eval", "source", "."):
        for word in (w for w in arguments if not w.startswith("-")):
            script = _read_small(_resolve(cwd, word))
            if script:
                findings += _check_shell(script, cwd, context, depth + 1)
    if name == "eval":
        findings += _check_shell(" ".join(arguments), cwd, context, depth + 1)
    if name == "alias":
        for definition in arguments:
            findings += _check_shell(
                definition.partition("=")[2], cwd, context, depth + 1
            )
    if name in _INTERPRETERS or name in _SHELLS:
        findings += [finding for word in arguments for finding in _check_code(word)]
    if name == "git":
        findings += _check_git(words, assignments, cwd, context, depth, adds=adds)
    if name == "rm":
        findings += _check_remove(arguments, cwd)
    if name == "find" and "-delete" in arguments:
        roots = [w for w in arguments if not w.startswith("-")][:1] or ["."]
        filtered = any(
            w in arguments
            for w in (
                "-name",
                "-iname",
                "-path",
                "-ipath",
                "-regex",
                "-newer",
                "-mtime",
            )
        )
        if not filtered and any(
            _resolve(cwd, root) in (cwd, *cwd.parents) for root in roots
        ):
            findings.append(
                "deleting everything under the working folder (find -delete)"
            )
    if any(_starts_with(words, prefix) for prefix in _STORE_DELETES):
        findings.append(f"deleting a hosted resource ({' '.join(words[:4])})")
    if name == "aws" and (
        (_starts_with(words, ("aws", "s3", "rm")) and "--recursive" in arguments)
        or (
            _starts_with(words, ("aws", "s3", "sync"))
            and any(w.startswith("--delete") for w in arguments)
        )
    ):
        findings.append("deleting a hosted store's contents (aws s3)")
    if name == "rsync" and any(w.startswith("--del") for w in arguments):
        destination = [w for w in arguments if not w.startswith("-")][-1:] or [""]
        if re.match(r"^[^/]*:", destination[0]):
            findings.append("an rsync that deletes on a remote host")
    if name in ("gh", "glab") and _starts_with(words, (name, "api")):
        if _method(arguments) == "DELETE" or any(
            "delete" in w.lower() and "mutation" in w.lower() for w in arguments
        ):
            findings.append("a DELETE through the code host's API")
    if name in ("curl", "wget") or (
        name in ("http", "https") and arguments[:1] == ["DELETE"]
    ):
        method = "DELETE" if name in ("http", "https") else _method(arguments)
        hosts = " ".join(w for w in arguments if "://" in w)
        if method == "DELETE" and not re.search(
            r"://(localhost|127\.0\.0\.1|\[::1\])", hosts
        ):
            findings.append("an HTTP DELETE")
    joined = re.sub(r"/\*.*?\*/", " ", " ".join(words).replace("\u00a0", " "))
    if _DESTRUCTIVE_SQL.search(joined) and _REMOTE_SQL.search(joined):
        findings.append("dropping or rewriting data in a hosted database")
    if any(_starts_with(words, prefix) for prefix in _CREDENTIAL_PRINTS) or (
        _starts_with(words, ("gh", "auth", "status"))
        and ("-t" in arguments or "--show-token" in arguments)
    ):
        findings.append(f"printing a stored credential ({' '.join(words[:3])})")
    if name == "printenv" and (
        not arguments
        or any(re.search(_SECRET_NAME, w, re.IGNORECASE) for w in arguments)
    ):
        findings.append("printing environment variables that may hold secrets")
    if name in ("env", "export", "set", "declare", "typeset") and set(arguments) <= {
        "-p",
        "-x",
        "-px",
        "-0",
    }:
        findings.append("printing every environment variable, secrets included")
    if name == "ps" and any(
        re.match(r"^[A-Za-z]*e[A-Za-z]*$|^-[A-Za-z]*E", w) for w in arguments
    ):
        findings.append("printing processes with their environment")
    if name == "jq" and any(w in ("env", "$ENV") or "$ENV" in w for w in arguments):
        findings.append("printing every environment variable through jq")
    if (
        name in ("grep", "rg", "ag", "ack", "git")
        and name != "git"
        and any(
            re.fullmatch(_SECRET_NAME, w, re.IGNORECASE)
            or re.search(r"(?i)^(token|secret|password|api_?key)$", w)
            for w in arguments
            if not w.startswith("-")
        )
    ):
        findings.append("searching files for secret-named values")
    if name in _PRINTERS and any(_SECRET_VARIABLE.search(w) for w in arguments):
        findings.append("printing a secret-named variable")
    if name in _READERS:
        sources = arguments[:-1] if name in ("cp", "scp") else arguments
        for word in sources:
            value = word.split("=", 1)[1] if word.startswith(("if=", "-in=")) else word
            if value.startswith("-"):
                continue
            if any(_is_secret_path(path) for path in [value, *_glob(cwd, value)]):
                findings.append(f"printing a secret file ({value})")
    for redirect, target in zip(arguments, arguments[1:]):
        if redirect == "<" and _is_secret_path(target) and name not in ("source", "."):
            findings.append(f"reading a secret file into a command ({target})")
        if redirect in (">", ">>", ">|", "&>") and (
            any(
                os.path.basename(p).lower() == grant_.FILE_NAME
                for p in _glob(cwd, target)
            )
            or _names_grant(target)
        ):
            findings.append("changing the standing grant")
        if redirect in (">", ">>", ">|", "&>") and _CONFIG_FILE.search(
            str(_resolve(cwd, target))
        ):
            findings.append("changing configuration that runs code outside the sandbox")
    reads_only = name in _GRANT_READERS and not any(
        word.startswith("-") and name == "less" for word in arguments
    )
    if not reads_only and any(_mentions_grant(word, cwd) for word in arguments):
        findings.append("changing the standing grant")
    return findings


def _mentions_grant(word: str, cwd: pathlib.Path) -> bool:
    """Return whether a word could name the standing grant, however it is written.

    One rule, with no option skipped: the name anywhere in the word, in any case, so
    ``-ogrant.json``, ``--output=grant.json`` and a ``sed`` script's ``w grant.json``
    count; or the word, or what follows an option's ``=`` or a short option's letter,
    as a glob that matches it or a path that expands to it.

    :param word: One word of a command, dequoted.
    :param cwd: The folder the command runs in.
    :returns: True where the word may name the grant.
    """
    if grant_.FILE_NAME in word.lower():
        return True
    candidates = {
        word,
        word.split("=", 1)[-1],
        word[2:] if re.match(r"^-[A-Za-z]", word) else word,
    }
    return any(
        _names_grant(candidate)
        or any(_names_grant(match) for match in _glob(cwd, candidate))
        for candidate in candidates
        if candidate
    )


def _check_environment_words(words: list[str], *, pushes: bool) -> list[str]:
    """Return a finding where a command sets git's environment, read from its dequoted words.

    The names come from the command's leading assignments and from the arguments of
    ``export``, ``declare``, ``typeset``, ``local``, ``readonly`` and ``env``, split at the
    first ``=``, so quoting inside a name hides nothing; a name built by an expansion the
    guard cannot resolve counts too where the line pushes.

    :param words: One simple command's words, dequoted.
    :param pushes: Whether the command line runs a ``git push``.
    :returns: One finding, or none.
    """
    names: list[str] = []
    index = 0
    while index < len(words) and words[index] in _RESERVED:
        index += 1
    while index < len(words) and re.match(r"^[^=\s-][^=\s]*=", words[index]):
        names.append(words[index].split("=", 1)[0])
        index += 1
    if index < len(words) and os.path.basename(words[index]) in (
        "declare", "env", "export", "local", "readonly", "typeset",
    ):  # fmt: skip
        names += [
            w.split("=", 1)[0] for w in words[index + 1 :] if not w.startswith("-")
        ]
    for name in names:
        if re.fullmatch(r"GIT_(" + _GIT_VARIABLES + r")\w*", name):
            return [
                "setting git's configuration, repository or commands through the environment"
            ]
        if "$" in name and pushes:
            return ["a variable whose name is built at run time, set beside a push"]
    return []


def _check_shell(
    text: str, cwd: pathlib.Path, context: Context, depth: int = 0
) -> list[str]:
    """Return the findings for a shell command line.

    Every simple command is checked, from the real command name and from each dangerous
    tool named later in it; every here-document body and every word holding a space, the
    usual shape of a command passed as a string, is checked as a command line too.

    :param text: The command line as the Bash tool would run it.
    :param cwd: The folder it starts in.
    :param context: The grant, whether anyone is present and the budget.
    :param depth: How deep in nested commands this is.
    :returns: A reason per rule any command in it breaks.
    """
    _spend(context)
    if depth > _NEST_DEPTH:
        return ["a command nested too deeply to check"]
    findings: list[str] = []
    if _SECRET_VALUE.search(text):
        findings.append("a command carrying a secret-looking value")
    if _GIT_ENVIRONMENT.search(text):
        findings.append(
            "setting git's configuration, repository or commands through the environment"
        )
    try:
        line = _split(text)
    except ValueError:
        return [*findings, "a command the guard could not parse"]
    for inner in re.findall(r"`([^`]*)`", text):
        findings += _check_shell(inner, cwd, context, depth + 1)
    for body in line.bodies:
        findings += _check_code(body)
        findings += _check_shell(body, cwd, context, depth + 1)
    adds = any(
        "add" in words and _unwrap(words)[1][:1] == ["git"] for words in line.commands
    )
    pushes = bool(re.search(r"\bgit\b.*\bpush\b", text, re.DOTALL))
    for words in line.commands:
        findings += _check_environment_words(words, pushes=pushes)
        for word in words:
            if re.search(r"\s", word.strip()) and depth < _NEST_DEPTH:
                findings += _check_shell(word, cwd, context, depth + 1)
        assignments, plain = _unwrap(words)
        if not plain:
            continue
        if plain[0] in ("cd", "pushd") and len(plain) > 1:
            cwd = _resolve(cwd, plain[1])
            continue
        findings += _check_words(plain, assignments, cwd, context, depth, adds=adds)
        for index in range(1, len(plain)):
            if os.path.basename(plain[index]) in _ANCHORS:
                findings += _check_words(
                    [os.path.basename(plain[index]), *plain[index + 1 :]],
                    [],
                    cwd,
                    context,
                    depth,
                    adds=adds,
                )
        if plain[0].startswith("$"):
            joined = " ".join(plain)
            if re.search(r"\bpush\b", joined) and re.search(
                r"(\s-\w*[fd]|--(force|mirror|delete|prune)|\s[+:]\w)", joined
            ):
                findings.append(
                    "what looks like a force-push or remote deletion behind a variable"
                )
    return findings


def _names_grant(word: str) -> bool:
    """Return whether a word names the standing grant, as written or as a pattern.

    :param word: A path from a command.
    :returns: True for ``grant.json`` in any case, or a glob that matches it.
    """
    import fnmatch  # noqa: PLC0415 - deferred to keep ordinary calls fast

    name = os.path.basename(os.path.normpath(word)).lower()
    return name == grant_.FILE_NAME or fnmatch.fnmatch(grant_.FILE_NAME, name)


def check(call: Call, context: Context) -> list[str]:
    """Return why a tool call must be guarded, or nothing where it may run.

    :param call: The tool call.
    :param context: The grant, whether anyone is present and the budget.
    :returns: One reason per rule the call breaks.
    """
    tool, data = call.tool_name, call.tool_input
    if tool == "Bash":
        command = data.get("command")
        if not isinstance(command, str):
            return ["a Bash call with no command"]
        return _check_shell(command, call.cwd, context)
    text = json.dumps(data)
    fields = (
        "file_path",
        "notebook_path",
        "path",
        "glob",
        "pattern",
        "type",
        "url",
        "query",
    )
    if any(field in data and not isinstance(data[field], str) for field in fields):
        return [f"a {tool} call whose input is not the shape Claude Code sends"]
    if tool in ("Read", "NotebookRead"):
        path = str(data.get("file_path", ""))
        real = os.path.realpath(_resolve(call.cwd, path)) if path else ""
        if _is_secret_path(path) or _is_secret_path(real):
            return [f"reading a secret file ({path})"]
        return []
    if tool in ("Grep", "Glob"):
        where = f"{data.get('path', '')} {data.get('glob', '')}".split()
        pattern = str(data.get("pattern", ""))
        findings = []
        if tool == "Grep" and any(_is_secret_path(w) for w in where):
            findings.append("searching a secret file's contents")
        if tool == "Grep" and (
            str(data.get("type", "")).lower() in ("env", "dotenv")
            or re.fullmatch(_SECRET_NAME, pattern, re.IGNORECASE)
            or re.fullmatch(r"(?i)token|secret|password|api_?key", pattern)
        ):
            findings.append("searching files for secret-named values")
        return findings
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = str(
            _resolve(
                call.cwd, str(data.get("file_path", data.get("notebook_path", "")))
            )
        )
        findings = []
        if _names_grant(path) or _names_grant(os.path.realpath(path)):
            findings.append("changing the standing grant")
        if _CONFIG_FILE.search(path) or _CONFIG_FILE.search(os.path.realpath(path)):
            findings.append("changing configuration that runs code outside the sandbox")
        if _SECRET_VALUE.search(text) and not _is_secret_path(path):
            findings.append(
                "writing a secret-looking value into a file that is not a secret file"
            )
        return findings
    if tool in ("WebFetch", "WebSearch"):
        return (
            ["sending a secret-looking value to the web"]
            if _SECRET_VALUE.search(text)
            else []
        )
    if tool.startswith("mcp__"):
        action = tool.split("__", 2)[-1]
        action = (
            re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", action).lower().replace("-", "_")
        )
        findings = []
        if _MCP_DESTRUCTIVE.search(action):
            findings.append(f"a connector call that deletes or revokes ({tool})")
        if _MCP_HIDDEN_DELETE.search(text):
            findings.append(f"a connector call that deletes inside an update ({tool})")
        cleaned = re.sub(r"/\*.*?\*/", " ", text.replace("\\u00a0", " "))
        if _DESTRUCTIVE_SQL.search(cleaned):
            findings.append(f"a connector call that drops or rewrites data ({tool})")
        if _SECRET_VALUE.search(text):
            findings.append(
                f"sending a secret-looking value through a connector ({tool})"
            )
        return findings
    return []


def _is_unattended(permission_mode: str) -> bool:
    """Return whether nobody is present to answer a prompt.

    :param permission_mode: The session's permission mode, from the hook's input.
    :returns: True for a ``claude -p`` run, a launcher's run, or a mode that never asks.
    """
    return (
        os.environ.get("CLAUDE_GUARD") == "deny"
        or os.environ.get("CLAUDE_CODE_SESSION_ATTENDED") == "0"
        or permission_mode in ("bypassPermissions", "dontAsk")
    )


def _context(call: Call, *, started: float) -> Context:
    """Return the grant governing the call's folder, who can answer, and the budget.

    :param call: The tool call.
    :param started: When the hook started, on the monotonic clock.
    :returns: The context; an unreadable or expired grant counts as none.
    """
    project = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or call.cwd)
    found = grant_.find_grant(project)
    try:
        grant = grant_.read_grant(found) if found else None
    except grant_.GrantError:
        grant = None
    return Context(
        deadline=started + _SECONDS,
        git_calls=[0],
        grant=grant,
        unattended=_is_unattended(call.permission_mode),
    )


def _answer(findings: list[str], *, unattended: bool) -> dict[str, typing.Any]:
    """Return the hook's JSON answer for a guarded call.

    :param findings: Why the call is guarded.
    :param unattended: Whether nobody is present to answer a prompt.
    :returns: The ``hookSpecificOutput`` object.
    """
    said = "; ".join(dict.fromkeys(findings))
    if unattended:
        reason = (
            f"Refused by the guard hook (secure-project): {said}. Nobody is present to "
            "approve it. Do not retry it or reach the same end another way; list it in "
            "the report as a step for the owner."
        )
    else:
        reason = f"Guard hook (secure-project): {said}. Approve only if you meant it."
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny" if unattended else "ask",
            "permissionDecisionReason": reason,
        }
    }


def main() -> None:
    """Read the hook's input, check the call and print the decision, if any."""
    started = time.monotonic()
    raw = sys.stdin.buffer.read(_INPUT_LIMIT + 1)
    unattended = _is_unattended("")
    switched_off = os.environ.get("CLAUDE_PLUGIN_OPTION_GUARD", "on") == "off"
    try:
        if len(raw) > _INPUT_LIMIT:
            raise ValueError("input too large")
        data = json.loads(raw.decode("utf-8"))
        tool_input = data.get("tool_input")
        call = Call(
            cwd=pathlib.Path(str(data.get("cwd") or os.getcwd())),
            permission_mode=str(data.get("permission_mode", "")),
            tool_input=tool_input if isinstance(tool_input, dict) else {},
            tool_name=str(data.get("tool_name", "")),
        )
        unattended = _is_unattended(call.permission_mode)
        if switched_off and not unattended:
            return
        findings = check(call, _context(call, started=started))
    except OutOfTime:
        findings = ["a call too large to check in the guard's time"]
    except Exception as failure:  # noqa: BLE001 - any failure must guard, never let the call through
        findings = [f"a call the guard could not check ({type(failure).__name__})"]
    if findings:
        json.dump(_answer(findings, unattended=unattended), sys.stdout)


if __name__ == "__main__":
    main()
