# Distributed Tictactoe
## 1. Architektur

Die verteilte Web-Applikation „Distributed Tictactoe“ ist als moderne Microservice-basierte Anwendung konzipiert, welche vollständig containerisiert in einem Kubernetes-Cluster betrieben wird. Ziel der Architektur ist eine hohe Skalierbarkeit, Ausfallsicherheit sowie die Unterstützung von Echtzeitkommunikation für ein reibungsloses Spielerlebnis.

### 1.1 Aufbau und Architekturelle Entscheidungen

Die gewählte Architektur folgt dem Microservice-Paradigma. Jede fachliche Domäne (z. B. Benutzerverwaltung, Spiellogik, Spielhistorie) ist durch einen eigenständigen Dienst repräsentiert. Diese Dienste kommunizieren über standardisierte HTTP-Schnittstellen sowie WebSockets für Echtzeitanwendungen. Die Entscheidung für Microservices basiert auf den Vorteilen in Bezug auf Skalierbarkeit, unabhängige Entwicklung und Fehlertoleranz [1].

Die Services laufen innerhalb eines Kubernetes-Clusters. Als Service Mesh kommt Istio zum Einsatz, um Aspekte wie Traffic Management, mTLS-Verschlüsselung, Observability und Policy Enforcement zentral und deklarativ zu steuern [2]. Für die lokale Entwicklung wird Minikube verwendet.

Ein Istio Ingress Gateway dient als zentraler Einstiegspunkt in das System. Über definierte `VirtualServices` wird der eingehende Datenverkehr zu den jeweiligen Services weitergeleitet.


### 1.2 Systemkomponenten und Interaktion

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

#### 1.2.1 Frontend
Das Frontend ist als Single Page Application (SPA) mit Vue.js umgesetzt. Es wird als statisches Bundle gebaut und über einen Webserver ausgeliefert, welcher im Kubernetes-Cluster über das Istio Ingress Gateway erreichbar ist. Die Applikation kommuniziert mit den Backenddiensten über REST und WebSockets.

#### 1.2.2 Users-Service
Der Users-Service implementiert die Benutzerverwaltung. Er basiert auf FastAPI und bietet Login via OAuth2.0 (GitHub), Gastzugänge sowie Authentifizierung über HTTP-only Cookies mit JWT. Die Authentifizierung wird gemäß dem OAuth2.0-Standard umgesetzt, wie von [3] beschrieben. Die Nutzerdaten werden in einer eigenen PostgreSQL-Datenbank persistiert.

Da viele andere Dienste (z. B. Game Service) den JWT validieren müssen, wird der Users-Service in mehreren Instanzen betrieben, um eine höhere Verfügbarkeit und Lastverteilung zu ermöglichen.

#### 1.2.3 Game-Service
Der Game Service implementiert die Spiellogik für das Tictactoe-Spiel. Spieler können Spielräume erstellen, beitreten und über WebSockets gegeneinander oder gegen einen Bot spielen. Die unifiziertte Schnittstelle sorgt dafür, dass Frontend die gleiche Komponenten sowohl für Bot, als auch für Multiplayer verwenden kann. Laufende Spiele werden in einem Redis-Cluster gespeichert, um schnellen Zugriff und konsistenten Spielstatus bei mehreren Instanzen zu gewährleisten.

Nach Spielende werden relevante Spieldaten als Nachrichten in Redis Streams veröffentlicht. Redis Streams ermöglichen eine Event-getriebene Kommunikation nach dem Publish-Subscribe-Prinzip, was insbesondere bei verteilten Systemen Vorteile bietet [4].

#### 1.2.4 Game History-Service
Der Game History Service konsumiert Nachrichten aus dem Redis Stream und speichert abgeschlossene Spiele in einer dedizierten PostgreSQL-Datenbank. Darüber hinaus stellt er eine REST-API bereit, über welche vergangene Spiele abgerufen werden können.

Die Entkopplung der Dienste durch den asynchronen Stream-Mechanismus erhöht die Systemrobustheit und entspricht dem Design empfohlener Event-driven Architectures [5].

#### 1.2.5 Redis Cluster
Redis übernimmt mehrere Aufgaben innerhalb des Systems:

- Speicherung des aktuellen Spielzustands
- Bereitstellung von Redis Streams für asynchrone Kommunikation zwischen Game- und History-Service
- Speicherung von Open Games

Die Wahl fiel auf Redis aufgrund seiner hohen Performance und nativen Unterstützung verteilter Datenstrukturen [6]. Dadurch, dass Redis auch eine Message Queue bereitstellt, wurde auf eine zusätzliche Messaging-Lösung verzichtet, da es eine weitere Komplexität in der Architektur mit sich gebracht hätte.

#### 1.2.6 PostgreSQL Cluster (CloudNativePG)
Für die persistente Speicherung von Benutzerdaten sowie der Spielhistorie kommen zwei voneinander getrennte PostgreSQL-Datenbanken zum Einsatz. Diese werden mithilfe von CloudNativePG als Kubernetes-native StatefulSets betrieben.

CloudNativePG bietet folgende Vorteile:

