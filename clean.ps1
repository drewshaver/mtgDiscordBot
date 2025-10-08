$ErrorActionPreference = "Stop"

Remove-Item -ErrorAction SilentlyContinue cards.db
Remove-Item -ErrorAction SilentlyContinue main.db
Remove-Item -ErrorAction SilentlyContinue users.db
