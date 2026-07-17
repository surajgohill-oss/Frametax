import { Component } from "react";

// Top-level error boundary — a render failure anywhere in the routed app
// now surfaces a visible panel instead of degrading into a blank page.
// Detection + prevention only; not a redesign.
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null, info: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Full detail stays in the dev console; the UI shows a concise panel.
    // eslint-disable-next-line no-console
    console.error(`[CineGlobe] render failure${this.props.label ? ` (${this.props.label})` : ""}:`, error, info);
    this.setState({ info });
  }

  render() {
    const { error, info } = this.state;
    if (!error) return this.props.children;

    // Scoped boundaries (e.g. the sidebar identity globe) pass a `fallback`
    // so a non-critical subtree failure degrades gracefully instead of
    // taking over the screen with the full error panel.
    if ("fallback" in this.props) return this.props.fallback;

    const dev = import.meta.env.DEV;
    return (
      <div className="app-error-boundary">
        <div className="app-error-card">
          <p className="app-error-eyebrow">CineGlobe — unexpected error</p>
          <h2>The page failed to render.</h2>
          <p className="app-error-msg">{error.message || String(error)}</p>
          {dev && info?.componentStack && (
            <pre className="app-error-stack">{info.componentStack.trim()}</pre>
          )}
          <button className="app-error-reload" onClick={() => window.location.reload()}>
            Reload
          </button>
        </div>
      </div>
    );
  }
}
