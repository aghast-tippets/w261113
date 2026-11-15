# Repository notes for Claude

## Tags

`tags.sh` at the repository root is the permanent log of every git tag, and
the script that recreates them (`./tags.sh --push`).

- Whenever you create, or are asked to create, a tag, append a `tag` line
  for it to the log section of `tags.sh` in the same change: full commit
  hash, ISO-8601 UTC date, and the exact tag message. Newest last.
- Never edit or remove an existing line. To retire a tag, add a comment.
- Cloud sessions cannot push tags (the git proxy refuses them), so record
  the tag in `tags.sh`, push that commit, and tell the user to run
  `./tags.sh --push` on their machine.
