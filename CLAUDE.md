# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend (Next.js)
```bash
cd frontend
npm run dev          # Development server
npm run dev:fast     # Development server with Turbo
npm run build        # Production build
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt  # Install dependencies
python main.py                   # Start development server
uvicorn main:app --reload        # Alternative dev server

# Testing
pytest                           # Run all tests
pytest -m integration          # Run integration tests only
pytest backend/data_transformation/run_tests.py  # Run transformation tests
```

## Project Architecture

### High-Level Structure
This is a full-stack application with a **Next.js frontend** and **FastAPI backend** using **Supabase** as the database. The system implements a multi-agent architecture using Hugging Face's `smolagents` for AI-powered data analysis and chart generation.

### Multi-Agent System
The core AI system consists of:
- **AgentManager**: Orchestrates multiple specialized agents
- **DatabaseAgent**: Handles database queries and data retrieval
- **ChartGenerationAgent**: Generates visualization code
- **Manager Agent**: Coordinates between agents and handles user interactions

### Backend Architecture (Layered)
- **API Layer**: FastAPI routers for different modules
- **Agent Layer**: AI agents and their tools/services
- **Core Layer**: Business logic with repository pattern
  - `database/`: Connection management
  - `models/`: Pydantic data models
  - `repositories/`: Data access layer
  - `services/`: Business services
- **Module Layer**: Feature-specific modules
  - `dashboard/`: Analytics and insights
  - `scraping/`: Amazon data scraping
  - `review_analysis/`: Review processing pipeline
  - `product_segment/`: Product categorization
  - `data_transformation/`: Data processing

### Frontend Architecture
- **Next.js 15** with React 19
- **Tailwind CSS** with custom components
- **Recharts** for data visualization
- **Supabase** for authentication and data
- Component structure:
  - `analysis-db/`: Dashboard and analytics components
  - `auth/`: Authentication components
  - `chat/`: Chat interface for agent interaction
  - `ui/`: Reusable UI components

### Key Configuration
- **Models**: Configured per region (CN uses OpenRouter/Claude, US uses Google Gemini)
- **Database**: Supabase with service-level access
- **Monitoring**: Phoenix monitoring for agent performance
- **Streaming**: SSE for real-time agent responses

## Key Development Patterns

### Agent Integration
- All agents are managed through `AgentManager` with proper lifecycle management
- Use `stream_agent_response` for real-time user interactions
- Monitor agent performance with Phoenix integration

### Data Flow
```
Frontend → API → Agent System → Database Tools → Supabase
```

### Testing Strategy
- Unit tests for individual components
- Integration tests for agent workflows
- End-to-end tests for complete data pipelines
- Use pytest markers for test categorization

### Database Operations
- Use repository pattern for data access
- Service layer for complex business logic
- Supabase client for real-time features

## Critical Dependencies
- `smolagents`: Core AI agent framework
- `fastapi`: Backend API framework
- `supabase`: Database and auth
- `next.js`: Frontend framework
- `recharts`: Chart visualization
- `arize-phoenix`: Agent monitoring

## Environment Setup
- Backend requires environment variables for model configuration (REGION, MODEL_ID, API_KEY)
- Frontend requires Supabase configuration
- Test environment needs proper database setup