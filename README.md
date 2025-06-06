# Heart Project (AI placeholder)

## Introduction
Heart is a fitness application designed to help users manage their workout routines, track exercises, and maintain their fitness journey. The application provides features for user account management, workout planning, and exercise tracking.

## Project Structure

### API (`/api`)
The API component handles the backend functionality of the application:
- `api/api/` - Core API functionality
  - `accounts.py` - User account management
  - `app.py` - Main application entry point
  - `errors.py` - Error handling
  - `feedback.py` - User feedback functionality
  - `models.py` - Data models
  - `templates.py` - Template handling
  - `workouts.py` - Workout management
- `api/authorizer/` - Authentication and authorization
- `api/background/` - Background processing tasks
- `api/template.yaml` - AWS CloudFormation template for API deployment

### Exercises (`/exercises`)
This component manages exercise-related functionality:
- `assets.py` - Exercise asset management
- `assets/` - Directory containing exercise images and animations (GIFs)
- `common.py` - Common utilities for exercise handling
- `exercises.py` - Core exercise functionality
- `templates.json` and `templates.py` - Exercise templates

### Media (`/media`)
Handles media processing and storage:
- `config/` - Configuration files for media handling
- `process/` - Media processing functionality
- `template.yaml` - AWS CloudFormation template for media service deployment

### Migrations (`/migrations`)
Database migration scripts and data:
- `0001_init.sql` - Initial database schema
- Various CSV files for data import/export
- `import.py` - Script for importing data

### Libraries (`/libraries`)
Shared libraries and dependencies for the project.

### Scripts (`/scripts`)
Utility scripts for deployment and maintenance.

## Technology Stack
- **Backend**: Python 3.13
- **Cloud Infrastructure**: AWS
  - AWS Lambda for serverless functions
  - API Gateway for REST API
  - DynamoDB for data storage
  - S3 for media storage
- **Authentication**: Firebase (based on firebase.json files)
- **Deployment**: AWS SAM (Serverless Application Model)

## Development Guidelines
1. Follow the existing code structure and patterns
2. Use Python 3.13 for all development
3. Test thoroughly before deployment
4. Update documentation when making significant changes
5. Follow AWS best practices for serverless applications

## Deployment
The application is deployed using AWS SAM (Serverless Application Model):

1. Make sure you have the AWS SAM CLI installed
2. Configure AWS credentials
3. Use the deployment scripts in the `/scripts` directory:
   ```
   ./scripts/deploy.sh
   ```

## Getting Started
1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up AWS credentials
4. For local development, you can use AWS SAM local:
   ```
   sam local start-api
   ```
5. To deploy to AWS, use the deployment scripts

