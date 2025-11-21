#!/bin/bash

# Deep Research Agent - LangGraph Cloud Deployment Script
# This script helps automate the deployment process

set -e  # Exit on any error

echo "================================================"
echo "Deep Research Agent - LangGraph Cloud Deployment"
echo "================================================"
echo ""

# Check if langgraph CLI is installed
if ! command -v langgraph &> /dev/null; then
    echo "Error: langgraph CLI not found!"
    echo "Install it with: pip install langgraph-cli"
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "Warning: .env file not found!"
    echo "Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Please edit .env with your API keys before deploying"
        exit 1
    else
        echo "Error: .env.example not found!"
        exit 1
    fi
fi

# Check if user is logged in
echo "Checking LangGraph Cloud authentication..."
if ! langgraph whoami &> /dev/null; then
    echo "Not logged in. Please login first:"
    langgraph login
fi

echo ""
echo "Current user:"
langgraph whoami
echo ""

# Ask for confirmation
read -p "Deploy to LangGraph Cloud? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Deploy
echo ""
echo "Starting deployment..."
langgraph deploy

echo ""
echo "================================================"
echo "Deployment completed!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Set environment variables in LangGraph Cloud:"
echo "   langgraph env set TAVILY_API_KEY=your_key"
echo "   langgraph env set ANTHROPIC_API_KEY=your_key"
echo ""
echo "2. Test your deployment:"
echo "   langgraph invoke research_agent '{\"messages\": [{\"role\": \"human\", \"content\": \"test query\"}]}'"
echo ""
echo "3. Monitor your agent in LangGraph Studio:"
echo "   langgraph studio"
echo ""
