#!/bin/bash

# Deployment script for Google Cloud Run

echo "🚀 Deploying Agentic Timetable Planner to Cloud Run"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    exit 1
fi

# Read configuration
read -p "Enter your GCP Project ID: " PROJECT_ID
read -p "Enter your Gemini API Key: " GEMINI_API_KEY
read -p "Enter deployment region [us-central1]: " REGION
REGION=${REGION:-us-central1}

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and deploy
echo "🔨 Building container..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/timetable-planner

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy timetable-planner \
  --image gcr.io/$PROJECT_ID/timetable-planner \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY,GCP_PROJECT_ID=$PROJECT_ID \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10

echo "✅ Deployment complete!"
echo "🌐 Your application should be available at the URL shown above."
