import { useNavigate } from "react-router-dom";
import { UserPlus, Palette } from "lucide-react";
import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";

export function Settings() {
  const navigate = useNavigate();
  const { role } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <AppShell breadcrumb="Settings">
      <div className="flex max-w-lg flex-col gap-4">
        {role === "ADMIN" && (
          <Card>
            <button
              onClick={() => navigate("/settings/users/new")}
              className="flex w-full items-center gap-3 text-left"
            >
              <UserPlus size={18} className="text-accent" />
              <div>
                <p className="text-sm text-text">Add user</p>
                <p className="text-xs text-text-muted">Create a new team member account</p>
              </div>
            </button>
          </Card>
        )}

        <Card>
          <button onClick={toggleTheme} className="flex w-full items-center gap-3 text-left">
            <Palette size={18} className="text-accent" />
            <div>
              <p className="text-sm text-text">Appearance</p>
              <p className="text-xs text-text-muted">
                Currently using {theme === "dark" ? "dark" : "light"} mode — click to switch
              </p>
            </div>
          </button>
        </Card>
      </div>
    </AppShell>
  );
}