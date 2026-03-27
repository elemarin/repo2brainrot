# Repo Analysis Procedure

Step-by-step process for analyzing a repository before generating brainrot scripts.

## Step 1: Identify the Stack

Read these files first (in order):
1. `README.md` — what does this app DO?
2. `package.json` / `requirements.txt` / `Cargo.toml` / `go.mod` — what's the tech stack?
3. Entry point (`src/index.js`, `main.py`, `cmd/main.go`, etc.) — where does it start?
4. Config files (webpack, vite, tsconfig, .env.example) — how is it built?

From this, determine:
- **Language**: JavaScript, TypeScript, Python, Go, Rust, etc.
- **Framework**: React, Vue, Angular, Django, Express, FastAPI, etc.
- **Key libraries**: State management, routing, HTTP client, ORM, etc.
- **App type**: SPA, SSR, API, CLI, library, monorepo

## Step 2: Map the Architecture

Draw the component/module map:
1. List all top-level directories and their purpose
2. Identify the main "actors" (components, services, models, controllers)
3. Trace the primary user journey end-to-end (e.g., "user opens app → sees feed → clicks article → reads it")
4. Map data flow: UI → Action → API → Response → State → UI

## Step 3: Score Each Category

Go through all 16 categories from `categories.md` and for each:

1. **Search** for relevant files using pattern matching:
   - Auth: `*auth*`, `*login*`, `*register*`, `*token*`, `*session*`
   - Routing: `*route*`, `*router*`, `*navigation*`, `*page*`
   - State: `*store*`, `*reducer*`, `*action*`, `*state*`, `*context*`
   - Components: `*component*`, `src/components/`, `src/views/`
   - API: `*api*`, `*agent*`, `*service*`, `*client*`, `*fetch*`
   - Styling: `*.css`, `*.scss`, `*.styled.*`, `*theme*`, `*tailwind*`
   - Types: `*.d.ts`, `*types*`, `*models*`, `*schema*`, `*interface*`
   - Forms: `*form*`, `*input*`, `*field*`, `*validation*`
   - CRUD: `*create*`, `*edit*`, `*delete*`, `*update*`, `*list*`
   - Errors: `*error*`, `*exception*`, `*catch*`, `*boundary*`
   - Tests: `*.test.*`, `*.spec.*`, `*__tests__*`, `*cypress*`, `*playwright*`
   - Build: `webpack*`, `vite*`, `babel*`, `tsconfig*`, `Dockerfile*`, `.github/workflows/*`
   - Security: `*sanitize*`, `*csrf*`, `*cors*`, `*helmet*`, `*rate-limit*`
   - Performance: `*cache*`, `*lazy*`, `*memo*`, `*virtual*`, `*pagina*`

2. **Read** the key files for each category
3. **Score** 0-3 based on complexity and interestingness
4. **Extract** the specific patterns, libraries, and approaches used
5. **Note** connections to other categories (e.g., auth middleware connects to routing)

## Step 4: Build the Analysis JSON

Create `analysis.json` with this structure:

```json
{
  "repo_name": "react-redux-realworld-example-app",
  "repo_path": "repos/react-redux-realworld-example-app",
  "app_description": "A Medium.com clone (Conduit) built with React + Redux",
  "tech_stack": {
    "language": "JavaScript",
    "framework": "React 16 + Redux 3",
    "key_libraries": ["react-router", "superagent", "marked"],
    "build_tool": "create-react-app (webpack + babel)"
  },
  "categories": [
    {
      "id": "project-structure",
      "name": "Project Structure",
      "score": 2,
      "difficulty": "beginner",
      "summary": "Flat component structure with separate reducers directory...",
      "key_files": ["src/components/App.js", "src/reducer.js"],
      "patterns": ["feature-by-type organization"],
      "connections": ["components", "state-management"],
      "episode_count": 1
    }
  ],
  "total_episodes": 12,
  "estimated_duration_minutes": 8
}
```

## Step 5: Plan Episode Order

The feed order should maximize engagement:

1. **Episode 1:** Always Project Structure — "Here's the map"
2. **Episodes 2-3:** The most interesting categories (score 3) — hook them early
3. **Middle episodes:** Alternate between:
   - Heavy/complex (state, API, auth) — requires focus
   - Light/quick (deps, styling, types) — breather episodes
4. **Last episodes:** Build/Config and Testing — "the full picture" satisfaction

Within each category, if it has multiple episodes:
- Episode A: "What is it?" (overview + hook)
- Episode B: "How does it actually work?" (deep dive into code)
- Episode C: "The clever part" (interesting pattern or gotcha)

## Tips for High-Quality Analysis

- **Read files, don't guess.** Open the actual source code for every category.
- **Follow imports.** The import graph tells you how everything connects.
- **Check middleware.** Middleware is where the magic happens (auth tokens, logging, error handling).
- **Look at the entry point.** `index.js` or `App.js` usually reveals the whole architecture at a glance.
- **Count things.** "8 reducers", "36 action types", "9 routes" — specific numbers make great hooks.
- **Find the weird parts.** Unusual patterns, clever hacks, or surprising decisions make the best content.
