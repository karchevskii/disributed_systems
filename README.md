# Distributed Tictactoe

Die Implementierung des Tic-Tac-Toe-Spiels ist eine verteilte Webapplikation. Es besteht die Möglichkeit, einen Benutzeraccount zu erstellen (OAuth2.0 via GitHub) oder als Gast zu spielen. Zwei Spielmodi stehen zur Verfügung: gegen einen Bot oder im Multiplayer-Modus.

---

## 1. Architektur

Die Applikation basiert auf einer **Microservice-Architektur**, ausgeführt in einem Kubernetes-Cluster. Das System wurde modular und skalierbar konzipiert und besteht aus folgenden Komponenten:

- Frontend (Vue.js)
- Users-Service (FastAPI, PostgreSQL)
- Game-Service (FastAPI, Redis)
- Game History-Service (FastAPI, PostgreSQL)
- Redis (Clustered)
- PostgreSQL (CloudNativePG, zwei Cluster)
- Kubernetes mit Istio (Service Mesh)

### 1.1 Systemkomponenten und Interaktion

```mermaid
graph TD
  subgraph Client
    A[Browser / Frontend Vue.js]
  end

  subgraph "Kubernetes Cluster"
    subgraph "Istio Service Mesh"
      B[Ingress Gateway]
      
      subgraph "Users Service Pod"
        C[Users Service]
        CP[Envoy Proxy Sidecar]
      end
      
      subgraph "Game Service Pod"
        D[Game Service]
        DP[Envoy Proxy Sidecar]
      end
      
      subgraph "Game History Pod"
        E[Game History Service]
        EP[Envoy Proxy Sidecar]
      end

      subgraph "Control Plane"
        IC[Istiod]
      end
      
      subgraph "Observability Stack"
        PR[Prometheus]
        GR[Grafana]
        KI[Kiali]
        JA[Jaeger]
      end
    end
    
    subgraph "Data Layer"
      R[(Redis Cluster)]
      P1[(PostgreSQL - Game History)]
      P2[(PostgreSQL - Users)]
    end
  end
  
  %% Client to Gateway connections
  A -->|HTTP+WebSocket| B
  
  %% Control Plane connections
  IC -.->|Config| CP
  IC -.->|Config| DP
  IC -.->|Config| EP
  IC -.->|Config| B
  
  %% Gateway to services
  B -->|HTTP| CP
  B -->|HTTP+WebSocket| DP
  B -->|HTTP| EP
  
  %% Service to sidecar to service communication
  CP --> C
  DP --> D
  EP --> E
  
  %% Data connections
  D <-->|Cache+State| R
  E -->|Store| P1
  C -->|Store| P2
  D -->|Stream Events| R
  E -->|Stream Consumer| R
  
  %% Observability connections
  CP -.->|Metrics+Traces| PR
  DP -.->|Metrics+Traces| PR
  EP -.->|Metrics+Traces| PR
  B -.->|Metrics+Traces| PR
  PR -->|Data| GR
  PR -->|Data| KI
  CP -.->|Traces| JA
  DP -.->|Traces| JA
  EP -.->|Traces| JA
  B -.->|Traces| JA
  KI -->|Visualization| GR
```

### 1.2 Anforderungen

**Funktionale Anforderungen:**

- Registrierung/Login via GitHub (OAuth2.0)
- Gast-Login
- Matchmaking (Bot/Multiplayer)
- Spielverlauf in Echtzeit
- Speicherung und Abfrage gespielter Spiele

**Nichtfunktionale Anforderungen:**

- Horizontale Skalierung
- Echtzeitfähigkeit (WebSocket)
- Fehlertoleranz (Redis Streams, mehrere Instanzen)
- Trennung von Zuständigkeiten
- Wartbarkeit & Erweiterbarkeit

### 1.3 Architekturelle Entscheidungen

- **FastAPI** wegen schneller Entwicklung und OpenAPI-Unterstützung
- **Redis** zur Zustandsverwaltung und als Event-Stream
- **PostgreSQL** für persistente Datenhaltung (via CloudNativePG)
- **Istio** zur Trennung der Netzwerkkontrolle und Sicherheitsregeln (Service Mesh)
- **Kubernetes** für flexible, portable und deklarative Infrastruktur
- **WebSockets** für flüssiges Spielverhalten in Echtzeit

> "A distributed system is a collection of independent computers that appears to its users as a single coherent system."  
> – Tanenbaum & Van Steen [1]

