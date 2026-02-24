import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";

import Home from "./pages/Home";
import RoleSelect from "./pages/RoleSelect";

// Signup
import PatientSignup from "./pages/signup/PatientSignup";
import DoctorSignup from "./pages/signup/DoctorSignup";
import DiagnosticSignup from "./pages/signup/DiagnosticSignup";
import InsuranceSignup from "./pages/signup/InsuranceSignup";

// Login
import PatientLogin from "./pages/login/PatientLogin";
import DoctorLogin from "./pages/login/DoctorLogin";
import DiagnosticLogin from "./pages/login/DiagnosticLogin";
import InsuranceLogin from "./pages/login/InsuranceLogin";

// Dashboard
import PatientDashboard from "./pages/dashboard/PatientDashboard";
import DoctorDashboard from "./pages/dashboard/DoctorDashboard";
import DiagnosticDashboard from "./pages/dashboard/DiagnosticDashboard";
import InsuranceDashboard from "./pages/dashboard/InsuranceDashboard";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/roles" element={<RoleSelect />} />

        {/* Signup */}
        <Route path="/signup/patient" element={<PatientSignup />} />
        <Route path="/signup/doctor" element={<DoctorSignup />} />
        <Route path="/signup/diagnostic" element={<DiagnosticSignup />} />
        <Route path="/signup/insurance" element={<InsuranceSignup />} />

        {/* Login */}
        <Route path="/login/patient" element={<PatientLogin />} />
        <Route path="/login/doctor" element={<DoctorLogin />} />
        <Route path="/login/diagnostic" element={<DiagnosticLogin />} />
        <Route path="/login/insurance" element={<InsuranceLogin />} />

        {/* Dashboard */}
        <Route path="/dashboard/patient" element={<PatientDashboard />} />
        <Route path="/dashboard/doctor" element={<DoctorDashboard />} />
        <Route path="/dashboard/diagnostic" element={<DiagnosticDashboard />} />
        <Route path="/dashboard/insurance" element={<InsuranceDashboard />} />
      </Routes>
    </Router>
  );
}

export default App;