# GitHub publishing commands

GitHub CLI was not installed in the release environment, so repository creation
could not be authenticated or performed automatically.

From the repository root:

```bash
brew install gh
gh auth login
gh repo create global-equity-council --public --source=. --remote=origin --push
```

If the public repository already exists:

```bash
git remote add origin git@github.com:YOUR_ACCOUNT/global-equity-council.git
git push -u origin main
```

Replace `YOUR_ACCOUNT` only in the manual fallback. Do not paste a token into
the repository or remote URL.
