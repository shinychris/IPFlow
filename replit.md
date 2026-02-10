# 知识产权助手 (IP Application Kit)

## Overview

A full-stack web application for preparing Chinese intellectual property registration materials, supporting three business types: software copyright (软著申请), patent (专利申请), and trademark (商标申请). Each type has its own wizard workflow with automatic document generation, compliance validation, and export functionality.

**Core Purpose:** Streamline IP application processes by automating document formatting, compliance checking, and material organization according to Chinese registration requirements.

**Business Types:**
- **Software Copyright (软著):** 5-step wizard - project setup, software info, code processing (60 pages), operation manual, export
- **Patent (专利):** 5-step wizard - project setup, patent info, claims, description, export  
- **Trademark (商标):** 4-step wizard - project setup, trademark info, Nice classification, export

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

### Object Storage
- **Replit Object Storage:** Google Cloud Storage-backed file storage
- **Environment Variables:**
  - `DEFAULT_OBJECT_STORAGE_BUCKET_ID`: Storage bucket identifier
  - `PRIVATE_OBJECT_DIR`: Directory for private file uploads (/.private)
- **File Upload:** Server-side buffering via multer, uploaded to PRIVATE_OBJECT_DIR
- **File Download:** Project-scoped API requiring both project UUID and asset UUID
- **Security Note:** This is a single-user document preparation tool without authentication. Files are protected by UUID-based access control (knowledge of both project ID and asset ID required). Full multi-tenant authentication can be added as future enhancement if needed.

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