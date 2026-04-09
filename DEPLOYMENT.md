# 🚀 Deployment Guide: AgentForge on Vercel

This guide will help you deploy AgentForge to Vercel with the beautiful animated frontend.

## Prerequisites

- GitHub account with the AgentForge repository
- Vercel account (free at https://vercel.com)
- API keys for LLM providers (OpenAI, Anthropic, or Google)

## Step 1: Connect GitHub Repository

1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Select "Import Git Repository"
4. Find and select `Puneetdivedi/AgentForge` repository
5. Click "Import"

## Step 2: Configure Environment Variables

In the Vercel dashboard, add the following environment variables:

```
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4
ANTHROPIC_API_KEY=your-anthropic-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229
GOOGLE_API_KEY=your-google-key
GOOGLE_MODEL=gemini-pro
CHROMA_HOST=your-chroma-instance.com
CHROMA_PORT=8001
REDIS_HOST=your-redis-instance.com
REDIS_PORT=6379
DEBUG=false
LOG_LEVEL=INFO
```

## Step 3: Configure Build Settings

Vercel should auto-detect the Python project. Ensure:

- **Build Command**: Leave empty (uses vercel.json)
- **Output Directory**: Leave empty
- **Install Command**: Use default

## Step 4: Deploy

1. Click "Deploy"
2. Wait for the build and deployment to complete
3. Your site will be live at `https://your-project.vercel.app`

## What Gets Deployed

- **Frontend**: Animated HTML/CSS/JS interface served as static files
- **API**: FastAPI backend as Vercel serverless functions
- **Routes**:
  - `/` - Homepage with chat interface
  - `/api/v1/chat` - Chat endpoint
  - `/api/v1/agents` - List agents
  - `/api/v1/health` - Health check

## Frontend Features

- ⚡ Animated hero section with rotating orb
- 🎨 Glassmorphism design with gradients
- 💬 Real-time chat interface
- 🔄 Smooth loading animations
- 📱 Fully responsive design
- 🌙 Dark mode ready

## Using the Chat

1. Open the deployed URL
2. Scroll down to the "Try AgentForge" section
3. Type your message in the chat input
4. Click send or press Enter
5. Wait for the agent's response

## Production Considerations

### Database & Memory

For production, you should set up:

- **Redis Instance**: For caching and short-term memory
  - Consider: Redis Cloud, AWS ElastiCache, or similar
  - Update `REDIS_HOST` and `REDIS_PORT`

- **Vector Database**: For RAG functionality
  - Consider: ChromaDB Cloud, Pinecone, Weaviate
  - Update `CHROMA_HOST` and `CHROMA_PORT`

### API Rate Limiting

Currently, there's no rate limiting. Consider adding:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/chat")
@limiter.limit("30/minute")
async def chat(request):
    # ...
```

### CORS Configuration

The API is currently open to all origins. For production, restrict this:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Logging & Monitoring

Uses structured JSON logging. Send logs to a service like:
- Datadog
- New Relic
- CloudWatch
- Sentry (for errors)

### SSL/HTTPS

Vercel provides free SSL certificates. All traffic is automatically HTTPS.

## Troubleshooting

### Chat not working

1. Check that API server is running (`/api/v1/health` should return 200)
2. Check browser console for errors (F12)
3. Ensure environment variables are set correctly
4. Check server logs in Vercel dashboard

### Build failing

1. Check build logs in Vercel dashboard
2. Ensure all dependencies in `requirements.txt`
3. Verify `vercel.json` configuration
4. Check for Python syntax errors

### Cold starts

Serverless functions may have cold start delays. Solutions:
- Keep functions warm with periodic pings
- Optimize function code for faster execution
- Use Redis for caching responses

## Scaling

As you grow, consider:

1. **Load Balancing**: Vercel handles this automatically
2. **Database Scaling**: Upgrade Redis/ChromaDB instances
3. **Cost Optimization**: Monitor Vercel deployment metrics
4. **Performance**: Implement caching and compression

## Advanced Customization

### Custom Domain

1. In Vercel dashboard, go to Project Settings
2. Click "Domains"
3. Add your custom domain
4. Update DNS records as instructed

### CI/CD

Every push to main automatically deploys. To customize:

1. Create `.github/workflows/deploy.yml`
2. Add custom build/test steps
3. Trigger on specific branch/tag patterns

### Environment Variants

Create different environments for staging/production:

1. Create branches: `main`, `staging`, `develop`
2. Create projects for each branch
3. Manage separate environment variables

## Cost Estimation

With Vercel's free tier:
- **Functions**: 1,000,000 invocations/month free
- **Bandwidth**: 1,000 GB/month included
- **Storage**: Limited storage for environments

Paid services you'll need:
- **LLM APIs**: Depends on usage (OpenAI ~$0.03 per 1K tokens)
- **Vector DB**: Varies ($0-50+/month)
- **Redis**: $0-100+/month depending on size
- **Vercel Pro**: $20/month (optional, for production)

## Resources

- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI on Vercel](https://vercel.com/guides/using-fastapi-correctly-in-a-vercel-serverless-function)
- [AgentForge GitHub](https://github.com/Puneetdivedi/AgentForge)
- [OpenAI API Docs](https://platform.openai.com/docs)

## Support

For issues or questions:
- Check GitHub Issues
- Review Vercel logs
- Contact support teams for respective services

---

**Deployed and ready to scale! 🚀**
