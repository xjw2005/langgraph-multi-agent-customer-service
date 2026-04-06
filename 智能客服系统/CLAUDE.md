# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an intelligent customer service system built with LangGraph, implementing a multi-agent architecture for handling e-commerce customer inquiries. The system specializes in maternal and infant products with professional domain knowledge and personalized recommendations.

## Architecture

### Multi-Agent System
- **Master-Worker Pattern**: MasterAgent coordinates specialized agents
- **LangGraph State Machine**: Event-driven workflow with state persistence
- **Checkpoint System**: Conversation state recovery and rollback capabilities
- **Dynamic Routing**: Intent-based agent selection with confidence scoring

### Core Components
- `core/main_graph.py`: Main LangGraph workflow orchestrator
- `core/states.py`: Unified state structure (CustomerServiceState)
- `agents/master_agent.py`: Central coordinator for intent recognition and task delegation
- `agents/qa_agent.py`: Professional Q&A with maternal/infant expertise
- `agents/selection_agent.py`: Product recommendation and selection
- `services/database_service.py`: SQLite operations and data persistence

### State Management
The system uses `CustomerServiceState` as the central state container with:
- User context and session management
- Business data (orders, products, logistics)
- Agent processing results and confidence scores
- Performance monitoring and error tracking

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API credentials

# Initialize database
python -m services.database_service
```

### Running the System
```bash
# Basic demo
python examples/basic_demo.py

# Advanced features demo
python examples/advanced_demo.py

# Test specific components
python test_baby_system.py
python test_basic_system.py
```

### Database Operations
```bash
# Initialize/reset database
python -m config.database

# Load knowledge base
python init_knowledge.py
```

## Key Technical Details

### Agent Communication
- All agents inherit from `BaseAgent` with standardized `process()` method
- State flows through LangGraph nodes with `add_messages` annotation
- Agents communicate via shared `CustomerServiceState` object

### Database Schema
- 7 core tables: users, orders, products, conversations, user_preferences, logistics, refunds
- SQLite with checkpoint database for LangGraph state persistence
- Automatic schema initialization and migration support

### RAG System
- Vector store in `rag/vector_store.py` using ChromaDB
- Knotrieval in `rag/retriever.py` with multi-strategy search
- Maternal/infant domain knowledge in `data/` directory

### Configuration
- Environment-based configuration in `config/settings.py`
- Required: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`
- Optional: Database paths, logging levels, confidence thresholds

## Business Logic

### Intent Recognition
The MasterAgent classifies user intents into:
- `product_consultation`: Product information and recommendations
- `order_inquiry`: Order status, modification, cancellation
- `professional_qa`: Maternal/infant care questions
- `general_chat`: Casual conversation

### User Profiling
System tracks user preferences including:
- Baby's age and development stage
- Feeding preferences (breastfeeding/formula)
- Product brand preferences
- Purchase history and behavior patterns

### Conversation Flow
1. User message → MasterAgent intent analysis
2. Route to specialized agent based on confidence score
3. Agent processes with domain knowdge
4. MasterAgent synthesizes final response
5. State persistence and history logging

## Testing and Debugging

### Test Files
- `test_baby_system.py`: End-to-end system testing
- `test_basic_system.py`: Core functionality validation
- `examples/`: Interactive demos and usage examples

### Debugging Tips
- Check `processing_steps` in state for agent execution trace
- Monitor `agent_performance` for timing and confidence metrics
- Use `conversation_history` for full interaction context
- Enable detailed logging via `LOG_LEVEL=DEBUG`

## Extension Points

### Adding New Agents
1. Inherit from `BaseAgent`
2. Implement `prs(state: CustomerServiceState)` method
3. Register intent patterns in `MasterAgent.classify_intent()`
4. Add routing logic in main graph

### Custom Knowledge Domains
1. Extend `rag/vector_store.py` collections
2. Add domain-specific knowledge in `data/`
3. Update retrieval strategies in `rag/retriever.py`
4. Modify agent prompts for new domains

### Database Extensions
1. Add new tables in `config/database.py`
2. Update `services/database_service.py` operations
3. Extend state structure in `core/states.py`
4. Handle migrations in initialization scripts