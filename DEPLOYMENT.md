# Deployment Guide

## Render Deployment

### Step 1: Prepare Your Repository

1. Ensure all files are committed:
   ```bash
   git add .
   git commit -m "Initial commit"
   ```

2. Push to GitHub:
   ```bash
   git remote add origin https://github.com/StefanVaskovic-SD/SD-User-personas.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com
   - Sign in or create an account

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub account if not already connected
   - Select the repository: `SD-User-personas`

3. **Configure the Service:**
   - **Name:** `user-persona-generator` (or your preferred name)
   - **Region:** Choose closest to your users
   - **Branch:** `main`
   - **Root Directory:** (leave empty)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

4. **Add Environment Variables:**
   - Click "Advanced" → "Add Environment Variable"
   - Add: `GEMINI_API_KEY` = `your-api-key-here`
   - Add (optional): `GEMINI_MODEL` = `gemini-2.5-flash`

5. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy your application
   - Wait for deployment to complete (usually 2-5 minutes)

6. **Access Your App:**
   - Once deployed, you'll get a URL like: `https://user-persona-generator.onrender.com`
   - The app will auto-deploy on every push to main branch

### Alternative: Using render.yaml

If you prefer to use the `render.yaml` file:

1. The file is already configured in the repository
2. In Render dashboard, instead of manual configuration:
   - Go to "New +" → "Blueprint"
   - Connect your repository
   - Render will automatically detect and use `render.yaml`

### Environment Variables on Render

Required:
- `GEMINI_API_KEY`: Your Gemini API key from Google AI Studio

Optional:
- `GEMINI_MODEL`: Model name (default: `gemini-2.5-flash`)

### Troubleshooting

**Build fails:**
- Check that `requirements.txt` is correct
- Ensure Python version is 3.9 or higher

**App won't start:**
- Verify the start command includes `--server.address=0.0.0.0`
- Check that `$PORT` is used (Render sets this automatically)

**API errors:**
- Verify `GEMINI_API_KEY` is set correctly in environment variables
- Check API quota and limits

**Slow cold starts:**
- Render free tier has slower cold starts (~30 seconds)
- Consider upgrading to paid plan for faster response times

## Local Testing

Before deploying, test locally:

```bash
streamlit run app.py
```

Then test with production-like settings:

```bash
PORT=8501 streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

