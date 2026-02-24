import { Link } from "react-router-dom";

function RoleSelect() {
  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h2>Select Your Role</h2>

      <div>
        <Link to="/signup/patient"><button>Patient</button></Link>
        <Link to="/signup/doctor"><button>Doctor</button></Link>
        <Link to="/signup/diagnostic"><button>Diagnostic Center</button></Link>
        <Link to="/signup/insurance"><button>Insurance Provider</button></Link>
      </div>
    </div>
  );
}

export default RoleSelect;