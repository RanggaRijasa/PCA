import type { User } from "../types";

export const mockUsers: User[] = [
  { id: "user_viewer", name: "Lina Hartono", email: "viewer@company.local", role: "viewer", department: "General", status: "active" },
  { id: "user_staff", name: "Budi Santoso", email: "staff@company.local", role: "staff", department: "Finance", status: "active" },
  { id: "user_manager", name: "Andrew Davis", email: "manager@company.local", role: "manager", department: "HR", status: "active" },
  { id: "user_admin", name: "Maya Putri", email: "admin@company.local", role: "admin", department: "Operations", status: "active" },
];
