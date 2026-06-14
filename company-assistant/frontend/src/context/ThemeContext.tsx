import { createContext, type ReactNode, useContext, useEffect, useState } from "react";

type ThemeContextValue = {
  darkMode: boolean;
  toggleDarkMode: () => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("pca-theme") === "dark");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("pca-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  return <ThemeContext.Provider value={{ darkMode, toggleDarkMode: () => setDarkMode((value) => !value) }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within ThemeProvider");
  return context;
}

