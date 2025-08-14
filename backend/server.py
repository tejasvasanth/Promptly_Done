from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import tempfile
import shutil
import zipfile
from io import BytesIO
import uuid
from typing import Dict, List, Optional
import google.generativeai as genai
import asyncio
import sqlite3
from datetime import datetime
import hashlib
import jwt
import re
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Configure Gemini AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# JWT Secret Key
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', 'your-email@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-app-password')

# OTP storage (in production, use Redis or database)
otp_storage = {}

app = FastAPI()
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
def init_database():
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_name TEXT NOT NULL,
            initial_prompt TEXT NOT NULL,
            optimized_prompt TEXT NOT NULL,
            generated_files TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Utility functions
def generate_otp():
    return str(random.randint(100000, 999999))

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

# Models
class PromptRequest(BaseModel):
    prompt: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    email: str
    password: str

class SendOTPRequest(BaseModel):
    username: str
    email: str
    password: str

class VerifyOTPRequest(BaseModel):
    username: str
    email: str
    password: str
    otp: str

class ProjectSave(BaseModel):
    project_name: str
    initial_prompt: str
    optimized_prompt: str
    generated_files: List[dict]

class OptimizedPromptResponse(BaseModel):
    original_prompt: str
    optimized_prompt: str
    session_id: str

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_jwt_token(user_id: int, username: str) -> str:
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    return payload

class CodeGenerationRequest(BaseModel):
    optimized_prompt: str
    session_id: str

class GeneratedFile(BaseModel):
    path: str
    content: str

class CodeGenerationResponse(BaseModel):
    files: List[GeneratedFile]
    session_id: str

