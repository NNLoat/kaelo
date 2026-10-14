import { Component, type ErrorInfo, type ReactNode } from "react";

// Without this, a render-time throw leaves an empty #root with no feedback
// (a blank page). The boundary catches it and shows the error on screen.
export default class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Render error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: "2rem", fontFamily: "monospace", color: "#B4551D" }}>
          <h1 style={{ fontSize: "1.25rem", marginBottom: "0.75rem" }}>
            The app failed to render.
          </h1>
          <pre style={{ whiteSpace: "pre-wrap" }}>{this.state.error.message}</pre>
          <p style={{ marginTop: "1rem", color: "#5B6269" }}>
            Open the browser console for the full stack trace.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}
