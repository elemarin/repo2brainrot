# Universal App Categories

Every non-trivial application can be analyzed across these 16 categories. Not every app has all of them — score 0 for missing categories and skip them.

## 1. Project Structure
**What:** Folder layout, file organization, naming conventions, monorepo vs single-package.
**Look for:** Directory tree, README, entry points, how files are grouped (by feature vs by type).
**Why it matters:** This is the "map" — understand this first, everything else makes sense.
**Difficulty:** Beginner

## 2. Dependencies
**What:** External libraries, package manager, version constraints, dev vs production deps.
**Look for:** `package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`, lock files.
**Why it matters:** Tells you what problems the devs didn't want to solve themselves.
**Difficulty:** Beginner

## 3. Authentication & Authorization
**What:** Login/register, JWT/session tokens, OAuth, protected routes, role-based access.
**Look for:** Auth middleware, token storage (localStorage, cookies, headers), login/register forms, auth guards.
**Why it matters:** The bouncer at the door — who gets in and what they can do.
**Difficulty:** Intermediate

## 4. Routing
**What:** URL → component/handler mapping, navigation, deep linking, route guards.
**Look for:** Router config, route definitions, navigation hooks, URL params, redirects.
**Why it matters:** The GPS — how the app knows what to show you.
**Difficulty:** Beginner

## 5. State Management
**What:** How app data is stored, shared, and updated across components/pages.
**Look for:** Redux/Vuex/Zustand stores, React context, global state, reducers, actions, middleware.
**Why it matters:** The brain — where all the app's memories live.
**Difficulty:** Intermediate

## 6. Components / UI Architecture
**What:** Component hierarchy, reusable components, layout patterns, design system.
**Look for:** Component tree, container vs presentational, HOCs, hooks, composition patterns.
**Why it matters:** The building blocks — how the UI is assembled from pieces.
**Difficulty:** Intermediate

## 7. API Layer / Data Fetching
**What:** How the frontend talks to the backend, HTTP clients, API patterns.
**Look for:** Fetch/axios/superagent setup, API service files, endpoint definitions, request/response handling.
**Why it matters:** The phone line between frontend and backend.
**Difficulty:** Intermediate

## 8. Styling & Theming
**What:** CSS approach, design tokens, responsive design, dark mode.
**Look for:** CSS files, CSS-in-JS, Tailwind, SCSS, CSS modules, theme config, media queries.
**Why it matters:** The outfit — how the app looks and adapts.
**Difficulty:** Beginner

## 9. Data Models & Types
**What:** Shape of data, TypeScript types, PropTypes, database schemas, API contracts.
**Look for:** Type definitions, interfaces, models, schema files, validation schemas (Zod, Yup).
**Why it matters:** The vocabulary — what "things" exist in this app's world.
**Difficulty:** Intermediate

## 10. Forms & User Input
**What:** Form handling, validation, submission, controlled vs uncontrolled inputs.
**Look for:** Form components, form libraries (Formik, React Hook Form), validation logic, onChange handlers.
**Why it matters:** The conversation — how users talk to the app.
**Difficulty:** Beginner

## 11. CRUD Operations
**What:** Create/Read/Update/Delete patterns, how data flows from UI → API → DB and back.
**Look for:** Create/edit forms, delete confirmations, list views, detail views, API calls for each operation.
**Why it matters:** The four verbs of every app — everything is CRUD under the hood.
**Difficulty:** Beginner

## 12. Error Handling
**What:** How errors are caught, displayed, recovered from, logged.
**Look for:** Try/catch, error boundaries, error display components, toast notifications, error middleware.
**Why it matters:** The safety net — what happens when things go wrong.
**Difficulty:** Intermediate

## 13. Testing
**What:** Test strategy, unit/integration/e2e tests, test utilities, mocking.
**Look for:** Test files, test config (Jest, Vitest, Cypress, Playwright), test utilities, fixtures, mocks.
**Why it matters:** The quality inspector — how devs know it still works.
**Difficulty:** Advanced

## 14. Build & Configuration
**What:** Build tools, bundlers, transpilers, env vars, dev/prod config.
**Look for:** Webpack/Vite/esbuild config, babel config, .env files, CI/CD pipelines, Dockerfiles.
**Why it matters:** The factory — how source code becomes a running app.
**Difficulty:** Advanced

## 15. Security Patterns
**What:** XSS prevention, CSRF tokens, input sanitization, CSP, secure headers, secrets management.
**Look for:** Sanitization functions, helmet/CSP configs, CORS setup, rate limiting, security middleware.
**Why it matters:** The locks on the doors — keeping bad actors out.
**Difficulty:** Advanced

## 16. Performance Patterns
**What:** Caching, lazy loading, code splitting, memoization, pagination, virtualization.
**Look for:** React.memo, useMemo, lazy(), Suspense, pagination logic, CDN usage, service workers.
**Why it matters:** The engine tuning — making the app fast.
**Difficulty:** Advanced

---

## Scoring Guide

| Score | Meaning | Episodes | Example |
|-------|---------|----------|---------|
| 0 | Not present | 0 (skip) | No tests in the repo |
| 1 | Minimal / trivial | 1 short episode | Basic CSS from CDN, no custom styling |
| 2 | Standard implementation | 1-2 episodes | Redux with multiple reducers |
| 3 | Complex / novel / interesting | 2-3 episodes | Custom middleware chain, novel auth pattern |

## Feed Ordering Strategy

For maximum engagement, order episodes like this:
1. **Project Structure** (always first — orientation)
2. **Highest-scored categories** (the interesting stuff)
3. **Alternate** between heavy (state, API, auth) and light (deps, styling) topics
4. **Build & Config** (always last — satisfying "now I see the full picture" closure)
