
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { ToastProvider } from "@/components/ui/toast";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";

import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import LiveMonitor from "@/pages/LiveMonitor";
import Patients from "@/pages/Patients";
import PatientDetail from "@/pages/PatientDetail";
import Reports from "@/pages/Reports";
import Analytics from "@/pages/Analytics";
import Caregivers from "@/pages/Caregivers";


export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/live-monitor"
              element={
                <ProtectedRoute>
                  <LiveMonitor />
                </ProtectedRoute>
              }
            />

            <Route
              path="/patients"
              element={
                <ProtectedRoute>
                  <Patients />
                </ProtectedRoute>
              }
            />

            <Route
              path="/patients/:id"
              element={
                <ProtectedRoute>
                  <PatientDetail />
                </ProtectedRoute>
              }
            />

            <Route
              path="/reports"
              element={
                <ProtectedRoute>
                  <Reports />
                </ProtectedRoute>
              }
            />

            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <Analytics />
                </ProtectedRoute>
              }
            />

            <Route
              path="/caregivers"
              element={
                <ProtectedRoute>
                  <Caregivers />
                </ProtectedRoute>
              }
            />

            

            {/* Redirect removed pages to Dashboard */}
            <Route
              path="/alerts"
              element={<Navigate to="/dashboard" replace />}
            />

            <Route
              path="/settings"
              element={<Navigate to="/dashboard" replace />}
            />

            <Route
              path="/"
              element={<Navigate to="/dashboard" replace />}
            />

            <Route
              path="*"
              element={<Navigate to="/dashboard" replace />}
            />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}
