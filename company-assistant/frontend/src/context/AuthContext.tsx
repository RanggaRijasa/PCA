import { createContext, type ReactNode, useContext, useEffect, useState } from "react";
import { mockUsers } from "../mocks/users";
import { getCurrentUser, loginUser, logoutUser } from "../services/chatApi";
import { useLocalMocks } from "../services/apiClient";
import type { User } from "../types";

type AuthContextValue = {
  currentUser: User | null;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (useLocalMocks) {
      setCurrentUser(mockUsers[3]);
      setIsLoading(false);
      return;
    }
    getCurrentUser()
      .then(setCurrentUser)
      .catch(() => setCurrentUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    setError(null);
    setIsLoading(true);
    try {
      setCurrentUser(await loginUser(username, password));
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Login failed.";
      setError(message);
      throw caught;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setError(null);
    if (!useLocalMocks) await logoutUser();
    setCurrentUser(null);
  };

  return <AuthContext.Provider value={{ currentUser, isLoading, error, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}

export function useAuthenticatedUser(): User {
  const { currentUser } = useAuth();
  if (!currentUser) throw new Error("Authenticated user context is unavailable");
  return currentUser;
}
