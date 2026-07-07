# CloudBoard

A premium engineering management platform built with **Vite + React** and a **charcoal & gold** design system. It includes:

- Dashboard with risk alerts and AI‑driven suggestions
- Kanban board with drag‑and‑drop and task details modal
- Analytics view powered by Recharts
- Notification flow simulation (App → RabbitMQ → Worker → Slack/Email/In‑App)
- RBAC settings panel with role‑based feature gating
- Real or mock Gemini AI integration for task estimation & duplicate detection

## Development

```bash
npm install          # install dependencies
npm run dev          # start dev server (http://127.0.0.1:5173)
```

The UI follows a dark‑mode charcoal theme with premium gold accents – no glassmorphism or neon.

## Production Build & Deployment

### 1. Build the static assets
```bash
npm run build        # creates a production‑optimised bundle in ./dist
```

### 2. Docker image
A multi‑stage Dockerfile is provided. Build and run the image:
```bash
# Build
docker build -t cloudboard:latest .

# Run
docker run -p 8080:80 cloudboard:latest
```
Visit `http://localhost:8080` – the app is served via **nginx** with SPA fallback.

### 3. Environment variables
For a real Gemini integration, expose the API key at runtime:
```bash
docker run -p 8080:80 \
  -e VITE_GEMINI_API_KEY=YOUR_GEMINI_KEY \
  cloudboard:latest
```
If the variable is omitted, the app falls back to the local mock heuristics (useful for CI).

### 4. CI/CD (GitHub Actions)
The workflow `.github/workflows/ci.yml` automatically:
1. Lints the code
2. Runs unit tests
3. Builds the production bundle
4. Builds and pushes a Docker image to Docker Hub (requires `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets).

### 5. Deployment options
- **Docker Hub** – push the image and pull it on any host.
- **Render / Fly.io / Railway** – point the service to the Docker image.
- **Kubernetes** – a minimal Helm chart can be added if needed.

---

## Production Checklist
- [ ] Verify environment variable `VITE_GEMINI_API_KEY` is set in the container.
- [ ] Run `docker run` and confirm the UI loads without console errors.
- [ ] Test the sidebar toggle on mobile viewports.
- [ ] Ensure the Nginx config serves `index.html` for unknown routes.
- [ ] Check that the CI workflow passes and the image is pushed.

---

### License
MIT © 2026 Sara
