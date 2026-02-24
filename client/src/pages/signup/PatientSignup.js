import { useNavigate } from "react-router-dom";
import { useState } from "react";

function PatientSignup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });

  const handleSubmit = (e) => {
    e.preventDefault();
    alert("Patient Registered");
    navigate("/login/patient");
  };

  return (
    <div style={styles.container}>
      <h2>Patient Signup</h2>
      <form onSubmit={handleSubmit}>
        <input placeholder="Name" onChange={(e)=>setForm({...form,name:e.target.value})}/>
        <input placeholder="Email" onChange={(e)=>setForm({...form,email:e.target.value})}/>
        <input type="password" placeholder="Password"
               onChange={(e)=>setForm({...form,password:e.target.value})}/>
        <button type="submit">Register</button>
      </form>
    </div>
  );
}

const styles = {
  container: { textAlign: "center", marginTop: "50px" }
};

export default PatientSignup;