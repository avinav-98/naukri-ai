import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../../auth/AuthProvider";

export function SignUpPage() {
  const navigate = useNavigate();
  const { signup, authPending } = useAuth();
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    setError("");
    try {
      await signup({
        full_name: formData.get("full_name"),
        email: formData.get("email"),
        password: formData.get("password"),
        naukri_id: formData.get("naukri_id"),
        naukri_password: formData.get("naukri_password"),
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <p className="eyebrow">Create Account</p>
      <h2>Register and keep the existing cookie session flow</h2>
      <form className="stack-form" onSubmit={handleSubmit}>
        <label>
          Full name
          <input name="full_name" required />
        </label>
        <label>
          Email
          <input name="email" type="email" required />
        </label>
        <label>
          Password
          <input name="password" minLength="6" type="password" required />
        </label>
        <label>
          Naukri ID
          <input name="naukri_id" />
        </label>
        <label>
          Naukri Password
          <input name="naukri_password" type="password" />
        </label>
        {error ? <p className="form-error">{error}</p> : null}
        <button className="primary-button" disabled={authPending} type="submit">
          {authPending ? "Creating..." : "Create Account"}
        </button>
      </form>
      <div className="inline-links">
        <Link to="/signin">Back to sign in</Link>
      </div>
    </section>
  );
}
