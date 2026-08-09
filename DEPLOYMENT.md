# Deployment Guide

## Prerequisites

1. **Databricks Workspace** with Apps V2 enabled
2. **Lakebase Postgres** instance with movies database
3. **API Keys**:
   - OpenAI API key (for agent)
   - Databricks workspace token

## Step 1: Set Up Secrets

Create the following secrets in your Databricks workspace:

```bash
# Lakebase connection (base64 encoded)
databricks secrets put-secret \
  --scope <your-scope> \
  --key lakebase-connection-url \
  --string-value "<base64-encoded-connection-url>"

# OpenAI API key
databricks secrets put-secret \
  --scope <your-scope> \
  --key openai-api-key \
  --string-value "<your-openai-key>"

# Databricks credentials
databricks secrets put-secret \
  --scope <your-scope> \
  --key databricks-host \
  --string-value "<workspace-url>"

databricks secrets put-secret \
  --scope <your-scope> \
  --key databricks-token \
  --string-value "<your-token>"
```

## Step 2: Update app.yaml

Update the `app.yaml` file with your secret scope:

```yaml
env:
  - name: LAKEBASE_CONNECTION_URL
    secret: <your-scope>/lakebase-connection-url
  - name: OPENAI_API_KEY
    secret: <your-scope>/openai-api-key
```

## Step 3: Deploy the App

### Option A: Using Databricks CLI

```bash
cd /Workspace/Users/<your-email>/ai-movie-night-planner

# Deploy
databricks apps deploy . --source-dir .
```

### Option B: Using the UI

1. Navigate to **Apps** in Databricks workspace
2. Click **Create App**
3. Select **From Repository**
4. Point to your workspace folder
5. Click **Deploy**

## Step 4: Verify Deployment

1. Wait for app to reach **Running** state
2. Click on the app URL
3. Test the chat interface:
   - "Find me a comedy"
   - "What should we watch tonight?"
   - "Show me movies like Inception"

## Step 5: Monitor

```bash
# Check app status
databricks apps get <app-name>

# View logs
databricks apps logs <app-name>

# Restart if needed
databricks apps restart <app-name>
```

## Troubleshooting

### App won't start
- Check logs: `databricks apps logs <app-name>`
- Verify secrets are set correctly
- Ensure Lakebase connection is accessible

### Agent errors
- Verify OpenAI API key is valid
- Check LangChain/LangGraph are installed (requirements.txt)
- Test agent locally first

### Database connection errors
- Verify connection URL is base64 encoded
- Check Lakebase instance is running
- Test connection from notebook first

## Local Testing

Before deploying, test locally:

```bash
cd streamlit_app

# Set environment variables
export LAKEBASE_CONNECTION_URL="<connection-url>"
export OPENAI_API_KEY="<your-key>"

# Run Streamlit
streamlit run app.py
```

## Updating the App

After making changes:

```bash
# Re-deploy
databricks apps deploy . --source-dir . --force
```

## Resources

- [Databricks Apps Documentation](https://docs.databricks.com/apps/)
- [Lakebase Documentation](https://docs.databricks.com/lakebase/)
- [Streamlit Documentation](https://docs.streamlit.io/)