# Store temporary sessions
sessions: Dict[str, Dict] = {}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Authentication endpoints
@app.post("/api/send-otp")
async def send_otp(request: SendOTPRequest):
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    
    try:
        # Check if username or email already exists
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (request.username, request.email))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Generate and store OTP
        otp = generate_otp()
        otp_key = f"{request.username}_{request.email}"
        otp_storage[otp_key] = {
            'otp': otp,
            'username': request.username,
            'email': request.email,
            'password': request.password,
            'timestamp': datetime.now()
        }
        
        # Send OTP email
        subject = "PromptlyDone - Verification Code"
        body = f"Your verification code is: {otp}\n\nThis code will expire in 10 minutes."
        
        if send_email(request.email, subject, body):
            return {"message": "OTP sent successfully", "otp_sent": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to send OTP")
            
    except Exception as e:
        if "Username or email already exists" in str(e) or "Failed to send OTP" in str(e):
            raise e
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    finally:
        conn.close()

@app.post("/api/verify-otp-register")
async def verify_otp_register(request: VerifyOTPRequest):
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    
    try:
        otp_key = f"{request.username}_{request.email}"
        
        if otp_key not in otp_storage:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
        stored_data = otp_storage[otp_key]
        
        # Check if OTP matches and is not expired (10 minutes)
        time_diff = (datetime.now() - stored_data['timestamp']).total_seconds()
        if time_diff > 600:  # 10 minutes
            del otp_storage[otp_key]
            raise HTTPException(status_code=400, detail="OTP expired")
        
        if stored_data['otp'] != request.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # Verify password matches
        if stored_data['password'] != request.password:
            raise HTTPException(status_code=400, detail="Password mismatch")
        
        # Create new user
        password_hash = hash_password(request.password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (request.username, request.email, password_hash)
        )
        user_id = cursor.lastrowid
        conn.commit()
        
        # Clean up OTP
        del otp_storage[otp_key]
        
        # Create JWT token
        token = create_jwt_token(user_id, request.username)
        
        return {
            "message": "User registered successfully",
            "token": token,
            "user": {
                "id": user_id,
                "username": request.username,
                "email": request.email
            }
        }
    except Exception as e:
        conn.rollback()
        if any(msg in str(e) for msg in ["Invalid or expired OTP", "OTP expired", "Invalid OTP", "Password mismatch"]):
            raise e
        raise HTTPException(status_code=500, detail="Registration failed")
    finally:
        conn.close()

@app.post("/api/register")
async def register_user(user: UserRegister):
    # This endpoint is kept for backward compatibility but should use OTP flow
    raise HTTPException(status_code=400, detail="Please use OTP verification for registration")

@app.get("/api/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}

@app.post("/api/send-otp-login")
async def send_otp_login(request: SendOTPRequest):
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    
    try:
        # Find user by username and email
        cursor.execute(
            "SELECT id, username, email, password_hash FROM users WHERE username = ? AND email = ?",
            (request.username, request.email)
        )
        user_data = cursor.fetchone()
        
        if not user_data or not verify_password(request.password, user_data[3]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate and store OTP
        otp = generate_otp()
        otp_key = f"login_{request.username}_{request.email}"
        otp_storage[otp_key] = {
            'otp': otp,
            'user_id': user_data[0],
            'username': request.username,
            'email': request.email,
            'timestamp': datetime.now()
        }
        
        # Send OTP email
        subject = "PromptlyDone - Login Verification Code"
        body = f"Your login verification code is: {otp}\n\nThis code will expire in 10 minutes."
        
        if send_email(request.email, subject, body):
            return {"message": "OTP sent successfully", "otp_sent": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to send OTP")
            
    except Exception as e:
        if "Invalid credentials" in str(e) or "Failed to send OTP" in str(e):
            raise e
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    finally:
        conn.close()

@app.post("/api/verify-otp-login")
async def verify_otp_login(request: VerifyOTPRequest):
    try:
        otp_key = f"login_{request.username}_{request.email}"
        
        if otp_key not in otp_storage:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
        stored_data = otp_storage[otp_key]
        
        # Check if OTP matches and is not expired (10 minutes)
        time_diff = (datetime.now() - stored_data['timestamp']).total_seconds()
        if time_diff > 600:  # 10 minutes
            del otp_storage[otp_key]
            raise HTTPException(status_code=400, detail="OTP expired")
        
        if stored_data['otp'] != request.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # Clean up OTP
        del otp_storage[otp_key]
        
        # Create JWT token
        token = create_jwt_token(stored_data['user_id'], stored_data['username'])
        
        return {
            "message": "Login successful",
            "token": token,
            "user": {
                "id": stored_data['user_id'],
                "username": stored_data['username'],
                "email": stored_data['email']
            }
        }
    except Exception as e:
        if any(msg in str(e) for msg in ["Invalid or expired OTP", "OTP expired", "Invalid OTP"]):
            raise e
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/login")
async def login_user(user: UserLogin):
    # This endpoint is kept for backward compatibility but should use OTP flow
    raise HTTPException(status_code=400, detail="Please use OTP verification for login")

@app.post("/api/optimize-prompt", response_model=OptimizedPromptResponse)
async def optimize_prompt(request: PromptRequest):
    try:
        session_id = str(uuid.uuid4())
        
        # Initialize Gemini for prompt optimization
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        system_prompt = """You are an expert prompt optimizer for code generation. 
Your job is to take a user's high-level, potentially vague prompt and transform it into a detailed, structured prompt that will result in high-quality code generation.

Your optimized prompt should:
1. Add specific technical details and requirements
2. Specify the programming language if not mentioned (default to Python for backend, React for frontend)
3. Include best practices and patterns
4. Add error handling requirements
5. Specify file structure expectations
6. Include documentation and comments requirements
7. Add testing considerations if applicable

Return ONLY the optimized prompt text, nothing else."""
        
        full_prompt = f"{system_prompt}\n\nOptimize this code generation prompt: {request.prompt}"
        response = model.generate_content(full_prompt)
        
        optimized_prompt = response.text
        
        # Store session data
        sessions[session_id] = {
            "original_prompt": request.prompt,
            "optimized_prompt": optimized_prompt,
            "created_at": asyncio.get_event_loop().time()
        }
        
        return OptimizedPromptResponse(
            original_prompt=request.prompt,
            optimized_prompt=optimized_prompt,
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing prompt: {str(e)}")

@app.post("/api/generate-code", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    try:
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Initialize Gemini for code generation
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        system_prompt = """You are an expert code generator. Generate complete, production-ready code based on the user's prompt.

CRITICAL: Your response must be in JSON format with this exact structure:
{
  "files": [
    {
      "path": "relative/path/to/file.ext",
      "content": "complete file content here"
    }
  ]
}

Requirements:
1. Generate complete, working code with proper structure
2. Include all necessary files (main files, config, dependencies, README)
3. Add comprehensive comments and documentation
4. Include error handling and best practices
5. Use modern patterns and libraries
6. Ensure code is production-ready
7. Return ONLY valid JSON, no other text or explanation

For web projects, include:
- Frontend: React components with modern hooks, TypeScript if applicable
- Backend: FastAPI, Express, or similar with proper routing
- Configuration files (package.json, requirements.txt, etc.)
- Basic styling (CSS/Tailwind)
- README with setup instructions

For other projects, include:
- Main application files
- Configuration files
- Dependencies file
- Documentation
- Basic tests if applicable"""
        
        full_prompt = f"{system_prompt}\n\n{request.optimized_prompt}"
        response = model.generate_content(full_prompt)
        
        generated_response = response.text
        
        # Parse the JSON response
        try:
            generated_data = json.loads(generated_response)
        except json.JSONDecodeError:
            # If not valid JSON, try to extract JSON from the response
            start_idx = generated_response.find('{')
            end_idx = generated_response.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                generated_data = json.loads(generated_response[start_idx:end_idx])
            else:
                raise HTTPException(status_code=500, detail="Generated response is not valid JSON")
        
        # Validate structure
        if "files" not in generated_data or not isinstance(generated_data["files"], list):
            raise HTTPException(status_code=500, detail="Invalid generated code structure")
        
        # Convert to response format
        files = []
        for file_data in generated_data["files"]:
            if "path" in file_data and "content" in file_data:
                files.append(GeneratedFile(
                    path=file_data["path"],
                    content=file_data["content"]
                ))
        
        # Update session with generated files
        sessions[request.session_id]["generated_files"] = files
        
        return CodeGenerationResponse(
            files=files,
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating code: {str(e)}")

@app.get("/api/download-zip/{session_id}")
async def download_zip(session_id: str):
    try:
        if session_id not in sessions or "generated_files" not in sessions[session_id]:
            raise HTTPException(status_code=404, detail="Session or files not found")
        
        files = sessions[session_id]["generated_files"]
        
        # Create zip file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                zip_file.writestr(file.path, file.content)
        
        zip_buffer.seek(0)
        
        # Return as streaming response
        return StreamingResponse(
            BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=generated_code.zip"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating zip: {str(e)}")

@app.get("/api/download-file/{session_id}/{file_index}")
async def download_file(session_id: str, file_index: int):
    try:
        if session_id not in sessions or "generated_files" not in sessions[session_id]:
            raise HTTPException(status_code=404, detail="Session or files not found")
        
        files = sessions[session_id]["generated_files"]
        
        if file_index < 0 or file_index >= len(files):
            raise HTTPException(status_code=404, detail="File not found")
        
        file = files[file_index]
        filename = os.path.basename(file.path) or "generated_file.txt"
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}")
        temp_file.write(file.content.encode('utf-8'))
        temp_file.close()
        
        return FileResponse(
            temp_file.name,
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

# Cleanup old sessions periodically
@app.on_event("startup")
async def startup_event():
    async def cleanup_sessions():
        while True:
            current_time = asyncio.get_event_loop().time()
            expired_sessions = [
                sid for sid, data in sessions.items()
                if current_time - data.get("created_at", 0) > 3600  # 1 hour
            ]
            for sid in expired_sessions:
                del sessions[sid]
            await asyncio.sleep(300)  # Cleanup every 5 minutes
    
    asyncio.create_task(cleanup_sessions())

# Project history endpoints
@app.post("/api/save-project")
async def save_project(project: ProjectSave, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    
    try:
        user_id = current_user['user_id']
        
        # Save the project
        cursor.execute(
            "INSERT INTO projects (user_id, project_name, initial_prompt, optimized_prompt, generated_files) VALUES (?, ?, ?, ?, ?)",
            (user_id, project.project_name, project.initial_prompt, project.optimized_prompt, json.dumps(project.generated_files))
        )
        project_id = cursor.lastrowid
        
        # Keep only the last 5 projects for this user
        cursor.execute(
            "SELECT id FROM projects WHERE user_id = ? ORDER BY created_at DESC LIMIT -1 OFFSET 5",
            (user_id,)
        )
        old_projects = cursor.fetchall()
        
        if old_projects:
            old_project_ids = [str(p[0]) for p in old_projects]
            cursor.execute(
                f"DELETE FROM projects WHERE id IN ({','.join(['?'] * len(old_project_ids))})",
                old_project_ids
            )
        
        conn.commit()
        
        return {
            "message": "Project saved successfully",
            "project_id": project_id
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save project: {str(e)}")
    finally:
        conn.close()

@app.get("/api/projects")
async def get_user_projects(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    
    try:
        user_id = current_user['user_id']
        
        cursor.execute(
            "SELECT id, project_name, initial_prompt, optimized_prompt, generated_files, created_at FROM projects WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
            (user_id,)
        )
        projects = cursor.fetchall()
        
        project_list = []
        for project in projects:
            project_list.append({
                "id": project[0],
                "project_name": project[1],
                "initial_prompt": project[2],
                "optimized_prompt": project[3],
                "generated_files": json.loads(project[4]),
                "created_at": project[5]
            })
        
        return {
            "projects": project_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve projects: {str(e)}")
    finally:
        conn.close()

@app.get("/api/project/{project_id}")
async def get_project(project_id: int, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    
    try:
        user_id = current_user['user_id']
        
        cursor.execute(
            "SELECT id, project_name, initial_prompt, optimized_prompt, generated_files, created_at FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user_id)
        )
        project = cursor.fetchone()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "id": project[0],
            "project_name": project[1],
            "initial_prompt": project[2],
            "optimized_prompt": project[3],
            "generated_files": json.loads(project[4]),
            "created_at": project[5]
        }
    except Exception as e:
        if "Project not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to retrieve project: {str(e)}")
    finally:
        conn.close()

@app.delete("/api/project/{project_id}")
async def delete_project(project_id: int, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    
    try:
        user_id = current_user['user_id']
        
        cursor.execute(
            "DELETE FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user_id)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        conn.commit()
        
        return {
            "message": "Project deleted successfully"
        }
    except Exception as e:
        conn.rollback()
        if "Project not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)