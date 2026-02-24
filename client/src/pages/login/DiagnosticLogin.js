import { useNavigate } from "react-router-dom";
import { useState } from "react";

function PatientLogin() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });

  const handleSubmit = (e) => {
    e.preventDefault();
    alert("Login Successful");
    navigate("/dashboard/diagnostic");
  };

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h2>Diagnostic Login</h2>
      <form onSubmit={handleSubmit}>
        <input placeholder="Email" onChange={(e)=>setForm({...form,email:e.target.value})}/>
        <input type="password" placeholder="Password"
               onChange={(e)=>setForm({...form,password:e.target.value})}/>
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

export default DiagnosticLogin;