
import * as React from "react";
import { Activity, Users, Footprints } from "lucide-react";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { StatCard } from "@/components/dashboard/StatCard";
import { SystemHealthCard } from "@/components/dashboard/SystemHealthCard";
import { LiveFeed } from "@/components/camera/LiveFeed";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePatients } from "@/hooks/usePatients";
import { useWebSocket } from "@/hooks/useWebSocket";
import * as alertService from "@/services/alertService";
import * as cameraService from "@/services/cameraService";
import type { CameraStatus } from "@/services/cameraService";

export default function Dashboard() {
  const { patients } = usePatients();
  const { lastMessage, isConnected } = useWebSocket();
  const [status, setStatus] = React.useState<CameraStatus | null>(null);

  React.useEffect(() => {
    const loadData = async () => {
      const [alertList, cameraStatus] = await Promise.all([
        alertService.listAlerts({ status: "open" }),
        cameraService.getCameraStatus(),
      ]);
      
      setStatus(cameraStatus);
    };
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <DashboardLayout title="Dashboard">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Patients"
          value={patients.length}
          icon={Users}
          delay={0}
        />
        <StatCard
          label="Current Activity"
          value={lastMessage?.activity_label ?? "—"}
          icon={Footprints}
          tone="success"
          delay={0.15}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card glass>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-primary" />
                Live Monitoring Preview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <LiveFeed message={lastMessage} isConnected={isConnected} />
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <SystemHealthCard status={status} />
          
        </div>
      </div>
    </DashboardLayout>
  );
}