- Automatisches Failover und Replikation: Primär- und Replikasetups werden automatisiert verwaltet, was hohe Verfügbarkeit garantiert.
- Kubernetes-native Verwaltung: Ressourcen wie Cluster, Backup, ScheduledBackup und Replica werden über Kubernetes Custom Resources (CRDs) definiert.
- Einfache Integration in CI/CD: Backups, Upgrades und Rollouts lassen sich deklarativ automatisieren.
- TLS-Verschlüsselung und Benutzer-/Rollenverwaltung sind direkt integrierbar.
- Die Trennung in zwei PostgreSQL-Cluster erlaubt eine Lastverteilung und Performanceoptimierung:
- Der Users-Service interagiert mit einer für schnelle Lesezugriffe optimierten Datenbank.
- Der Game History Service nutzt ein Setup mit hohem Schreibdurchsatz, um viele Spielabschlüsse performant zu speichern.

Diese Architektur folgt dem Prinzip verteilter, fehlertoleranter Speichersysteme, wie sie auch von Tanenbaum beschrieben werden: „Distributed databases must cope with replication, partitioning and fault-tolerance[...]“ [1, Kapitel 7].


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

---

## 2. Umsetzung

Die technische Umsetzung orientiert sich eng an den definierten architektonischen Prinzipien. Die Anwendung wurde vollständig containerisiert und in einem Kubernetes-Cluster bereitgestellt, sowohl für lokale Entwicklung (Minikube) als auch für produktionsnahe Testszenarien. Die Wahl der eingesetzten Technologien erfolgte nach Kriterien wie Modularität, Erweiterbarkeit, Skalierbarkeit und Echtzeitfähigkeit.

### 2.1 Implementierung der Architektur

#### 2.1.1 Backend-Services mit FastAPI
Alle Backend-Microservices wurden in FastAPI umgesetzt, einem modernen Python-Webframework mit automatischer OpenAPI-Generierung und hervorragender Performance. Die Services nutzen Pydantic für Typisierung und Validierung sowie JWT für Authentifizierung. Die getrennte Entwicklung jedes Dienstes ermöglichte eine klare fachliche und technische Abgrenzung.



#### 2.1.2 Websockets für Echtzeit-Spielbetrieb
Die Kommunikation beim Spiel erfolgt über WebSockets, da diese eine permanente bidirektionale Verbindung zwischen Client und Server ermöglichen. Im Gegensatz zu HTTP-Polling oder Long-Polling reduziert WebSocket die Latenz signifikant – ein entscheidender Faktor für eine flüssige Spielerfahrung [1].

#### 2.1.3 Redis für Session-Management und Event-Streaming
Redis wurde aufgrund seiner In-Memory-Natur und Unterstützung von Streams und Hashes eingesetzt. Folgende Aufgaben übernimmt Redis im System:

- Session- und Spielstatusspeicherung: Spielzustände werden als Redis Hashes gespeichert.
- Event-Streaming: Beendete Spiele werden als Event-Objekte in Redis Streams gespeichert, damit der History-Service diese asynchron verarbeiten kann.

Die Nutzung von Redis Streams erlaubt die lose Kopplung zwischen Services und unterstützt resiliente, fehlertolerante Event-getriebene Systeme [2].

#### 2.1.4 GitHub-Login mit OAuth2.0
Die Authentifizierung über GitHub erfolgt via OAuth2.0 Authorization Code Flow. Der Users-Service ruft nach erfolgreicher Authentifizierung die Nutzerdaten über die GitHub API ab und erstellt ein Session-JWT. Dieser Token wird verschlüsselt im Cookie gespeichert.

Die Entscheidung für GitHub-Login wurde getroffen, um eine einfache und für Entwickler vertraute Authentifizierungsmethode anzubieten, mit geringem Verwaltungsaufwand für Passwörter und Account-Sicherheit [3].

#### 2.1.5 Kubernetes und Istio
Alle Services wurden in Kubernetes als Deployments ausgerollt. Stateful Services wie Redis und PostgreSQL (via CloudNativePG) werden als StatefulSets betrieben. Istio wird eingesetzt für:

- mTLS-gesicherte interne Kommunikation
- Traffic Routing (z. B. Canary-Deployments)
- Retry-Strategien und Circuit Breakers
- Service-Monitoring mit Prometheus und Grafana

Das Service Mesh abstrahiert die Netzwerklogik von den Applikationen und erlaubt die Deklaration von Policies in Kubernetes-Manifests. Laut Tanenbaum ist diese Trennung zwischen Kommunikationslogik und Anwendungslogik ein Kernelement verteilter Systeme [4].

#### 2.1.6 CI mit GitHub Actions
Die Continuous Integration Pipeline wurde mit GitHub Actions implementiert. Folgende Schritte sind Teil des Workflows:
- Detectieren von Code-Änderungen
- Bauen der Container-Images
- Pushen der Images zu Docker Hub

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
[2]  Istio Authors, “Istio Documentation,” [Online]. Available: https://istio.io/latest/docs/. [Accessed: 06-Apr-2025].
[3] IETF, “The OAuth 2.0 Authorization Framework,” RFC 6749, Oct. 2012. [Online]. Available: https://tools.ietf.org/html/rfc6749  
[4] Redis Authors, “Redis Streams,” [Online]. Available: https://redis.io/docs/data-types/streams/. [Accessed: 06-Apr-2025].
[5] M. Fowler, “Event-Driven Architecture,” [Online]. Available: https://martinfowler.com/articles/201701-event-driven.html. [Accessed: 06-Apr-2025].
[6] Redis Authors, “Redis – In-Memory Data Structure Store,” [Online]. Available: https://redis.io/. [Accessed: 06-Apr-2025].
