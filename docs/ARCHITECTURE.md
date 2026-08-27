# Architecture

## 1. Architecture Overview

The Insurance Claims Adjudication System follows a modular monolith
architecture using Clean Architecture and Ports and Adapters principles.

The system provides AI-assisted insurance claim adjudication while
keeping high-impact decisions under human control.

The system currently has two user roles:

- **Adjuster** — reviews and adjudicates assigned claims.
- **Manager** — supervises claims and has broader system access.

The architecture separates API concerns, application workflows,
business logic, and infrastructure implementations.


---

# 2. C4 Architecture

## 2.1 C4 Level 1 — System Context

The System Context diagram shows the main system, its users, and
external dependencies.

It shows how the Adjuster and Manager interact with the Insurance
Claims Adjudication System and how the system communicates with the
external LLM Provider.

**Diagram source:** [`c4-context.mmd`](diagrams/c4-context.mmd)


---

## 2.2 C4 Level 2 — Container

The Container diagram shows the main technical building blocks
of the system and how they communicate.

The current containers include:

- React Web UI
- Django REST Framework Backend API
- Application Layer
- Background Worker
- PostgreSQL
- PostgreSQL with pgvector
- External LLM Provider

The Web UI communicates with the Backend API, while the application
layer coordinates business workflows and communication with the data
stores, background worker, and LLM provider.

**Diagram source:** [`c4-container.mmd`](diagrams/c4-container.mmd)


---

## 2.3 C4 Level 3 — Component

The Component diagram provides a detailed view of the backend
application and its main components.

The current components include:

- API Layer
- Claim Use Cases
- Document Ingestion
- Retrieval Service
- Agent Orchestrator
- Tool Layer
- Approval Workflow
- LLM Port
- Vector Store Port
- Repository Ports

These components separate the main application responsibilities and
provide abstractions between the application logic and infrastructure.

**Diagram source:** [`c4-component.mmd`](diagrams/c4-component.mmd)


---

# 3. Data Flow and Trust Boundaries

The data-flow diagram shows how information moves between the users,
application components, data stores, and the external LLM Provider.

It also identifies the main trust boundaries in the system.

The high-level flow is:

1. The Adjuster or Manager interacts with the React Web UI.
2. The Web UI communicates with the Django REST API.
3. Authentication and authorization are applied by the application.
4. The application retrieves the required claim and policy information.
5. The Retrieval Service retrieves relevant information.
6. The application selects the required context.
7. The selected context is sent to the external LLM Provider.
8. The generated response is returned to the Web UI.

**Diagram source:** [`data-flow.mmd`](diagrams/data-flow.mmd)


## 3.1 Trust Boundaries

### User Trust Boundary

The Adjuster and Manager interact with the system through the
React Web UI.

### Application Trust Boundary

The application controls authentication, authorization, data access,
retrieval, agent orchestration, and tool execution.

### External Provider Trust Boundary

The LLM Provider is outside the application's infrastructure.

The application controls the information sent to the external
provider.


## 3.2 LLM Data Boundary

The LLM Provider does not directly access PostgreSQL or pgvector.

The application retrieves and selects the required context before
sending information to the LLM.

The LLM may receive information such as:

- User question
- Relevant claim context
- Relevant policy content
- Retrieved evidence
- Required tool results

The LLM Provider does not receive direct database credentials or
direct access to the application's database.


---

# 4. Architecture Status

This document currently describes the architecture diagrams completed
at the current stage of the project.

Additional architecture documentation will be added as implementation
progresses.

Planned additions include:

- Agentic workflow sequence diagram
- Entity Relationship diagram
- Layer dependency diagram
- Architecture Decision Records (ADRs)