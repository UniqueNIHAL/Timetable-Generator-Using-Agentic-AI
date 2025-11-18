#!/bin/bash

# Deploy Agentic Timetable Planner to Google Cloud Run with Firebase Auth
# Run this script from the project root directory

set -e  # Exit on error

echo "🚀 Deploying Agentic Timetable Planner with Firebase Authentication..."

# Configuration
PROJECT_ID="bnb-blr-478413"
REGION="europe-west1"
SERVICE_NAME="timetable-planner"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

# Check if firebase-service-account.json exists
if [ ! -f "firebase-service-account.json" ]; then
    echo "❌ Error: firebase-service-account.json not found!"
    echo "Please download the service account key from Firebase Console"
    exit 1
fi

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: GEMINI_API_KEY environment variable not set!"
    echo "Export it first: export GEMINI_API_KEY=your_api_key"
    exit 1
fi

echo "📦 Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} --project ${PROJECT_ID}

echo "🔐 Uploading service account to Secret Manager..."
# Create or update secret
if gcloud secrets describe firebase-service-account --project ${PROJECT_ID} >/dev/null 2>&1; then
    echo "Secret already exists, updating..."
    gcloud secrets versions add firebase-service-account \
        --data-file=firebase-service-account.json \
        --project ${PROJECT_ID}
else
    echo "Creating new secret..."
    gcloud secrets create firebase-service-account \
        --data-file=firebase-service-account.json \
        --project ${PROJECT_ID}
fi

echo "🚢 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY} \
    --set-secrets FIREBASE_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json=firebase-service-account:latest \
    --project ${PROJECT_ID}

echo "✅ Deployment complete!"
echo ""
echo "Your app is live at:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)' --project ${PROJECT_ID}
echo ""
echo "🔒 Firebase Authentication is enabled"
echo "📊 Features protected: Chat, Generate, Upload"
echo "👥 Users must sign in to access the app"
