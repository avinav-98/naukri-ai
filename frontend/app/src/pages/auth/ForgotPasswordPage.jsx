import { useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../../auth/AuthProvider";

export function ForgotPasswordPage() {
  const { forgotPassword } = useAuth();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    setMessage("");
    setError("");
    try {
      const result = await forgotPassword({ email: formData.get("email") });
      setMessage(result.message || "Reset request submitted.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <p className="eyebrow">Password Recovery</p>
      <h2>Request a reset token</h2>
      <form className="stack-form" onSubmit={handleSubmit}>
        <label>
          Email
          <input name="email" type="email" required />
        </label>
        {message ? <p className="form-success">{message}</p> : null}
        {error ? <p className="form-error">{error}</p> : null}
        <button className="primary-button" type="submit">
          Request Reset
        </button>
      </form>
      <div className="inline-links">
        <Link to="/signin">Back to sign in</Link>
      </div>
    </section>
  );
}
