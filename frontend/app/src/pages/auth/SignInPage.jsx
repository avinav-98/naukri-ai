import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../auth/AuthProvider";

export function SignInPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, authPending } = useAuth();
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    setError("");
    try {
      await login({
        email: formData.get("email"),
        password: formData.get("password"),
      });
      navigate(location.state?.from?.pathname || "/dashboard", { replace: true });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <p className="eyebrow">Sign In</p>
      <h2>Continue with your existing session system</h2>
      <form className="stack-form" onSubmit={handleSubmit}>
        <label>
          Email
          <input name="email" type="email" required />
        </label>
        <label>
          Password
          <input name="password" type="password" required />
        </label>
        {error ? <p className="form-error">{error}</p> : null}
        <button className="primary-button" disabled={authPending} type="submit">
          {authPending ? "Signing in..." : "Sign In"}
        </button>
      </form>
      <div className="inline-links">
        <Link to="/signup">Create account</Link>
        <Link to="/forgot-password">Forgot password</Link>
      </div>
    </section>
  );
}
