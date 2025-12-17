# 软著申请助手 (Software Copyright Kit)

## Overview

A full-stack web application designed to help individuals and teams prepare Chinese software copyright registration materials within 7 days. The system guides users through a multi-step wizard to collect software information, process source code, generate operation manuals, and export compliant document packages for submission.

**Core Purpose:** Streamline the software copyright application process by automating document formatting, compliance checking, and material organization according to Chinese software copyright registration requirements.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework:** React 18 with TypeScript
- **Routing:** Wouter (lightweight client-side routing)
- **State Management:** TanStack React Query for server state
- **UI Framework:** shadcn/ui components built on Radix UI primitives
- **Styling:** Tailwind CSS with custom design tokens for Chinese enterprise applications
- **Build Tool:** Vite with HMR support

**Design System Rationale:** Follows Ant Design principles optimized for Chinese enterprise applications - form-intensive workflows, data display, and document management. Uses a sidebar navigation pattern with 240px fixed width and content area with max-width 1200px.

### Backend Architecture
- **Runtime:** Node.js with Express
- **Language:** TypeScript (ESM modules)
- **API Pattern:** RESTful JSON API under `/api` prefix
- **Development:** Hot module replacement via Vite middleware

**Key Design Decisions:**
- Single server serves both API and static frontend assets
- Vite dev server integrated for development; static file serving for production
- Custom build script bundles server dependencies to reduce cold start times

### Data Layer
- **ORM:** Drizzle ORM with PostgreSQL dialect
- **Schema Location:** `shared/schema.ts` (shared between client and server)
- **Validation:** Zod schemas generated from Drizzle schemas via `drizzle-zod`
- **Migrations:** Drizzle Kit with push strategy (`db:push`)

**Data Model:** Projects are the central entity, containing software information, code bundles, manual bundles, proof assets, compliance runs, and export packages. Supports individual, enterprise, and institution subject types with various development methods.

### Project Structure
```
├── client/           # React frontend
│   ├── src/
│   │   ├── components/   # UI components (shadcn + custom)
│   │   ├── pages/        # Route pages
│   │   ├── hooks/        # Custom React hooks
│   │   └── lib/          # Utilities and query client
├── server/           # Express backend
│   ├── index.ts      # Server entry point
│   ├── routes.ts     # API route definitions
│   ├── storage.ts    # Data access layer interface
│   └── vite.ts       # Vite dev middleware
├── shared/           # Shared types and schemas
│   └── schema.ts     # Drizzle schema definitions
└── migrations/       # Database migrations
```

### Application Flow
1. **Project Creation:** User creates project with subject type, development method, publication status
2. **Software Info:** Collects software name, version, completion date, rights holder details
3. **Code Processing:** Uploads source code, system extracts first 30 + last 30 pages (60 pages total, 50+ lines each)
4. **Manual Generation:** Template-based operation manual creation with 5 template types (web, mobile, algorithm, script, desktop)
5. **Compliance Check:** Validates materials against registration requirements
6. **Export:** Generates compliant document package (PDF format with proper headers/footers)

## External Dependencies

### Database
- **PostgreSQL:** Primary database via `DATABASE_URL` environment variable
- **Session Storage:** `connect-pg-simple` for Express session persistence

### UI Component Libraries
- **Radix UI:** Full suite of accessible primitives (dialog, dropdown, tabs, etc.)
- **Embla Carousel:** Carousel functionality
- **cmdk:** Command palette component

### Development Tools
- **Replit Plugins:** 
  - `@replit/vite-plugin-runtime-error-modal` for error display
  - `@replit/vite-plugin-cartographer` and `@replit/vite-plugin-dev-banner` for Replit integration

### Build Dependencies
- **esbuild:** Server bundling for production
- **Vite:** Frontend bundling with React plugin

### Fonts
- Google Fonts: DM Sans, Fira Code, Geist Mono, Architects Daughter
- System fonts: PingFang SC, Microsoft YaHei (Chinese typography)