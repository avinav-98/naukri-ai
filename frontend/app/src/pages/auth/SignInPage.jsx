import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../auth/AuthProvider";

const howItWorks = [
  {
    step: "1",
    title: "Connect Profile",
    description: "Import your Naukri profile and preferences.",
  },
  {
    step: "2",
    title: "AI Finds Jobs",
    description: "Our engine scans thousands of listings.",
  },
  {
    step: "3",
    title: "Auto Apply",
    description: "Apply instantly to the most relevant jobs.",
  },
  {
    step: "4",
    title: "Track Results",
    description: "Monitor applications from your dashboard.",
  },
];

const features = [
  {
    icon: "🔎",
    title: "Smart Job Discovery",
    description: "Find jobs matching your skills.",
  },
  {
    icon: "🎯",
    title: "AI Relevance Scoring",
    description: "Rank jobs based on probability of response.",
  },
  {
    icon: "🤖",
    title: "Auto Apply Engine",
    description: "Automatically submit applications.",
  },
  {
    icon: "📊",
    title: "Application Dashboard",
    description: "Track applied jobs and response status.",
  },
  {
    icon: "⚙️",
    title: "Custom Filters",
    description: "Experience, salary, and location preferences.",
  },
  {
    icon: "🔐",
    title: "Secure Session System",
    description: "Protected login and credential storage.",
  },
];

const previewMetrics = [
  { label: "Jobs Found Today", value: "128" },
  { label: "Applications Sent", value: "36" },
  { label: "Interview Responses", value: "08" },
  { label: "Relevance Score", value: "92%" },
];

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
    <main className="landing-page">
      <section className="hero-section">
        <div className="hero-copy">
          <p className="eyebrow">AI Job Search Automation</p>
          <h1>Automate Your Job Search with AI</h1>
          <p className="hero-text">
            Find relevant jobs, apply automatically, and track applications in one dashboard.
          </p>
          <div className="hero-actions">
            <a className="primary-button" href="#signin-form">
              Get Started
            </a>
            <a className="secondary-button" href="#features">
              View Features
            </a>
          </div>
          <div className="benefit-list">
            <span>AI Job Matching</span>
            <span>One-Click Auto Apply</span>
            <span>Smart Application Tracking</span>
          </div>

          <section className="hero-login-card" id="signin-form">
            <div className="hero-login-header">
              <div>
                <p className="eyebrow">Sign In</p>
                <h2>Access Your Automation Dashboard</h2>
              </div>
              <Link className="text-link" to="/signup">
                Create account
              </Link>
            </div>
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
        </div>

        <div className="hero-preview">
          <div className="hero-preview-card">
            <div className="preview-window-bar">
              <span />
              <span />
              <span />
            </div>
            <div className="preview-header-row">
              <div>
                <p className="eyebrow">Dashboard Preview</p>
                <h2>Naukri Auto Apply AI</h2>
              </div>
              <span className="status-pill active">Live Tracking</span>
            </div>
            <div className="preview-metric-grid">
              {previewMetrics.map((metric) => (
                <article className="preview-metric-card" key={metric.label}>
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                </article>
              ))}
            </div>
            <div className="preview-board">
              <div className="preview-board-row">
                <span>Frontend Engineer at Acme</span>
                <strong>96%</strong>
              </div>
              <div className="preview-board-row">
                <span>Backend Developer at Orbit</span>
                <strong>91%</strong>
              </div>
              <div className="preview-board-row">
                <span>Platform Engineer at Nova</span>
                <strong>88%</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section" id="how-it-works">
        <div className="section-heading">
          <p className="eyebrow">How It Works</p>
          <h2>Understand the workflow in minutes</h2>
        </div>
        <div className="how-grid">
          {howItWorks.map((item) => (
            <article className="feature-card step-card" key={item.step}>
              <span className="step-badge">{item.step}</span>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-section" id="features">
        <div className="section-heading">
          <p className="eyebrow">Core Features</p>
          <h2>Built for high-volume, focused job hunting</h2>
        </div>
        <div className="feature-grid">
          {features.map((feature) => (
            <article className="feature-card" key={feature.title}>
              <span className="feature-icon">{feature.icon}</span>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-section dashboard-preview-section">
        <div className="section-heading">
          <p className="eyebrow">Dashboard Preview</p>
          <h2>Powerful Job Application Dashboard</h2>
        </div>
        <div className="dashboard-highlight-grid">
          <article className="feature-card">
            <span className="feature-icon">📊</span>
            <h3>Jobs Found Today</h3>
            <p>Stay on top of the newest matching opportunities every day.</p>
          </article>
          <article className="feature-card">
            <span className="feature-icon">📤</span>
            <h3>Applications Sent</h3>
            <p>Review exactly what the automation engine has already submitted.</p>
          </article>
          <article className="feature-card">
            <span className="feature-icon">📬</span>
            <h3>Interview Responses</h3>
            <p>Spot employer engagement faster instead of searching your inbox manually.</p>
          </article>
          <article className="feature-card">
            <span className="feature-icon">⭐</span>
            <h3>Relevance Score Tracking</h3>
            <p>Prioritize the listings with the strongest fit before the market moves.</p>
          </article>
        </div>
      </section>

      <section className="landing-section cta-section">
        <p className="eyebrow">Call To Action</p>
        <h2>Stop wasting hours applying manually.</h2>
        <p className="cta-text">Let AI do the work while you focus on interviews.</p>
        <div className="hero-actions cta-actions">
          <Link className="primary-button" to="/signup">
            Create Free Account
          </Link>
        </div>
      </section>
    </main>
  );
}
