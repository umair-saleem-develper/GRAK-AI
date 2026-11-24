import os
import sys
import subprocess
from pathlib import Path

# Paths
DOCS_DIR = Path(r"C:\Users\us761\.gemini\antigravity\scratch\OmniAI\docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)
HTML_PATH = DOCS_DIR / "GrakAI_SDA_Diagrams.html"
PDF_PATH = DOCS_DIR / "GrakAI_SDA_Diagrams.pdf"
DOCX_PATH = DOCS_DIR / "GrakAI_SDA_Diagrams.docx"

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Grak AI - SDA Diagrams & Architecture Specification</title>
  <style>
    @page {
      size: A4;
      margin: 18mm 15mm 20mm 15mm;
      @bottom-right {
        content: counter(page);
        font-size: 10pt;
        color: #718096;
      }
    }
    body {
      font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
      color: #1a202c;
      background: #ffffff;
      line-height: 1.55;
      font-size: 11pt;
      margin: 0;
      padding: 0;
    }
    .cover {
      page-break-after: always;
      text-align: center;
      padding-top: 60px;
    }
    .cover-badge {
      display: inline-block;
      background: #7c3aed;
      color: #ffffff;
      padding: 6px 18px;
      border-radius: 20px;
      font-weight: 700;
      font-size: 11pt;
      letter-spacing: 1px;
      text-transform: uppercase;
      margin-bottom: 25px;
    }
    .cover h1 {
      font-size: 32pt;
      color: #0f172a;
      margin: 0 0 12px 0;
      font-weight: 800;
      line-height: 1.2;
    }
    .cover h2 {
      font-size: 16pt;
      color: #64748b;
      margin: 0 0 35px 0;
      font-weight: 500;
    }
    .cover-meta {
      margin-top: 70px;
      border-top: 2px solid #e2e8f0;
      padding-top: 30px;
      display: inline-block;
      text-align: left;
      font-size: 12pt;
      color: #334155;
      line-height: 1.9;
    }
    .cover-meta strong {
      color: #0f172a;
    }
    h2.section-title {
      font-size: 18pt;
      color: #4338ca;
      border-bottom: 2px solid #e0e7ff;
      padding-bottom: 8px;
      margin-top: 35px;
      margin-bottom: 18px;
      page-break-after: avoid;
    }
    h3.sub-title {
      font-size: 13pt;
      color: #1e293b;
      margin-top: 20px;
      margin-bottom: 8px;
      page-break-after: avoid;
    }
    p, li {
      color: #334155;
    }
    .card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 16px 20px;
      margin: 15px 0;
    }
    .card-purple {
      background: #faf5ff;
      border: 1px solid #e9d5ff;
    }
    .diagram-container {
      background: #ffffff;
      border: 1.5px solid #cbd5e1;
      border-radius: 12px;
      padding: 20px;
      margin: 20px 0;
      text-align: center;
      box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    svg {
      max-width: 100%;
      height: auto;
    }
    pre {
      background: #0f172a;
      color: #f1f5f9;
      padding: 14px 16px;
      border-radius: 8px;
      font-size: 9.5pt;
      overflow-x: auto;
      font-family: 'Consolas', 'Courier New', monospace;
      line-height: 1.45;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 15px 0;
      font-size: 10pt;
    }
    th, td {
      border: 1px solid #cbd5e1;
      padding: 8px 12px;
      text-align: left;
    }
    th {
      background: #f1f5f9;
      color: #0f172a;
      font-weight: 600;
    }
    .tag {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 8.5pt;
      font-weight: 600;
    }
    .tag-actor { background: #e0e7ff; color: #3730a3; }
    .tag-uc { background: #ecfdf5; color: #065f46; }
    .page-break {
      page-break-after: always;
    }
  </style>
</head>
<body>

  <!-- COVER PAGE -->
  <div class="cover">
    <div class="cover-badge">University SDA Project Specification</div>
    <h1>Grak AI (OmniAI)</h1>
    <h2>Software Design & Architecture (SDA) Diagrams</h2>
    <div style="font-size: 13pt; color: #475569; max-width: 600px; margin: 0 auto;">
      Simplified UML Class Diagram, 4 Subsystem Use Case Diagrams, Copy-Paste Prompts for Draw.io & Word, and Viva Presentation Guide.
    </div>

    <div class="cover-meta">
      <div><strong>Project Name:</strong> Grak AI / OmniAI Intelligent Platform</div>
      <div><strong>Course:</strong> Software Design and Architecture (SDA)</div>
      <div><strong>Document Scope:</strong> UML Class Diagram & Functional Use Cases</div>
      <div><strong>Generated Date:</strong> October 2026</div>
      <div><strong>Primary Architecture:</strong> Client-Server / Service-Oriented Gateway (FastAPI + Next.js)</div>
    </div>
  </div>

  <!-- SECTION 1: SIMPLE UML CLASS DIAGRAM -->
  <div class="page-break">
    <h2 class="section-title">1. Simplified UML Class Diagram</h2>
    <p>
      This UML Class Diagram reflects the <strong>real implemented architecture</strong> of Grak AI in a clean, easy-to-explain structure. It highlights the separation of concerns:
      <strong>Identity & Session Management</strong>, <strong>Chat Persistence</strong>, and <strong>AI Gateway with Provider Failover</strong>.
    </p>

    <div class="diagram-container">
      <svg width="680" height="480" viewBox="0 0 680 480" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="headerGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#4f46e5"/>
            <stop offset="100%" stop-color="#4338ca"/>
          </linearGradient>
          <filter id="shadow" x="-4" y="-4" width="108%" height="108%">
            <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.1"/>
          </filter>
        </defs>

        <!-- CLASS: User -->
        <g transform="translate(40, 30)" filter="url(#shadow)">
          <rect width="180" height="140" rx="6" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <path d="M 0 0 L 180 0 L 180 28 L 0 28 Z" fill="url(#headerGrad)"/>
          <text x="90" y="19" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">User</text>
          <text x="10" y="46" font-size="10" fill="#334155">- id: String</text>
          <text x="10" y="60" font-size="10" fill="#334155">- email: String</text>
          <text x="10" y="74" font-size="10" fill="#334155">- role: String</text>
          <text x="10" y="88" font-size="10" fill="#334155">- tokens: Integer</text>
          <line x1="0" y1="96" x2="180" y2="96" stroke="#e2e8f0" stroke-width="1"/>
          <text x="10" y="112" font-size="10" fill="#047857">+ login()</text>
          <text x="10" y="126" font-size="10" fill="#047857">+ verifyOTP()</text>
        </g>

        <!-- CLASS: Session -->
        <g transform="translate(40, 240)" filter="url(#shadow)">
          <rect width="180" height="120" rx="6" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <path d="M 0 0 L 180 0 L 180 28 L 0 28 Z" fill="url(#headerGrad)"/>
          <text x="90" y="19" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">Session</text>
          <text x="10" y="46" font-size="10" fill="#334155">- id: String</text>
          <text x="10" y="60" font-size="10" fill="#334155">- userId: String</text>
          <text x="10" y="74" font-size="10" fill="#334155">- refreshTokenHash: String</text>
          <text x="10" y="88" font-size="10" fill="#334155">- expiresAt: DateTime</text>
          <line x1="0" y1="96" x2="180" y2="96" stroke="#e2e8f0" stroke-width="1"/>
          <text x="10" y="112" font-size="10" fill="#047857">+ rotateToken()</text>
        </g>

        <!-- CLASS: Conversation -->
        <g transform="translate(260, 30)" filter="url(#shadow)">
          <rect width="180" height="140" rx="6" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <path d="M 0 0 L 180 0 L 180 28 L 0 28 Z" fill="url(#headerGrad)"/>
          <text x="90" y="19" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">Conversation</text>
          <text x="10" y="46" font-size="10" fill="#334155">- id: String</text>
          <text x="10" y="60" font-size="10" fill="#334155">- userId: String</text>
          <text x="10" y="74" font-size="10" fill="#334155">- title: String</text>
          <text x="10" y="88" font-size="10" fill="#334155">- isPinned: Boolean</text>
          <line x1="0" y1="96" x2="180" y2="96" stroke="#e2e8f0" stroke-width="1"/>
          <text x="10" y="112" font-size="10" fill="#047857">+ addMessage()</text>
          <text x="10" y="126" font-size="10" fill="#047857">+ rename() / softDelete()</text>
        </g>

        <!-- CLASS: Message -->
        <g transform="translate(260, 240)" filter="url(#shadow)">
          <rect width="180" height="140" rx="6" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <path d="M 0 0 L 180 0 L 180 28 L 0 28 Z" fill="url(#headerGrad)"/>
          <text x="90" y="19" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">Message</text>
          <text x="10" y="46" font-size="10" fill="#334155">- id: String</text>
          <text x="10" y="60" font-size="10" fill="#334155">- role: String (user/ai)</text>
          <text x="10" y="74" font-size="10" fill="#334155">- content: String</text>
          <text x="10" y="88" font-size="10" fill="#334155">- provider: String</text>
          <text x="10" y="102" font-size="10" fill="#334155">- model: String</text>
          <line x1="0" y1="110" x2="180" y2="110" stroke="#e2e8f0" stroke-width="1"/>
          <text x="10" y="126" font-size="10" fill="#047857">+ parseVisualBlocks()</text>
        </g>

        <!-- CLASS: AIGateway -->
        <g transform="translate(480, 130)" filter="url(#shadow)">
          <rect width="180" height="130" rx="6" fill="#ffffff" stroke="#8b5cf6" stroke-width="1.5"/>
          <path d="M 0 0 L 180 0 L 180 28 L 0 28 Z" fill="#6d28d9"/>
          <text x="90" y="19" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">AIGateway</text>
          <text x="10" y="46" font-size="10" fill="#334155">- providers: List&lt;AIProvider&gt;</text>
          <text x="10" y="60" font-size="10" fill="#334155">- defaultModel: String</text>
          <line x1="0" y1="72" x2="180" y2="72" stroke="#e2e8f0" stroke-width="1"/>
          <text x="10" y="90" font-size="10" fill="#7c3aed">+ stream(messages)</text>
          <text x="10" y="105" font-size="10" fill="#7c3aed">+ chat(messages)</text>
          <text x="10" y="120" font-size="10" fill="#7c3aed">+ fallbackRoute()</text>
        </g>

        <!-- CLASS: BaseAIProvider & Subclasses -->
        <g transform="translate(480, 310)" filter="url(#shadow)">
          <rect width="180" height="85" rx="6" fill="#ffffff" stroke="#8b5cf6" stroke-width="1.5" stroke-dasharray="3,3"/>
          <path d="M 0 0 L 180 0 L 180 28 L 0 28 Z" fill="#475569"/>
          <text x="90" y="19" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">&lt;&lt;interface&gt;&gt; AIProvider</text>
          <text x="10" y="48" font-size="10" fill="#334155">+ stream(messages, model)</text>
          <text x="10" y="64" font-size="10" fill="#334155">+ chat(messages, model)</text>
        </g>

        <!-- Subclasses below -->
        <rect x="475" y="420" width="85" height="30" rx="4" fill="#f1f5f9" stroke="#64748b"/>
        <text x="517" y="439" font-size="9" font-weight="bold" text-anchor="middle" fill="#0f172a">GeminiProvider</text>

        <rect x="580" y="420" width="85" height="30" rx="4" fill="#f1f5f9" stroke="#64748b"/>
        <text x="622" y="439" font-size="9" font-weight="bold" text-anchor="middle" fill="#0f172a">GroqProvider</text>

        <!-- RELATIONSHIPS / CONNECTORS -->
        <!-- User to Session -->
        <line x1="130" y1="170" x2="130" y2="240" stroke="#475569" stroke-width="1.5"/>
        <text x="138" y="200" font-size="10" fill="#64748b">1</text>
        <text x="138" y="230" font-size="10" fill="#64748b">0..*</text>

        <!-- User to Conversation -->
        <line x1="220" y1="100" x2="260" y2="100" stroke="#475569" stroke-width="1.5"/>
        <text x="225" y="93" font-size="10" fill="#64748b">1</text>
        <text x="245" y="93" font-size="10" fill="#64748b">0..*</text>

        <!-- Conversation to Message (Composition diamond) -->
        <line x1="350" y1="170" x2="350" y2="240" stroke="#475569" stroke-width="1.5"/>
        <polygon points="350,170 345,178 350,186 355,178" fill="#475569"/>
        <text x="358" y="200" font-size="10" fill="#64748b">1</text>
        <text x="358" y="230" font-size="10" fill="#64748b">1..*</text>

        <!-- Message to AIGateway -->
        <line x1="440" y1="310" x2="480" y2="200" stroke="#475569" stroke-width="1.5" stroke-dasharray="4,4"/>
        <text x="446" y="250" font-size="9" fill="#64748b">&lt;&lt;uses&gt;&gt;</text>

        <!-- AIGateway to AIProvider (Aggregation) -->
        <line x1="570" y1="260" x2="570" y2="310" stroke="#475569" stroke-width="1.5"/>
        <polygon points="570,260 565,268 570,276 575,268" fill="#ffffff" stroke="#475569"/>
        <text x="578" y="295" font-size="10" fill="#64748b">1..*</text>

        <!-- AIProvider inheritance arrows -->
        <line x1="517" y1="395" x2="517" y2="420" stroke="#475569" stroke-width="1.5"/>
        <polygon points="517,395 512,403 522,403" fill="#ffffff" stroke="#475569"/>

        <line x1="622" y1="395" x2="622" y2="420" stroke="#475569" stroke-width="1.5"/>
        <polygon points="622,395 617,403 627,403" fill="#ffffff" stroke="#475569"/>
      </svg>
    </div>

    <div class="card card-purple">
      <strong>Viva / Teacher Explanation (Easy Language):</strong>
      <p style="margin: 6px 0 0 0;">
        <em>"Sir, hamara Class Diagram 3 core layers mein divided hai: First layer mein <strong>User</strong> aur <strong>Session</strong> security aur refresh token maintain karte hain. Second layer mein <strong>Conversation</strong> aur <strong>Message</strong> hain, jismein har conversation multiple messages compose karti hai. Third layer mein <strong>AIGateway</strong> pattern hai jo polymorphic <strong>AIProvider</strong> interface ke zariye primary model (Gemini) se fallback model (Groq) par seamless switch karta hai."</em>
      </p>
    </div>

    <h3 class="sub-title">PlantUML Code Prompt (Copy & Paste in Draw.io or PlantText)</h3>
    <pre>@startuml
class User {
  - id: String
  - email: String
  - role: String
  - tokens: Integer
  + login()
  + verifyOTP()
  + logout()
}

class Session {
  - id: String
  - userId: String
  - refreshTokenHash: String
  - expiresAt: DateTime
  + rotateToken()
}

class Conversation {
  - id: String
  - userId: String
  - title: String
  - isPinned: Boolean
  + addMessage()
  + rename()
  + softDelete()
}

class Message {
  - id: String
  - conversationId: String
  - role: String
  - content: String
  - provider: String
  - model: String
  + parseVisualBlocks()
}

class AIGateway {
  - providers: List<AIProvider>
  + stream(messages)
  + chat(messages)
  + fallbackRoute()
}

interface AIProvider {
  + stream(messages, model)
  + chat(messages, model)
}

class GeminiProvider implements AIProvider
class GroqProvider implements AIProvider

User "1" -- "0..*" Session : owns >
User "1" -- "0..*" Conversation : manages >
Conversation "1" *-- "1..*" Message : contains >
Message ..> AIGateway : uses >
AIGateway o-- "1..*" AIProvider : aggregates >
@enduml</pre>
  </div>

  <!-- SECTION 2: USE CASE DIAGRAM 1 (AUTH) -->
  <div class="page-break">
    <h2 class="section-title">2. Use Case Diagram 1: Authentication & Session Subsystem</h2>
    <p>
      Describes how users access the system securely using modern passwordless mechanisms: <strong>Brevo Email OTP</strong>, <strong>Firebase Google OAuth</strong>, and <strong>HttpOnly Cookie Token Rotation</strong>.
    </p>

    <div class="diagram-container">
      <svg width="680" height="380" viewBox="0 0 680 380" xmlns="http://www.w3.org/2000/svg">
        <!-- ACTOR: User -->
        <g transform="translate(40, 150)">
          <circle cx="25" cy="20" r="14" fill="#e0e7ff" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="34" x2="25" y2="70" stroke="#4338ca" stroke-width="2"/>
          <line x1="5" y1="48" x2="45" y2="48" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="70" x2="10" y2="105" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="70" x2="40" y2="105" stroke="#4338ca" stroke-width="2"/>
          <text x="25" y="125" font-size="12" font-weight="bold" fill="#1e1b4b" text-anchor="middle">User</text>
        </g>

        <!-- SYSTEM BOUNDARY -->
        <rect x="140" y="20" width="380" height="340" rx="10" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="6,4"/>
        <text x="330" y="42" font-size="13" font-weight="bold" fill="#334155" text-anchor="middle">Authentication Subsystem</text>

        <!-- USE CASES (OVALS) -->
        <!-- UC1: Request Email OTP -->
        <g transform="translate(190, 60)">
          <ellipse cx="140" cy="25" rx="110" ry="24" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="30" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Request Email OTP</text>
        </g>

        <!-- UC2: Verify OTP & Issue Token -->
        <g transform="translate(190, 125)">
          <ellipse cx="140" cy="25" rx="120" ry="24" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="30" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Verify OTP &amp; Issue Tokens</text>
        </g>

        <!-- UC3: Google OAuth Login -->
        <g transform="translate(190, 190)">
          <ellipse cx="140" cy="25" rx="110" ry="24" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="30" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Sign In with Google</text>
        </g>

        <!-- UC4: Refresh JWT Session -->
        <g transform="translate(190, 255)">
          <ellipse cx="140" cy="25" rx="110" ry="24" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="30" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Proactive Token Refresh</text>
        </g>

        <!-- SECONDARY ACTOR: Brevo Email API -->
        <g transform="translate(570, 70)">
          <rect x="0" y="0" width="85" height="45" rx="6" fill="#e0f2fe" stroke="#0284c7" stroke-width="1.5"/>
          <text x="42" y="20" font-size="10" font-weight="bold" fill="#0369a1" text-anchor="middle">&lt;&lt;Service&gt;&gt;</text>
          <text x="42" y="34" font-size="10" font-weight="bold" fill="#0c4a6e" text-anchor="middle">Brevo API</text>
        </g>

        <!-- SECONDARY ACTOR: Firebase Auth -->
        <g transform="translate(570, 195)">
          <rect x="0" y="0" width="85" height="45" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
          <text x="42" y="20" font-size="10" font-weight="bold" fill="#b45309" text-anchor="middle">&lt;&lt;Service&gt;&gt;</text>
          <text x="42" y="34" font-size="10" font-weight="bold" fill="#78350f" text-anchor="middle">Firebase</text>
        </g>

        <!-- CONNECTORS -->
        <line x1="80" y1="180" x2="200" y2="85" stroke="#475569" stroke-width="1.2"/>
        <line x1="80" y1="185" x2="200" y2="150" stroke="#475569" stroke-width="1.2"/>
        <line x1="80" y1="195" x2="200" y2="215" stroke="#475569" stroke-width="1.2"/>
        <line x1="80" y1="205" x2="200" y2="280" stroke="#475569" stroke-width="1.2"/>

        <line x1="430" y1="85" x2="570" y2="92" stroke="#475569" stroke-width="1.2" stroke-dasharray="3,3"/>
        <line x1="430" y1="215" x2="570" y2="217" stroke="#475569" stroke-width="1.2" stroke-dasharray="3,3"/>
      </svg>
    </div>

    <table>
      <thead>
        <tr>
          <th>Use Case</th>
          <th>Primary Actor</th>
          <th>Precondition</th>
          <th>Postcondition</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Request Email OTP</strong></td>
          <td>User</td>
          <td>Valid email entered</td>
          <td>6-digit OTP stored as SHA-256 in DB; email dispatched via Brevo.</td>
        </tr>
        <tr>
          <td><strong>Verify OTP &amp; Issue Tokens</strong></td>
          <td>User</td>
          <td>OTP entered &lt; 10 min old</td>
          <td>User authenticated; 15-min JWT returned; 7-day HttpOnly cookie set.</td>
        </tr>
        <tr>
          <td><strong>Sign In with Google</strong></td>
          <td>User</td>
          <td>Active Google account</td>
          <td>Firebase ID Token verified on server; user auto-provisioned in DB.</td>
        </tr>
        <tr>
          <td><strong>Proactive Token Refresh</strong></td>
          <td>Browser Client</td>
          <td>JWT expiring in &lt; 60s</td>
          <td>Rotated refresh token saved in DB; new access token issued.</td>
        </tr>
      </tbody>
    </table>

    <h3 class="sub-title">PlantUML Code Prompt</h3>
    <pre>@startuml
left to right direction
actor "User" as user
actor "Brevo Email API" as brevo <<Service>>
actor "Firebase Auth" as firebase <<Service>>

rectangle "Authentication Subsystem" {
  usecase "Request Email OTP" as UC1
  usecase "Verify OTP & Issue Tokens" as UC2
  usecase "Sign In with Google" as UC3
  usecase "Proactive Token Refresh" as UC4
}

user --> UC1
user --> UC2
user --> UC3
user --> UC4

UC1 ..> brevo : <<dispatches email>>
UC3 ..> firebase : <<validates token>>
@enduml</pre>
  </div>

  <!-- SECTION 3: USE CASE DIAGRAM 2 (CHAT STREAMING) -->
  <div class="page-break">
    <h2 class="section-title">3. Use Case Diagram 2: Conversational AI &amp; Streaming Subsystem</h2>
    <p>
      Details how chat messages are received, routed through intent classifiers, and streamed token-by-token with automatic fallback failover.
    </p>

    <div class="diagram-container">
      <svg width="680" height="380" viewBox="0 0 680 380" xmlns="http://www.w3.org/2000/svg">
        <!-- ACTOR: User -->
        <g transform="translate(40, 140)">
          <circle cx="25" cy="20" r="14" fill="#e0e7ff" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="34" x2="25" y2="70" stroke="#4338ca" stroke-width="2"/>
          <line x1="5" y1="48" x2="45" y2="48" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="70" x2="10" y2="105" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="70" x2="40" y2="105" stroke="#4338ca" stroke-width="2"/>
          <text x="25" y="125" font-size="12" font-weight="bold" fill="#1e1b4b" text-anchor="middle">Registered User</text>
        </g>

        <!-- SYSTEM BOUNDARY -->
        <rect x="150" y="20" width="370" height="340" rx="10" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="6,4"/>
        <text x="335" y="42" font-size="13" font-weight="bold" fill="#334155" text-anchor="middle">Chat &amp; Streaming Subsystem</text>

        <!-- OVALS -->
        <g transform="translate(180, 60)">
          <ellipse cx="140" cy="22" rx="110" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Send Chat Message</text>
        </g>

        <g transform="translate(180, 120)">
          <ellipse cx="140" cy="22" rx="110" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Detect User Intent</text>
        </g>

        <g transform="translate(180, 180)">
          <ellipse cx="140" cy="22" rx="115" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Stream AI Response (SSE)</text>
        </g>

        <g transform="translate(180, 240)">
          <ellipse cx="140" cy="22" rx="120" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Failover to Backup Provider</text>
        </g>

        <g transform="translate(180, 300)">
          <ellipse cx="140" cy="22" rx="110" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Manage Chat History</text>
        </g>

        <!-- SECONDARY ACTOR: AI Gateway / Providers -->
        <g transform="translate(560, 175)">
          <rect x="0" y="0" width="100" height="50" rx="6" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
          <text x="50" y="20" font-size="10" font-weight="bold" fill="#6d28d9" text-anchor="middle">&lt;&lt;AI Engine&gt;&gt;</text>
          <text x="50" y="35" font-size="10" font-weight="bold" fill="#4c1d95" text-anchor="middle">Gemini &amp; Groq</text>
        </g>

        <!-- CONNECTORS -->
        <line x1="80" y1="180" x2="200" y2="82" stroke="#475569" stroke-width="1.2"/>
        <line x1="80" y1="190" x2="200" y2="322" stroke="#475569" stroke-width="1.2"/>

        <!-- <<include>> Send Message includes Detect Intent -->
        <line x1="320" y1="104" x2="320" y2="120" stroke="#4338ca" stroke-width="1.2" stroke-dasharray="4,3"/>
        <polygon points="320,120 316,113 324,113" fill="#4338ca"/>
        <text x="365" y="115" font-size="8.5" fill="#4338ca">&lt;&lt;include&gt;&gt;</text>

        <!-- <<include>> Send Message includes Stream Response -->
        <line x1="320" y1="164" x2="320" y2="180" stroke="#4338ca" stroke-width="1.2" stroke-dasharray="4,3"/>
        <polygon points="320,180 316,173 324,173" fill="#4338ca"/>
        <text x="365" y="175" font-size="8.5" fill="#4338ca">&lt;&lt;include&gt;&gt;</text>

        <!-- <<extend>> Failover extends Stream Response -->
        <line x1="320" y1="240" x2="320" y2="224" stroke="#d97706" stroke-width="1.2" stroke-dasharray="4,3"/>
        <polygon points="320,224 316,231 324,231" fill="#d97706"/>
        <text x="365" y="235" font-size="8.5" fill="#d97706">&lt;&lt;extend&gt;&gt;</text>

        <line x1="435" y1="202" x2="560" y2="200" stroke="#475569" stroke-width="1.2" stroke-dasharray="3,3"/>
      </svg>
    </div>

    <div class="card card-purple">
      <strong>Viva / Teacher Explanation:</strong>
      <p style="margin: 6px 0 0 0;">
        <em>"Sir, jab user <strong>Send Chat Message</strong> karta hai, toh do use cases mandatory tor par <strong>&lt;&lt;include&gt;&gt;</strong> hotay hain: <strong>Detect User Intent</strong> (taake text, code ya diagram classify ho sake) aur <strong>Stream AI Response</strong>. Agar primary provider (Gemini 3.1) busy ho ya 429 quota error aaye, toh <strong>Failover to Backup Provider</strong> use case conditional tor par <strong>&lt;&lt;extend&gt;&gt;</strong> hota hai aur Groq se seamless streaming continue hoti hai."</em>
      </p>
    </div>

    <h3 class="sub-title">PlantUML Code Prompt</h3>
    <pre>@startuml
left to right direction
actor "Registered User" as user
actor "Gemini / Groq LLMs" as ai <<Service>>

rectangle "Chat & Streaming Subsystem" {
  usecase "Send Chat Message" as UC1
  usecase "Detect User Intent" as UC2
  usecase "Stream AI Response (SSE)" as UC3
  usecase "Failover to Backup Provider" as UC4
  usecase "Manage Chat History" as UC5
}

user --> UC1
user --> UC5

UC1 ..> UC2 : <<include>>
UC1 ..> UC3 : <<include>>
UC4 ..> UC3 : <<extend>> (on 429 / timeout)

UC3 ..> ai : <<consumes tokens>>
@enduml</pre>
  </div>

  <!-- SECTION 4: USE CASE DIAGRAM 3 (VISUAL & IMAGE) -->
  <div class="page-break">
    <h2 class="section-title">4. Use Case Diagram 3: Visual Explanations &amp; Image Synthesis</h2>
    <p>
      Covers educational diagram lookups (SerpApi / Tavily / Wikipedia), real-time FLUX image generation, and document parsing with Gemini Vision OCR.
    </p>

    <div class="diagram-container">
      <svg width="680" height="380" viewBox="0 0 680 380" xmlns="http://www.w3.org/2000/svg">
        <!-- ACTOR: User -->
        <g transform="translate(40, 140)">
          <circle cx="25" cy="20" r="14" fill="#e0e7ff" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="34" x2="25" y2="70" stroke="#4338ca" stroke-width="2"/>
          <line x1="5" y1="48" x2="45" y2="48" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="70" x2="10" y2="105" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="70" x2="40" y2="105" stroke="#4338ca" stroke-width="2"/>
          <text x="25" y="125" font-size="12" font-weight="bold" fill="#1e1b4b" text-anchor="middle">User</text>
        </g>

        <!-- SYSTEM BOUNDARY -->
        <rect x="150" y="20" width="370" height="340" rx="10" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="6,4"/>
        <text x="335" y="42" font-size="13" font-weight="bold" fill="#334155" text-anchor="middle">Visual &amp; Multimodal Subsystem</text>

        <!-- OVALS -->
        <g transform="translate(180, 60)">
          <ellipse cx="140" cy="22" rx="125" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Request Visual Explanation</text>
        </g>

        <g transform="translate(180, 120)">
          <ellipse cx="140" cy="22" rx="120" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Search Labeled Hero Diagram</text>
        </g>

        <g transform="translate(180, 180)">
          <ellipse cx="140" cy="22" rx="115" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Generate AI Image (FLUX)</text>
        </g>

        <g transform="translate(180, 240)">
          <ellipse cx="140" cy="22" rx="115" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Upload Document / Image</text>
        </g>

        <g transform="translate(180, 300)">
          <ellipse cx="140" cy="22" rx="120" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Transcribe via Gemini OCR</text>
        </g>

        <!-- SECONDARY ACTORS -->
        <g transform="translate(555, 80)">
          <rect x="0" y="0" width="105" height="45" rx="6" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
          <text x="52" y="19" font-size="10" font-weight="bold" fill="#15803d" text-anchor="middle">&lt;&lt;Search Engine&gt;&gt;</text>
          <text x="52" y="33" font-size="10" font-weight="bold" fill="#14532d" text-anchor="middle">SerpApi / Tavily</text>
        </g>

        <g transform="translate(555, 180)">
          <rect x="0" y="0" width="105" height="45" rx="6" fill="#fff7ed" stroke="#ea580c" stroke-width="1.5"/>
          <text x="52" y="19" font-size="10" font-weight="bold" fill="#c2410c" text-anchor="middle">&lt;&lt;Image Synthesis&gt;&gt;</text>
          <text x="52" y="33" font-size="10" font-weight="bold" fill="#7c2d12" text-anchor="middle">NVIDIA / FLUX</text>
        </g>

        <!-- CONNECTORS -->
        <line x1="80" y1="180" x2="195" y2="82" stroke="#475569" stroke-width="1.2"/>
        <line x1="80" y1="190" x2="205" y2="202" stroke="#475569" stroke-width="1.2"/>
        <line x1="80" y1="200" x2="205" y2="262" stroke="#475569" stroke-width="1.2"/>

        <!-- <<include>> Visual Explanation includes Search Labeled Diagram -->
        <line x1="320" y1="104" x2="320" y2="120" stroke="#4338ca" stroke-width="1.2" stroke-dasharray="4,3"/>
        <polygon points="320,120 316,113 324,113" fill="#4338ca"/>
        <text x="365" y="115" font-size="8.5" fill="#4338ca">&lt;&lt;include&gt;&gt;</text>

        <!-- <<include>> Upload Document includes Gemini OCR -->
        <line x1="320" y1="284" x2="320" y2="300" stroke="#4338ca" stroke-width="1.2" stroke-dasharray="4,3"/>
        <polygon points="320,300 316,293 324,293" fill="#4338ca"/>
        <text x="365" y="295" font-size="8.5" fill="#4338ca">&lt;&lt;include&gt;&gt;</text>

        <line x1="440" y1="142" x2="555" y2="105" stroke="#475569" stroke-width="1.2" stroke-dasharray="3,3"/>
        <line x1="435" y1="202" x2="555" y2="202" stroke="#475569" stroke-width="1.2" stroke-dasharray="3,3"/>
      </svg>
    </div>

    <h3 class="sub-title">PlantUML Code Prompt</h3>
    <pre>@startuml
left to right direction
actor "User" as user
actor "SerpApi / Tavily" as search <<Search Engine>>
actor "NVIDIA / Pollinations" as synth <<Image Synthesis>>

rectangle "Visual & Multimodal Subsystem" {
  usecase "Request Visual Explanation" as UC1
  usecase "Search Labeled Hero Diagram" as UC2
  usecase "Generate AI Image (FLUX)" as UC3
  usecase "Upload Document / Image" as UC4
  usecase "Transcribe via Gemini OCR" as UC5
}

user --> UC1
user --> UC3
user --> UC4

UC1 ..> UC2 : <<include>>
UC4 ..> UC5 : <<include>> (if image uploaded)

UC2 ..> search : <<queries image index>>
UC3 ..> synth : <<synthesizes pixels>>
@enduml</pre>
  </div>

  <!-- SECTION 5: USE CASE DIAGRAM 4 (VOICE) -->
  <div class="page-break">
    <h2 class="section-title">5. Use Case Diagram 4: Real-time Voice Chat (Grak Speak)</h2>
    <p>
      Models the interactive low-latency voice assistant pipeline featuring client-side speech recognition, high-speed Groq inference, and Deepgram neural TTS with real-time barge-in interruption.
    </p>

    <div class="diagram-container">
      <svg width="680" height="380" viewBox="0 0 680 380" xmlns="http://www.w3.org/2000/svg">
        <!-- ACTOR: User -->
        <g transform="translate(40, 140)">
          <circle cx="25" cy="20" r="14" fill="#e0e7ff" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="34" x2="25" y2="70" stroke="#4338ca" stroke-width="2"/>
          <line x1="5" y1="48" x2="45" y2="48" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="70" x2="10" y2="105" stroke="#4338ca" stroke-width="2"/>
          <line x1="25" y1="70" x2="40" y2="105" stroke="#4338ca" stroke-width="2"/>
          <text x="25" y="125" font-size="12" font-weight="bold" fill="#1e1b4b" text-anchor="middle">User</text>
        </g>

        <!-- SYSTEM BOUNDARY -->
        <rect x="150" y="20" width="370" height="340" rx="10" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="6,4"/>
        <text x="335" y="42" font-size="13" font-weight="bold" fill="#334155" text-anchor="middle">Grak Speak Voice Subsystem</text>

        <!-- OVALS -->
        <g transform="translate(180, 60)">
          <ellipse cx="140" cy="22" rx="120" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Start Voice Mode Session</text>
        </g>

        <g transform="translate(180, 120)">
          <ellipse cx="140" cy="22" rx="120" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Capture &amp; Transcribe Speech</text>
        </g>

        <g transform="translate(180, 180)">
          <ellipse cx="140" cy="22" rx="125" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Generate Fast LLM Reply</text>
        </g>

        <g transform="translate(180, 240)">
          <ellipse cx="140" cy="22" rx="120" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Synthesize Speech (TTS MP3)</text>
        </g>

        <g transform="translate(180, 300)">
          <ellipse cx="140" cy="22" rx="115" ry="22" fill="#ffffff" stroke="#6366f1" stroke-width="1.5"/>
          <text x="140" y="27" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">Interrupt Playback (Barge-In)</text>
        </g>

        <!-- SECONDARY ACTORS -->
        <g transform="translate(555, 155)">
          <rect x="0" y="0" width="105" height="45" rx="6" fill="#fdf4ff" stroke="#c026d3" stroke-width="1.5"/>
          <text x="52" y="19" font-size="10" font-weight="bold" fill="#a21caf" text-anchor="middle">&lt;&lt;Fast LLM&gt;&gt;</text>
          <text x="52" y="33" font-size="10" font-weight="bold" fill="#701a75" text-anchor="middle">Groq Qwen</text>
        </g>

        <g transform="translate(555, 240)">
          <rect x="0" y="0" width="105" height="45" rx="6" fill="#f0f9ff" stroke="#0284c7" stroke-width="1.5"/>
          <text x="52" y="19" font-size="10" font-weight="bold" fill="#0369a1" text-anchor="middle">&lt;&lt;Voice TTS&gt;&gt;</text>
          <text x="52" y="33" font-size="10" font-weight="bold" fill="#0c4a6e" text-anchor="middle">Deepgram Aura</text>
        </g>

        <!-- CONNECTORS -->
        <line x1="80" y1="180" x2="200" y2="82" stroke="#475569" stroke-width="1.2"/>
        <line x1="80" y1="190" x2="200" y2="142" stroke="#475569" stroke-width="1.2"/>
        <line x1="80" y1="200" x2="205" y2="322" stroke="#475569" stroke-width="1.2"/>

        <!-- <<include>> Session includes Capture Speech -->
        <line x1="320" y1="104" x2="320" y2="120" stroke="#4338ca" stroke-width="1.2" stroke-dasharray="4,3"/>
        <polygon points="320,120 316,113 324,113" fill="#4338ca"/>
        <text x="365" y="115" font-size="8.5" fill="#4338ca">&lt;&lt;include&gt;&gt;</text>

        <!-- <<include>> Capture Speech includes Generate LLM -->
        <line x1="320" y1="164" x2="320" y2="180" stroke="#4338ca" stroke-width="1.2" stroke-dasharray="4,3"/>
        <polygon points="320,180 316,173 324,173" fill="#4338ca"/>
        <text x="365" y="175" font-size="8.5" fill="#4338ca">&lt;&lt;include&gt;&gt;</text>

        <!-- <<include>> Generate LLM includes Synthesize Audio -->
        <line x1="320" y1="224" x2="320" y2="240" stroke="#4338ca" stroke-width="1.2" stroke-dasharray="4,3"/>
        <polygon points="320,240 316,233 324,233" fill="#4338ca"/>
        <text x="365" y="235" font-size="8.5" fill="#4338ca">&lt;&lt;include&gt;&gt;</text>

        <!-- <<extend>> Barge-in extends Synthesize Audio -->
        <line x1="320" y1="300" x2="320" y2="284" stroke="#d97706" stroke-width="1.2" stroke-dasharray="4,3"/>
        <polygon points="320,284 316,291 324,291" fill="#d97706"/>
        <text x="365" y="295" font-size="8.5" fill="#d97706">&lt;&lt;extend&gt;&gt;</text>

        <line x1="445" y1="202" x2="555" y2="178" stroke="#475569" stroke-width="1.2" stroke-dasharray="3,3"/>
        <line x1="440" y1="262" x2="555" y2="262" stroke="#475569" stroke-width="1.2" stroke-dasharray="3,3"/>
      </svg>
    </div>

    <div class="card card-purple">
      <strong>Viva / Teacher Explanation:</strong>
      <p style="margin: 6px 0 0 0;">
        <em>"Sir, Voice Mode mein latency sabse critical hoti hai. Hamne 3-stage pipeline banayi hai: Web Speech API browser mein real-time speech transcribe karti hai; backend par <strong>Groq Qwen 27B</strong> sirf 1.2 seconds mein concise response banata hai; aur <strong>Deepgram Aura Asteria</strong> se natural MP3 voice synthesize hoti hai. Agar user beech mein bol pare, toh <strong>Barge-in Interruption</strong> &lt;&lt;extend&gt;&gt; hota hai jo running task cancel karke user ko dubara sunna shuru kar deta hai."</em>
      </p>
    </div>

    <h3 class="sub-title">PlantUML Code Prompt</h3>
    <pre>@startuml
left to right direction
actor "User" as user
actor "Groq Qwen LLM" as llm <<Fast LLM>>
actor "Deepgram Aura" as tts <<Voice TTS>>

rectangle "Grak Speak Voice Subsystem" {
  usecase "Start Voice Mode Session" as UC1
  usecase "Capture & Transcribe Speech" as UC2
  usecase "Generate Fast LLM Reply" as UC3
  usecase "Synthesize Speech (TTS MP3)" as UC4
  usecase "Interrupt Playback (Barge-In)" as UC5
}

user --> UC1
user --> UC2
user --> UC5

UC1 ..> UC2 : <<include>>
UC2 ..> UC3 : <<include>>
UC3 ..> UC4 : <<include>>
UC5 ..> UC4 : <<extend>> (cancels active audio)

UC3 ..> llm : <<1.2s conversational inference>>
UC4 ..> tts : <<MP3 neural synthesis>>
@enduml</pre>
  </div>

  <!-- SECTION 6: HOW TO DRAW IN WORD / DRAW.IO -->
  <div>
    <h2 class="section-title">6. How to Draw and Insert in MS Word / Draw.io</h2>
    <div class="card">
      <h3 style="margin-top: 0; color: #0f172a;">Method A: Using Draw.io (Recommended for 100% Quality)</h3>
      <ol style="margin-bottom: 0; padding-left: 20px;">
        <li>Open <a href="https://app.diagrams.net" target="_blank">draw.io</a> in your browser.</li>
        <li>Click <strong>Arrange</strong> &gt; <strong>Insert</strong> &gt; <strong>Advanced</strong> &gt; <strong>PlantUML</strong>.</li>
        <li>Copy any of the <strong>PlantUML Code Prompts</strong> from this document and paste them inside the box.</li>
        <li>Click <strong>Insert</strong>. The diagram will render automatically with perfect alignment!</li>
        <li>Go to <strong>File</strong> &gt; <strong>Export as</strong> &gt; <strong>PNG / PDF</strong> or paste it directly into MS Word.</li>
      </ol>
    </div>

    <div class="card">
      <h3 style="margin-top: 0; color: #0f172a;">Method B: Drawing directly in MS Word</h3>
      <ol style="margin-bottom: 0; padding-left: 20px;">
        <li>Go to <strong>Insert &gt; Shapes</strong> in MS Word.</li>
        <li>Draw a <strong>Large Rounded Rectangle</strong> for the <em>System Boundary</em> (set fill to None and border to dashed).</li>
        <li>Draw <strong>Ovals</strong> for each Use Case and double-click to type the name (e.g. <em>Send Chat Message</em>).</li>
        <li>Insert a <strong>Stick Figure</strong> icon or small text box for the <strong>User Actor</strong> on the left, and simple rectangular boxes for External Services on the right.</li>
        <li>Use <strong>Straight Line Connectors</strong> for primary associations, and <strong>Dashed Arrows</strong> labeled <code>&lt;&lt;include&gt;&gt;</code> or <code>&lt;&lt;extend&gt;&gt;</code>.</li>
      </ol>
    </div>
  </div>

</body>
</html>
"""

# Write HTML file
with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated HTML at {HTML_PATH}")

# Render PDF using Puppeteer via Node
node_script = f"""
const puppeteer = require('puppeteer');
(async () => {{
  const browser = await puppeteer.launch({{
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  }});
  const page = await browser.newPage();
  await page.goto('file:///{HTML_PATH.as_posix()}', {{ waitUntil: 'networkidle0' }});
  await page.pdf({{
    path: '{PDF_PATH.as_posix()}',
    format: 'A4',
    printBackground: true,
    margin: {{ top: '15mm', right: '12mm', bottom: '15mm', left: '12mm' }}
  }});
  await browser.close();
  console.log('PDF rendered successfully: {PDF_PATH.as_posix()}');
}})();
"""

res = subprocess.run(["node", "-e", node_script], cwd=r"C:\Users\us761\.gemini\antigravity\scratch\OmniAI\tests", capture_output=True, text=True)
print("Node stdout:", res.stdout)
if res.stderr:
    print("Node stderr:", res.stderr)

# Also generate MS Word .docx file using python-docx
try:
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

    doc = docx.Document()

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("Grak AI (OmniAI)\nSoftware Design & Architecture (SDA) Specification")
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(79, 70, 229)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Simple UML Class Diagram, 4 Functional Use Case Diagrams & Viva Guide\n")
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_heading("1. Simplified UML Class Diagram", level=1)
    doc.add_paragraph(
        "This simplified class diagram captures the essential architecture of Grak AI across three logical tiers:\n"
        "1. Security & Identity: User, Session, and AuthAuditLog.\n"
        "2. Data Persistence: Conversation (1) contains Message (1..*).\n"
        "3. AI Engine: AIGateway aggregates AIProvider with concrete implementations GeminiProvider and GroqProvider."
    )

    p_puml1 = doc.add_paragraph()
    run_puml1 = p_puml1.add_run(
        "PlantUML Code for Draw.io / Word:\n"
        "@startuml\n"
        "class User { - id, email, role, tokens | + login(), verifyOTP() }\n"
        "class Session { - id, userId, refreshTokenHash | + rotateToken() }\n"
        "class Conversation { - id, userId, title, isPinned | + addMessage(), rename() }\n"
        "class Message { - id, conversationId, role, content, provider, model }\n"
        "class AIGateway { - providers | + stream(), chat(), fallbackRoute() }\n"
        "interface AIProvider { + stream(), chat() }\n"
        "class GeminiProvider implements AIProvider\n"
        "class GroqProvider implements AIProvider\n\n"
        "User '1' -- '0..*' Session\n"
        "User '1' -- '0..*' Conversation\n"
        "Conversation '1' *-- '1..*' Message\n"
        "Message ..> AIGateway\n"
        "AIGateway o-- '1..*' AIProvider\n"
        "@enduml"
    )
    run_puml1.font.name = "Consolas"
    run_puml1.font.size = Pt(9.5)

    doc.add_heading("2. Use Case Diagram 1: Authentication & Session Management", level=1)
    doc.add_paragraph(
        "Primary Actor: User\n"
        "Secondary Actors: Brevo Email Service, Firebase Auth\n"
        "Key Use Cases:\n"
        "- Request Email OTP (sends 6-digit code via Brevo REST API)\n"
        "- Verify Email OTP (hashes OTP, creates user session, returns JWT)\n"
        "- Sign in with Google (Firebase popup verification)\n"
        "- Proactive Token Refresh (rotates refresh token in HttpOnly cookie)"
    )

    doc.add_heading("3. Use Case Diagram 2: Conversational AI & Streaming Engine", level=1)
    doc.add_paragraph(
        "Primary Actor: Registered User\n"
        "Secondary Actor: AI Providers (Gemini / Groq)\n"
        "Key Use Cases:\n"
        "- Send Chat Message\n"
        "- Detect User Intent <<include>> (Classifies into Text, Code, Image Gen, Visual Explanation)\n"
        "- Stream AI Response via SSE <<include>>\n"
        "- Failover to Backup Provider <<extend>> (Fires if Gemini returns 429 quota limit or network timeout)\n"
        "- Manage Chat History (Pin, Search, Rename, Soft Delete)"
    )

    doc.add_heading("4. Use Case Diagram 3: Visual Explanations & Image Synthesis", level=1)
    doc.add_paragraph(
        "Primary Actor: User\n"
        "Secondary Actors: SerpApi / Tavily / Wikipedia, NVIDIA FLUX / Pollinations\n"
        "Key Use Cases:\n"
        "- Request Visual Explanation (Searches verified diagrams and renders hero cards)\n"
        "- Search Labeled Hero Diagram <<include>>\n"
        "- Generate AI Image in 'Create Image' Mode (Calls NVIDIA FLUX Klein with Pollinations fallback)\n"
        "- Upload Document / Image (Extracts text via PyPDF2 / docx or Gemini Vision OCR)"
    )

    doc.add_heading("5. Use Case Diagram 4: Real-time Voice Chat (Grak Speak)", level=1)
    doc.add_paragraph(
        "Primary Actor: User\n"
        "Secondary Actors: Groq Qwen Fast LLM, Deepgram Aura TTS\n"
        "Key Use Cases:\n"
        "- Start Voice Mode Session (Establishes full-duplex WebSocket)\n"
        "- Capture & Transcribe Speech (Web Speech API STT in browser)\n"
        "- Generate Fast Conversational Reply (Groq Qwen 27B, ~1.2s latency)\n"
        "- Synthesize Speech Audio (Deepgram Aura Asteria, MP3)\n"
        "- Interrupt Playback via Barge-In <<extend>> (Instantly halts ongoing audio and returns to listening)"
    )

    doc.add_heading("6. Presentation & Viva Guide for University", level=1)
    doc.add_paragraph(
        "Key Speaking Points for Professor/Viva (English & Roman Urdu):\n\n"
        "1. Class Diagram Explanation:\n"
        "   'Sir/Ma'am, our architecture follows separation of concerns: User and Session handle authentication; "
        "   Conversation and Message manage persistence; and AIGateway uses polymorphic AIProviders so if Gemini hits a rate limit, "
        "   Groq instantly takes over without interrupting the user.'\n\n"
        "2. Chat & Failover (Use Case 2):\n"
        "   'Jab user message send karta hai, Intent Router usay classify karta hai. Streaming SSE ke through hoti hai. "
        "   Failover use case extend relationship ke zariye represent hota hai kyunke yeh tabhi trigger hota hai jab primary API fail ho.'\n\n"
        "3. Voice Pipeline (Use Case 4):\n"
        "   'Grak Speak voice mode WebSocket par chal raha hai. Client speech Web Speech API se recognize hoti hai, "
        "   Groq 1.2s mein reply generate karta hai, aur Deepgram natural audio stream karta hai. Agar user beech mein bol pare, "
        "   toh Barge-In task cancel karke user ko priority deta hai.'"
    )

    doc.save(str(DOCX_PATH))
    print(f"Generated DOCX at {DOCX_PATH}")
except Exception as e:
    print(f"Failed to generate DOCX: {e}")
