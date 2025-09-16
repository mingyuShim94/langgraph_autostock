# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LangGraph study repository containing documentation and conceptual materials for learning LangGraph framework for building AI systems, particularly focused on autonomous trading systems.

## Architecture and Design Philosophy

### Core System Architecture
The repository documents a **self-learning autonomous trading system** that operates as two interconnected LangGraph workflows:

1. **Trading Graph (Operational Loop)** - Real-time trading execution that runs hourly/daily:
   - Portfolio diagnosis and market analysis
   - Decision-making with justification recording
   - Risk validation and order execution
   - Comprehensive trade logging to central database

2. **Reflection & Improvement Graph (Learning Loop)** - Weekly learning cycle:
   - Performance data aggregation and analysis
   - Success/failure pattern identification
   - Strategy rule generation from insights
   - Automatic system logic updates

### Key Design Patterns

**Self-Evolution**: The system learns from past trades by analyzing recorded decision justifications and outcomes, then automatically updates its core decision-making prompts.

**Database-Centric Memory**: All trading decisions, market context, and justifications are stored in a central database that serves as the system's memory and learning foundation.

**LangGraph Progression Levels** (from documentation):
- **LV 1**: Simple sequential flows (Observer pattern)
- **LV 2**: Conditional branching (Rule-Follower pattern)
- **LV 3**: Multi-agent analysis (Strategist pattern)
- **LV 4**: Portfolio management (Fund Manager pattern)
- **LV 5**: Self-learning cycles (Master pattern)

## Development Context

This appears to be a **documentation and design repository** rather than an implementation repository. No actual code files, build scripts, or dependencies were found.

### Repository Structure
```
docs/
├── all_architecture.md      # Complete system architecture
├── dev_guide.md            # 5-level LangGraph development guide
└── langgraph_easy_concept.md # LangGraph concepts and patterns
```

## LangGraph Framework Concepts

### Core Components
- **Nodes**: Individual processing units (portfolio analysis, market analysis, etc.)
- **Edges**: Flow control between nodes (sequential, conditional, cyclical)
- **State**: Shared data object passed between nodes
- **Conditional Edges**: Dynamic routing based on state conditions
- **Human-in-the-Loop**: Interrupts for user input integration

### Advanced Patterns
- **Multi-Agent Systems**: Multiple specialized agents coordinated by supervisors
- **Cyclical Flows**: Loops for iterative improvement (reflection cycles)
- **Memory Integration**: Database-backed persistent memory across sessions
- **Self-Modification**: Systems that update their own logic based on performance

## Working with This Repository

Since this is a documentation repository:
- Focus on understanding the architectural concepts
- Use the progression levels (LV 1-5) as implementation guidelines
- The trading system design serves as a comprehensive LangGraph application example
- Consider the database schema and dual-graph architecture when implementing similar systems

## Key Insights for Implementation

1. **Database Design**: Critical for self-learning systems - must capture decision justifications and market context
2. **Graph Separation**: Separate operational and learning workflows for clear responsibility boundaries
3. **Progressive Complexity**: Build systems incrementally following the 5-level progression
4. **Memory Persistence**: Essential for systems that need to learn and improve over time