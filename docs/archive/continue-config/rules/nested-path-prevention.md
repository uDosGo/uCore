---
description: Prevent and detect nested/duplicated file paths when creating files
---

When creating files or editing, always verify the file path is correct by running `ls -la <filepath>` after writing. If the path is nested/duplicated (e.g. `/Users/user/Code/proj/Users/user/Code/proj/file`), use a fix script to move it to the correct location. When in doubt, use `realpath <relative-path>` to resolve the intended absolute path before creating a file.