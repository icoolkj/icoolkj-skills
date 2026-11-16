# Repository Standards

## License

This repository is licensed under the **MIT License**. The root `LICENSE` file is authoritative. Keep its copyright and permission notice in all copies or substantial portions of the Software.

- SPDX identifier: `MIT`
- Do not replace the standard MIT text with a shortened custom license.
- A Skill's `license` frontmatter must match the license that actually applies to its files.
- If a subdirectory contains third-party or differently licensed material, document the exception at the relevant path and in `THIRD_PARTY_NOTICES.md`.

## Copyright and author metadata

For first-party files where a header is appropriate:

```text
Copyright (c) YYYY icoolkj
SPDX-License-Identifier: MIT
```

Do not insert comment headers into formats where they break parsing. Do not claim authorship of third-party assets or external contributions.

## Skill frontmatter

Use the field order and required fields documented in the root README's **元数据规范** section. Required fields include `name`, `description`, `version`, `display_name`, `display_name_en`, `description_zh`, `description_en`, `author`, and `license`.

- `name` must equal the skill directory name and use lowercase hyphen-case.
- `version` must use SemVer without a `v` prefix.
- `license` must be the actual applicable license, not an assumed default.
- Repository and contact metadata must use the canonical project URL and maintained contact.

## Third-party notices

When distributing third-party code, fonts, icons, images, templates, datasets, or copied/adapted text, add `THIRD_PARTY_NOTICES.md` with the asset path, source, rightsholder, exact license, modifications, attribution requirements, and redistribution status.

Unknown or unapproved assets are marked `HOLD` and must not enter release ZIPs.

## Release requirements

Every release package must retain the applicable license and notices, include version and installation information, and be traceable to a source commit. A release is blocked when metadata conflicts with the actual license or required attribution is missing.
