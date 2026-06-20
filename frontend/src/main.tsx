import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import { OrdersPage } from '@/features/orders/OrdersPage';
import { ConversationPanel } from '@/features/conversation/ConversationPanel';
import { useAuthStore } from '@/stores/authStore';
import './index.css';

// Simple login page component
function LoginPage() {
  const { login } = useAuthStore();
  
  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Demo login - in production this would call the auth API
    login('demo-token', {
      id: '1',
      email: 'admin@mios.com',
      name: 'Admin User',
      role: 'administrator',
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
      <div className="max-w-md w-full p-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
        <h1 className="text-2xl font-bold text-center mb-6 text-primary-600">MIOS Login</h1>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input type="email" defaultValue="admin@mios.com" className="input-field" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input type="password" defaultValue="password" className="input-field" />
          </div>
          <button type="submit" className="btn-primary w-full">
            Sign In
          </button>
        </form>
        <p className="mt-4 text-xs text-center text-gray-500">
          Demo credentials - any email/password works
        </p>
      </div>
    </div>
  );
}

// Dashboard home page
function DashboardHome() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Total Orders</h3>
          <p className="text-2xl font-bold mt-2">156</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">In Production</h3>
          <p className="text-2xl font-bold mt-2">23</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Inventory Alerts</h3>
          <p className="text-2xl font-bold mt-2 text-red-600">5</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Pending Approvals</h3>
          <p className="text-2xl font-bold mt-2 text-yellow-600">8</p>
        </div>
      </div>
    </div>
  );
}

// Commands page
function CommandsPage() {
  return (
    <div className="h-[calc(100vh-12rem)]">
      <ConversationPanel />
    </div>
  );
}

// Placeholder pages
const PlaceholderPage = ({ title }: { title: string }) => (
  <div className="flex items-center justify-center h-64">
    <div className="text-center">
      <h2 className="text-xl font-semibold mb-2">{title}</h2>
      <p className="text-gray-500">This module is under development</p>
    </div>
  </div>
);

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function App() {
  const { isAuthenticated } = useAuthStore();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/" replace />} />
        
        <Route path="/" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
          <Route index element={<DashboardHome />} />
          <Route path="orders" element={<OrdersPage />} />
          <Route path="commands" element={<CommandsPage />} />
          <Route path="inventory" element={<PlaceholderPage title="Inventory Management" />} />
          <Route path="production" element={<PlaceholderPage title="Production Control" />} />
          <Route path="customers" element={<PlaceholderPage title="Customer Management" />} />
          <Route path="reports" element={<PlaceholderPage title="Reports & Analytics" />} />
          <Route path="settings" element={<PlaceholderPage title="System Settings" />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
