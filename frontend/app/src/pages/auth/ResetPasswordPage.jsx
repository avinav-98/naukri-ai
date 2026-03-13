import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../../auth/AuthProvider";

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const { token } = useParams();
  const { resetPassword } = useAuth();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    setMessage("");
    setError("");
    try {
      await resetPassword(token, { new_password: formData.get("new_password") });
      setMessage("Password updated. Redirecting to sign in.");
      window.setTimeout(() => navigate("/signin", { replace: true }), 1200);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <p className="eyebrow">Reset Password</p>
      <h2>Set a new password</h2>
      <form className="stack-form" onSubmit={handleSubmit}>
        <label>
          New password
          <input minLength="6" name="new_password" type="password" required />
        </label>
        {message ? <p className="form-success">{message}</p> : null}
        {error ? <p className="form-error">{error}</p> : null}
        <button className="primary-button" type="submit">
          Save Password
        </button>
      </form>
      <div className="inline-links">
        <Link to="/signin">Back to sign in</Link>
      </div>
    </section>
  );
}
