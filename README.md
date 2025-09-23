# naughty-chats

A modern AI-powered character chat and image generation platform built with FastAPI backend and Azure infrastructure.

## 🚀 Features

- **Character Management**: Create, discover, and interact with AI characters
- **Real-time Chat**: WebSocket-based streaming chat with AI characters
- **Image Generation**: AI-powered image generation with multiple quality tiers
- **Gem Economy**: Virtual currency system for monetization
- **Affiliate Program**: Built-in referral system with commission tracking
- **Production Ready**: Azure-native infrastructure with auto-scaling and monitoring

## 🏗️ Architecture

### Backend (FastAPI)
- **Authentication**: JWT-based with refresh token rotation
- **Characters API**: Full CRUD with search, filtering, and favorites
- **Chat API**: WebSocket streaming with session management
- **Generation API**: Async image generation with queue management
- **Gems API**: Payment processing and transaction history
- **User Management**: Profiles, sessions, and notifications

### Infrastructure (Azure)
- **Container Apps**: Auto-scaling containerized backend
- **Cosmos DB**: Global NoSQL database for all app data
- **Front Door**: CDN with WAF and HTTPS termination
- **Key Vault**: Centralized secrets management
- **Service Bus**: Async job processing queues
- **Storage Account**: Generated image and file storage

## 🛠️ Setup and Deployment

### Local Development

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the backend**:
   ```bash
   cd /path/to/naughty-chats
   python -c "from backend.app import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8080)"
   ```

4. **Test the API**:
   ```bash
   curl http://localhost:8080/
   curl http://localhost:8080/api/v1/characters
   curl http://localhost:8080/api/v1/gems/packs
   ```

### Azure Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment instructions.

**Quick deployment**:
1. Configure GitHub secrets (see DEPLOYMENT.md)
2. Push to main branch for dev deployment
3. Use workflow dispatch for prod deployment

## 📋 API Endpoints

### Public Endpoints
- `GET /` - Health check
- `GET /api/v1/characters` - List characters (with filtering)
- `GET /api/v1/tags` - Available character tags
- `GET /api/v1/gems/packs` - Gem pack catalog
- `GET /api/v1/affiliates/leaderboard` - Public affiliate stats
- `GET /api/v1/status` - System status

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - User logout

### Protected Endpoints (Require Authentication)
- `GET /api/v1/me` - Current user profile
- `PATCH /api/v1/me/profile` - Update profile
- `POST /api/v1/characters` - Create character
- `POST /api/v1/chat/sessions` - Start chat session
- `WebSocket /api/v1/chat/ws/{session_id}` - Real-time chat
- `POST /api/v1/generate` - Submit image generation
- `GET /api/v1/generate/jobs/{job_id}` - Check generation status
- `GET /api/v1/affiliates/me` - My affiliate stats
- `POST /api/v1/gems/checkout` - Purchase gems

## 🔧 Testing

```bash
# Run backend tests
cd backend
python -m pytest tests/ -v

# Test API endpoints
curl http://localhost:8080/api/v1/characters
curl http://localhost:8080/api/v1/gems/packs
```

## 📊 Monitoring

The application includes comprehensive monitoring:
- **Application Insights**: Performance and error tracking
- **Log Analytics**: Centralized logging
- **Azure Monitor**: Infrastructure monitoring
- **Front Door Analytics**: CDN and security metrics

## 🔒 Security Features

- **WAF Protection**: OWASP rules and custom security policies
- **HTTPS Only**: All traffic encrypted in transit
- **Managed Identity**: No stored credentials
- **Key Vault Integration**: Centralized secret management
- **Rate Limiting**: API and authentication rate limits
- **Input Validation**: Comprehensive request validation

## 🎯 Current Status

✅ **Completed**:
- Complete backend API implementation
- Production-ready Azure infrastructure
- CI/CD pipeline with GitHub Actions
- Comprehensive documentation
- Security and monitoring setup

🚧 **In Progress**:
- Frontend implementation
- Test suite completion
- Production deployment

## 📖 Documentation

- [Deployment Guide](./DEPLOYMENT.md) - Complete Azure deployment instructions
- [Backend Architecture](./backend.md) - Detailed backend design
- [Infrastructure Plan](./deployments.md) - Azure architecture overview
- [Screen Specifications](./screens.md) - Frontend requirements
- [Product Requirements](./PRD.md) - Complete product specification

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
