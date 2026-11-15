#!/bin/sh
# tags.sh -- the permanent record of every git tag in this repository, and
# the script that recreates them.
#
#   ./tags.sh            create any missing tag locally (safe to re-run)
#   ./tags.sh --push     ...then push every tag listed here to origin
#   ./tags.sh --dry-run  only show what would happen
#
# Each tag is an annotated tag on a full commit hash, with its original
# date (GIT_COMMITTER_DATE), so rerunning it gives the same tag name, target,
# message and date. The tagger is whoever runs the script.
#
# A tag that already exists is left alone if it points at the recorded
# commit; if it points anywhere else the script stops, so a recorded tag is
# never moved silently.
#
# Add a new tag by appending a `tag` line at the end (newest last), in the
# same commit that is tagged or right after it. Never edit or delete an
# existing line; to retire a tag, add a comment saying so.
set -eu

cd "$(dirname "$0")"

push=0
dry=0
for arg in "$@"; do
	case "$arg" in
	--push) push=1 ;;
	--dry-run) dry=1 ;;
	*) echo "usage: $0 [--push] [--dry-run]" >&2; exit 2 ;;
	esac
done

created=0
present=0
pushed=""

# tag NAME COMMIT DATE MESSAGE
tag() {
	name=$1 commit=$2 date=$3 message=$4
	if ! git cat-file -e "$commit^{commit}" 2>/dev/null; then
		echo "error: $name: commit $commit not found; run 'git fetch origin' first" >&2
		exit 1
	fi
	if git rev-parse -q --verify "refs/tags/$name" >/dev/null; then
		have=$(git rev-parse "$name^{commit}")
		if [ "$have" != "$commit" ]; then
			echo "error: $name exists but points at $have, not $commit" >&2
			exit 1
		fi
		echo "ok      $name -> $commit"
		present=$((present + 1))
	elif [ "$dry" = 1 ]; then
		echo "create  $name -> $commit ($date)"
	else
		GIT_COMMITTER_DATE=$date git tag -a "$name" "$commit" -m "$message"
		echo "created $name -> $commit"
		created=$((created + 1))
	fi
	pushed="$pushed refs/tags/$name"
}

# ---------------------------------------------------------------- the log

tag v1.0-rc1 3d9915ad97ba6457adb35820189ccb52e1e79a5d 2026-11-15T07:46:45Z \
"v1.0-rc1: e32 bare-metal ESP32 with BDD pipeline complete (Phases 0-5)

Release candidate. Still to confirm on a machine with xtensa-esp32-elf-gcc
and Espressif QEMU: make clean all, then tests/run_all.sh."

# ------------------------------------------------------------ end of log

echo "$created created, $present already present"
if [ "$push" = 1 ] && [ -n "$pushed" ]; then
	if [ "$dry" = 1 ]; then
		echo "would push:$pushed"
	else
		# shellcheck disable=SC2086  # one argument per tag
		git push origin $pushed
	fi
fi
