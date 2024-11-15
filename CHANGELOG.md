## v1.1.1 (2024-11-15)

### Fix

- nothing changed but bump version to kick-off release

## v1.1.0 (2024-11-15)

### Feat

- use XDG specification for file locations (#40)

## v1.0.3 (2024-05-06)

### Fix

- no longer strip words in brackets from descriptions (#26)

### Refactor

- move version to constants (#27)

## v1.0.2 (2024-02-13)

### Fix

- **index**: improve persisting customizations (#25)

## v1.0.1 (2024-02-05)

### Fix

- don't migrate db on first-run (#23)

## v1.0.0 (2024-02-04)

### Feat

- Release v1.0.0
- migrate to > v0.3.0

### Fix

- show number of commands as table footer

## v0.4.0 (2024-02-04)

### Feat

- recategorize commands (#22)

### Fix

- **db**: track cli version for future migrations (#21)

## v0.3.0 (2024-02-03)

### Feat

- customize command descriptions (#16)
- above and inline comments for descriptions (#15)

### Refactor

- **typing**: enforce mypy strict_optional

## v0.2.0 (2024-01-24)

### Feat

- add `uncategorized_name` to config
- explain commands with options (#13)
- search by command name or code (#12)
- improve configuration management (#11)

### Fix

- improve `--list` table view (#14)

## v0.1.0 (2024-01-21)

### Feat

- python >= 3.10 (#10)
- provide user feedback when no commands (#9)
- improve configuration file editing (#8)
- initial commit

### Fix

- fix bug preventing database creation
