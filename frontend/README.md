# MIOS Frontend

React + TypeScript + Vite frontend for the Manufacturing Intelligence Operating System.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **React Router** - Navigation
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`. It proxies API requests to the backend at `http://localhost:8000`.

### Build

```bash
npm run build
```

Production build will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API clients and types
│   │   ├── client.ts     # Axios instance with interceptors
│   │   ├── customerApi.ts
│   │   ├── orderApi.ts
│   │   └── conversationApi.ts
│   ├── components/       # Reusable UI components
│   │   └── ui/
│   │       └── Button.tsx
│   ├── features/         # Feature-specific components
│   │   ├── orders/
│   │   │   ├── OrdersPage.tsx
│   │   │   └── OrdersTable.tsx
│   │   ├── conversation/
│   │   │   └── ConversationPanel.tsx
│   │   └── ...
│   ├── hooks/            # Custom React hooks
│   │   └── useOrders.ts
│   ├── layouts/          # Page layouts
│   │   └── DashboardLayout.tsx
│   ├── lib/              # Utility libraries
│   │   ├── utils.ts      # CN utility
│   │   └── formatters.ts # Date/currency formatters
│   ├── pages/            # Page components
│   ├── stores/           # Zustand stores
│   │   └── authStore.ts
│   ├── types/            # Shared TypeScript types
│   ├── main.tsx          # App entry point
│   └── index.css         # Global styles
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Features

### Authentication
- JWT-based authentication
- Persistent login state with localStorage
- Automatic token refresh on 401 responses

### Orders Management
- View all orders with filtering by status
- Order detail modal with workflow actions
- Real-time status updates

### Conversational Interface
- Natural language command input
- Suggested commands for common actions
- Chat-style message history

### Dashboard
- Key metrics overview
- Quick access to critical information
- Navigation sidebar with role-based menu

## State Management

Uses Zustand for global state:

```typescript
import { useAuthStore } from '@/stores/authStore';

function MyComponent() {
  const { user, isAuthenticated, logout } = useAuthStore();
}
```

## API Integration

All API calls go through typed API clients:

```typescript
import orderApi from '@/api/orderApi';

const orders = await orderApi.getAll({ status: 'APPROVED' });
```

## Styling

Tailwind CSS with custom component classes:

```tsx
import { Button } from '@/components/ui/Button';

<Button variant="primary" size="lg">
  Click Me
</Button>
```

## Environment Variables

Create a `.env` file:

```env
VITE_API_BASE_URL=/api
```

## Code Quality

```bash
npm run lint
```

## Building for Production

The frontend is designed to work with the backend's static file serving in production. After building:

```bash
npm run build
```

Copy the `dist` folder contents to the backend's static files directory, or configure your web server to serve them.
