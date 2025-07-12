#!/bin/bash

# Create GitHub repository using API
echo "🚀 Creating GitHub repository 'Driftly-Prompt-Veo3' for user 'apedonkey'"

# You'll need to use your GitHub Personal Access Token
echo "Please enter your GitHub Personal Access Token:"
echo "(Get one from: https://github.com/settings/tokens/new)"
echo "Select scopes: repo, workflow"
read -s GITHUB_TOKEN

echo ""
echo "Creating repository..."

# Create the repository using GitHub API
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/user/repos \
     -d '{
       "name": "Driftly-Prompt-Veo3",
       "description": "AI-powered video automation studio using Grok 3 and Google Veo 3",
       "private": false,
       "has_issues": true,
       "has_projects": false,
       "has_wiki": false,
       "auto_init": false
     }'

echo ""
echo "✅ Repository created!"
echo ""
echo "Now pushing your code..."

# Add remote and push
git remote add origin https://github.com/apedonkey/Driftly-Prompt-Veo3.git
git push -u origin main

echo ""
echo "🎉 Done! Your repository is live at:"
echo "https://github.com/apedonkey/Driftly-Prompt-Veo3"