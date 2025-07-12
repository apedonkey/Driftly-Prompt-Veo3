# Security Checklist - Before Making Repository Public

## ⚠️ CRITICAL: Complete ALL items before going public!

### 🔴 High Priority - Secrets & Credentials

- [ ] **Rotate ALL exposed credentials**
  - [ ] Grok API key (x.ai dashboard)
  - [ ] FAL API key (fal.ai dashboard)
  - [ ] Google service account (Google Cloud Console)
  - [ ] YouTube OAuth credentials
  - [ ] Google Sheets API access

- [ ] **Clean repository history**
  ```bash
  # Remove .env from git history if it was ever committed
  git filter-branch --force --index-filter \
    "git rm --cached --ignore-unmatch .env" \
    --prune-empty --tag-name-filter cat -- --all
  
  # Remove config files
  git filter-branch --force --index-filter \
    "git rm --cached --ignore-unmatch config/*.json" \
    --prune-empty --tag-name-filter cat -- --all
  ```

- [ ] **Verify .gitignore is working**
  ```bash
  # This should return nothing
  git ls-files | grep -E "(\.env|config/.*\.json|\.log)"
  ```

### 🟠 Code Security Fixes

- [ ] **Fix hardcoded secrets** ✅ (Already fixed Flask SECRET_KEY)
- [ ] **Add file upload validation**
  ```python
  # Add to app.py
  ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
  app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
  ```

- [ ] **Remove sensitive data from logs**
  - Configure logger to mask API keys
  - Clear existing log files with secrets

### 🟡 Before Going Public

1. **Run the secret checker**
   ```bash
   python3 check_secrets.py
   ```
   Should return: "✅ No exposed secrets found!"

2. **Create proper documentation**
   - Update README.md without any real keys
   - Use .env.example as reference
   - Add setup instructions

3. **Add security notice**
   ```markdown
   ## Security Notice
   This project requires API keys. Never commit real credentials.
   See `.env.example` for required environment variables.
   ```

4. **Consider using GitHub Secrets**
   - For GitHub Actions
   - For deployment workflows

### 📋 Final Verification

Run this command to ensure no secrets remain:
```bash
# Search for common secret patterns
grep -r -E "(xai-|ya29\.|1//|private_key|client_secret)" . \
  --exclude-dir=.git \
  --exclude-dir=venv \
  --exclude-dir=logs \
  --exclude="*.pyc" \
  --exclude="check_secrets.py"
```

This should return NO results except in .env.example or documentation.

### 🚀 Safe to Publish Checklist

- [ ] All API keys rotated
- [ ] No secrets in git history
- [ ] .gitignore properly configured
- [ ] Secret checker returns clean
- [ ] Documentation uses only example keys
- [ ] File upload security implemented
- [ ] Logs don't contain secrets

## Remember: Once public, assume ALL old keys are compromised!