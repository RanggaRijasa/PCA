import { Navigate, Route, Routes } from "react-router-dom";
import { EmptyState } from "./components/common/States";
import { useAuthenticatedUser } from "./context/AuthContext";
import { ChatPage } from "./pages/ChatPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SourcesPage } from "./pages/SourcesPage";
import { AuditLogsPage } from "./pages/admin/AuditLogsPage";
import { EvaluationPage } from "./pages/admin/EvaluationPage";
import { IngestionPage } from "./pages/admin/IngestionPage";
import { SettingsPage } from "./pages/admin/SettingsPage";
import { UsersRolesPage } from "./pages/admin/UsersRolesPage";

function AdminRoute({ children }: { children: React.ReactNode }) {
  const currentUser = useAuthenticatedUser();
  if (currentUser.role !== "admin") return <div className="p-7"><EmptyState title="Admin access required" description="Your authenticated account does not have administrator access." /></div>;
  return children;
}

export function AppRoutes() {
  return <Routes><Route path="/" element={<Navigate to="/chat" replace />} /><Route path="/chat" element={<ChatPage />} /><Route path="/sources" element={<SourcesPage />} /><Route path="/documents" element={<DocumentsPage />} /><Route path="/reports" element={<ReportsPage />} /><Route path="/admin/ingestion" element={<AdminRoute><IngestionPage /></AdminRoute>} /><Route path="/admin/users" element={<AdminRoute><UsersRolesPage /></AdminRoute>} /><Route path="/admin/audit-logs" element={<AdminRoute><AuditLogsPage /></AdminRoute>} /><Route path="/admin/evaluation" element={<AdminRoute><EvaluationPage /></AdminRoute>} /><Route path="/admin/settings" element={<AdminRoute><SettingsPage /></AdminRoute>} /><Route path="*" element={<Navigate to="/chat" replace />} /></Routes>;
}
