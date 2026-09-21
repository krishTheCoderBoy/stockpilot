import { useQuery } from "@tanstack/react-query";
import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Skeleton } from "../../components/ui/Skeleton";
import { api } from "../../lib/api";

interface Me {
  id: string;
  username: string;
  email: string;
  mobile_no: string | null;
  address: string | null;
  full_name: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
}

export function Profile() {
  const { data: me, isLoading } = useQuery<Me>({
    queryKey: ["me"],
    queryFn: async () => (await api.get("/users/me")).data,
  });

  if (isLoading) {
    return (
      <AppShell breadcrumb="Profile">
        <Skeleton className="h-64 w-full max-w-lg" />
      </AppShell>
    );
  }

  return (
    <AppShell breadcrumb="Profile">
      <Card className="max-w-lg">
        <div className="mb-6 flex items-center gap-4">
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-accent/10 text-lg font-medium text-accent">
            {me?.full_name?.slice(0, 2).toUpperCase()}
          </span>
          <div>
            <h1 className="text-lg text-text">{me?.full_name}</h1>
            <Badge tone="accent">{me?.role}</Badge>
          </div>
        </div>

        <div className="flex flex-col gap-3 text-sm">
          <div className="flex justify-between border-b border-border pb-2">
            <span className="text-text-muted">Username</span>
            <span className="font-mono text-text">{me?.username}</span>
          </div>
          <div className="flex justify-between border-b border-border pb-2">
            <span className="text-text-muted">Email</span>
            <span className="text-text">{me?.email}</span>
          </div>
          <div className="flex justify-between border-b border-border pb-2">
            <span className="text-text-muted">Mobile</span>
            <span className="font-mono text-text">{me?.mobile_no ?? "—"}</span>
          </div>
          <div className="flex justify-between border-b border-border pb-2">
            <span className="text-text-muted">Address</span>
            <span className="text-text">{me?.address ?? "—"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Status</span>
            <Badge tone={me?.is_active ? "flow" : "neutral"}>{me?.is_active ? "Active" : "Inactive"}</Badge>
          </div>
        </div>
      </Card>
    </AppShell>
  );
}