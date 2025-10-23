# GitHub Setup Guide for Fork

## Quick Start: Set Up Required Secrets

Since you have GitHub CLI configured, we can set up secrets quickly:

### Step 1: Create Personal Access Token (if needed)

Your current token has scopes: `admin:public_key`, `gist`, `read:org`, `repo`

**You need a token with `packages:read` and `packages:write` scopes.**

Create one at: https://github.com/settings/tokens/new

**Required scopes:**
- ✅ `repo` (Full control of private repositories)
- ✅ `read:packages` (Download packages from GitHub Package Registry)
- ✅ `write:packages` (Upload packages to GitHub Package Registry)

**Suggested name:** "Azure Orbital Space SDK - CI/CD"

**Copy the token** - you'll need it in the next step!

### Step 2: Set GitHub Secrets (Using CLI)

Run these commands to set up the secrets:

```bash
# Set your GitHub username
gh secret set GIT_HUB_USER_NAME -b "montge" -R montge/azure-orbital-space-sdk-client

# Set your Personal Access Token (you'll be prompted to paste it)
gh secret set GIT_HUB_USER_TOKEN -R montge/azure-orbital-space-sdk-client
# Paste your token when prompted and press Enter

# Set the setup repository URL
gh secret set SETUP_REPO_URL -b "https://github.com/microsoft/azure-orbital-space-sdk-setup" -R montge/azure-orbital-space-sdk-client
```

### Step 3: Verify Secrets

```bash
gh secret list -R montge/azure-orbital-space-sdk-client
```

You should see:
```
GIT_HUB_USER_NAME     Updated YYYY-MM-DD
GIT_HUB_USER_TOKEN    Updated YYYY-MM-DD
SETUP_REPO_URL        Updated YYYY-MM-DD
```

## Alternative: Set Secrets via Web UI

If you prefer using the web interface:

1. Go to: https://github.com/montge/azure-orbital-space-sdk-client/settings/secrets/actions

2. Click "New repository secret" for each:

   **Secret 1: GIT_HUB_USER_NAME**
   - Name: `GIT_HUB_USER_NAME`
   - Value: `montge`

   **Secret 2: GIT_HUB_USER_TOKEN**
   - Name: `GIT_HUB_USER_TOKEN`
   - Value: Your Personal Access Token (from Step 1)

   **Secret 3: SETUP_REPO_URL**
   - Name: `SETUP_REPO_URL`
   - Value: `https://github.com/microsoft/azure-orbital-space-sdk-setup`

## Security Best Practices

### About the Secrets

1. **GIT_HUB_USER_NAME**: Your GitHub username
   - Used for: Authenticating to GitHub Container Registry
   - Sensitivity: Low (public information)

2. **GIT_HUB_USER_TOKEN**: Personal Access Token
   - Used for: Pulling/pushing packages during CI/CD
   - Sensitivity: HIGH - Treat like a password!
   - Rotate periodically (every 90 days recommended)

3. **SETUP_REPO_URL**: Repository URL
   - Used for: Cloning azure-orbital-space-sdk-setup during builds
   - Sensitivity: Low (public repository)

### Token Security

- ✅ Set expiration date (90 days recommended)
- ✅ Use minimum required scopes
- ✅ Never commit tokens to git
- ✅ Rotate tokens regularly
- ✅ Revoke old tokens after rotation

## Troubleshooting

### "Permission denied" during workflow

**Problem**: GitHub Actions can't access packages
**Solution**: Verify PAT has `read:packages` and `write:packages` scopes

### "Repository not found" for SETUP_REPO_URL

**Problem**: GitHub Actions can't clone azure-orbital-space-sdk-setup
**Solution**:
- Verify URL is correct
- Check if repository is accessible (public or you have access)
- If using your own fork, update URL to: `https://github.com/montge/azure-orbital-space-sdk-setup`

### Secrets not visible in workflow logs

**This is expected!** GitHub automatically masks secrets in logs for security.

## Next Steps

After setting up secrets:

1. ✅ Trigger a workflow run
2. ✅ Monitor the build at: https://github.com/montge/azure-orbital-space-sdk-client/actions
3. ✅ Verify artifacts are published

## Enable Code Scanning (Advanced Security)

GitHub Advanced Security provides code scanning to detect vulnerabilities.

### For Public Repositories (Free)

Code scanning is FREE for public repos! Enable it:

```bash
# Enable code scanning via CLI
gh api -X PATCH repos/montge/azure-orbital-space-sdk-client \
  -f security_and_analysis='{"advanced_security":{"status":"enabled"},"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}'
```

Or via Web UI:
1. Go to: https://github.com/montge/azure-orbital-space-sdk-client/settings/security_analysis
2. Enable "Code scanning" (CodeQL analysis)
3. Enable "Secret scanning"
4. Enable "Push protection"

CodeQL will automatically scan your code for security vulnerabilities!
