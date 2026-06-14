import { BrowserRouter } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { LoadingState } from "./components/common/States";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ChatProvider } from "./context/ChatContext";
import { ThemeProvider } from "./context/ThemeContext";
import { ToastProvider } from "./context/ToastContext";
import { LoginPage } from "./pages/LoginPage";
import { AppRoutes } from "./routes";

function AuthenticatedApplication() {
  const { currentUser, isLoading } = useAuth();
  if (isLoading) return <div className="flex min-h-screen items-center justify-center bg-slate-100 dark:bg-slate-950"><LoadingState label="Checking local session..." /></div>;
  if (!currentUser) return <LoginPage />;
  return <ToastProvider><ChatProvider><AppShell><AppRoutes /></AppShell></ChatProvider></ToastProvider>;
}

export default function App() {
  return <ThemeProvider><BrowserRouter><AuthProvider><AuthenticatedApplication /></AuthProvider></BrowserRouter></ThemeProvider>;
}