---

## 2. Umsetzung

### 2.1 Implementierung der Architektur

#### Backend-Services

- **Users-Service**

  - FastAPI + OAuth2.0 (GitHub)
  - JWT in HTTP-only Cookies
  - Validierung durch andere Services via `/users/me` (gibt 401 zurück, wenn Token nicht gültig)
  - Datenhaltung in PostgreSQL
  - Nutzung von SQLAlchemy für Objekt-Relational-Mapping
  - Nutzung von Alembic für Migrationen

- **Game-Service**

  - FastAPI + WebSockets
  - Game-Logik, Spielstart, Spielzug
  - Zustandsdaten in Redis (Hash)
  - Spielende als Event in Redis Stream

- **Game History-Service**
  - Redis Stream Consumer (Consumer Group)
  - Speicherung von Spieldaten in PostgreSQL
  - REST-API zur Abfrage

#### WebSocket & Redis

- WebSocket für Spielkommunikation (`/ws/play`)
- Redis:
  - Spielstatus (Hash)
  - Events (`stream.games.finished`)
  - Skalierbarkeit über Cluster & In-Memory Performance [2]

#### Authentifizierung

- GitHub OAuth2.0 Authorization Code Flow
- Public User Profile via GitHub API
- Abspeicherung von Session-Token im Cookie

#### Kubernetes & Istio

- Minikube für lokale Entwicklung
- Deployments mit Helm
- Istio:
  - TLS, Routing, Circuit Breaking, WebSocket-Handling
  - Prometheus + Grafana Integration

#### CI/CD

- GitHub Actions (Lint, Build, Test, Deploy)
- Docker Hub für Container-Images
- Helm für Umgebungsmanagement
- Kubernetes Secrets für Konfiguration

### 2.2 Herausforderungen und Lösungen

| Herausforderung                              | Lösung                                                |
| -------------------------------------------- | ----------------------------------------------------- |
| Synchronisation Game-Instanzen               | Zentrale Redis-Zustandsverwaltung                     |
| Token-Validierung zwischen Services          | Users-Service `/validate` API                         |
| Fehlertoleranz bei Event-Verarbeitung        | Redis Streams + Consumer Group                        |
| WebSocket-Kompatibilität mit Ingress & Istio | Anpassung der Istio Gateway + VirtualService Settings |

---

## 3. Reflektion

### 3.1 Was würde man anders machen?

- **JWT Self-Validation** via Public Key (JWK) → weniger Service-Abhängigkeiten
- **Früheres Observability Setup** → bessere Debug-Möglichkeiten
- **Frontend API-Abstraktionslayer** → bessere Testbarkeit und Flexibilität
- **GitOps statt CI/CD-only** → ArgoCD/Flux für Infrastrukturpflege

### 3.2 Größte Herausforderungen

| Herausforderung        | Lösung                           |
| ---------------------- | -------------------------------- |
| Verteilte Zustände     | Redis-Zentralisierung            |
| OAuth2-Testing lokal   | Mocks für GitHub-Login           |
| Asynchrone Events      | Redis Streams + Retry            |
| Echtzeit-Kommunikation | WebSockets mit korrektem Routing |

### Fazit

Das Projekt zeigt, wie sich verteilte Systeme in einem modernen Cloud-Native-Stack umsetzen lassen. Die Einbindung von Kubernetes, Istio, Redis und PostgreSQL in einer Microservice-Architektur ermöglichte eine modulare, fehlertolerante und skalierbare Spiellogik. Die Verbindung von Theorie (z. B. nach Tanenbaum [1]) mit praktischer Umsetzung erlaubte es, tiefere Einblicke in die Herausforderungen verteilter Architekturen zu gewinnen.

---

## Literaturverzeichnis

[1] A. S. Tanenbaum and M. van Steen, _Distributed Systems: Principles and Paradigms_, 2nd ed. Upper Saddle River, NJ, USA: Pearson, 2007.  
[2] Redis Authors, “Redis Streams,” [Online]. Available: https://redis.io/docs/data-types/streams/. [Accessed: 06-Apr-2025].  
[3] IETF, “The OAuth 2.0 Authorization Framework,” RFC 6749, Oct. 2012. [Online]. Available: https://tools.ietf.org/html/rfc6749  
[4] A. S. Tanenbaum and M. van Steen, _Distributed Systems_, Chapter 8: Communication in Distributed Systems.
