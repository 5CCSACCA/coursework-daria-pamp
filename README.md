# 5CCSACCA Coursework: ArtI - AI Art Interpreter

Repository URL: [https://github.com/5CCSACCA/coursework-daria-pamp]

## 1. Project Purpose (System Overview)

**ArtI** is a Software as a Service (SaaS) application. The primary goal of this project is to bring art to life by providing users with creative and contextual interpretations of visual art. The system functions by allowing a user to upload an image (such as a painting, sculpture, or photograph). This input triggers a two-part microservice process:

1.  Vision Analysis Service (YOLO): This service uses the *YOLOv8n model* from Ultralytics to perform object detection. It identifies the key components, subjects, and stylistic elements within the image ("person," "guitar," "sky," "cubism" etc).
2.  Text Generation Service (BitNet): The data from the YOLO service is then passed to the *BitNet LLM*. This model generates a creative textual response, such as a poetic description, an emotional interpretation, or a "monologue" from the artwork's perspective.

## 2. Project Directory Structure

The project is architected using a microservice model to ensure scalability and separation of concerns. Each component will be an independent Docker container, orchestrated by Docker Compose.

├── README.md            # This documentation file
├── docker-compose.yml   # The main orchestration file for all services
│
├── gateway-api/         # 1. FastAPI Gateway (The user-facing API)
│   ├── Dockerfile       # Container definition for the gateway
│   └── app/
│       └── main.py      # FastAPI code (endpoints, logic)
│
├── yolo-service/        # 2. YOLOv8n Microservice
│   ├── Dockerfile       # Container definition for the vision model
│   └── app/
│       └── main.py      # Code to load YOLO and perform detection
│
└── bitnet-service/      # 3. BitNet LLM Microservice
    ├── Dockerfile       # Container definition for the language model
    └── app/
       └── main.py      # Code to load BitNet and generate text


## 3. How to Run Locally (Docker)

The entire system is designed for simple, one-command local deployment using Docker and Docker Compose.

Prerequisites:
* Docker Desktop
* Git (for cloning)

Local Deployment Instructions:
bash
1. Clone this repository
git clone [https://github.com/5CCSACCA/coursework-daria-pamp.git]
cd coursework-daria-pamp

2. Build and run all services
This command reads the docker-compose.yml file and starts the entire system
docker-compose up --build

Once running, the FastAPI gateway and its documentation will be accessible at [http://localhost:8000/docs].

## 4. Deployment Specifications

As per the coursework requirements, the entire system (including all models) is designed to perform inference efficiently on hardware limited to:
CPUs: 4 Cores
RAM: 16GB

## 5. Future Implementation Ideas (Roadmap)

This README outlines the core architecture. Future development will proceed according to the phases detailed in the coursework brief, including:

Database Integration: Adding Firebase Firestore to store user information and the history of generated art interpretations.
File Storage: Using Firebase Storage to handle all user-uploaded images.
Authentication: Implementing Firebase Auth for secure user login and registration.
Asynchronous Processing: Integrating RabbitMQ as a message queue between the yolo-service and bitnet-service to provide non-blocking, instant API responses.
Model Versioning: Using MLFlow to track model experiments and manage model versions.
CI/CD Pipeline: Setting up GitHub Actions for automated testing and deployment.
Monitoring & Security: Implementing basic monitoring and securing all API endpoints.
