import React, { useState, useRef } from "react";

// ---- Agent pipeline definition — mirrors your Flask app.py sequence ----
const PIPELINE_STAGES = [
  { key: "orchestrator", label: "Orchestrator", desc: "Planning pipeline" },
  { key: "decomposer", label: "Decomposer", desc: "Breaking down query" },
  { key: "search_agent", label: "Search Agent", desc: "Retrieving sources" },
  { key: "summarizer", label: "Summarizer", desc: "Drafting answer" },
  { key: "fact_checker", label: "Fact Checker", desc: "Validating claims" },
];

const API_BASE =
  process.env.REACT_APP_API_URL || "http://127.0.0.1:5000";

export default function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeStage, setActiveStage] = useState(-1);
  const [expandedTrace, setExpandedTrace] = useState(null);
  const pollRef = useRef(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setActiveStage(0);

    // Simulate stage progression visually while the real request is in flight.
    // The backend doesn't stream yet, so this gives the user a sense of where
    // the pipeline likely is based on typical relative timings.
    let stageIndex = 0;
    const stageDurations = [1500, 1500, 9000, 3000, 4000]; // rough ms per stage
    function advance() {
      stageIndex++;
      if (stageIndex < PIPELINE_STAGES.length) {
        setActiveStage(stageIndex);
        pollRef.current = setTimeout(advance, stageDurations[stageIndex]);
      }
    }
    pollRef.current = setTimeout(advance, stageDurations[0]);

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      clearTimeout(pollRef.current);

      if (!res.ok) {
        setError(data.error || "Something went wrong");
      } else {
        setResult(data);
        setActiveStage(PIPELINE_STAGES.length);
      }
    } catch (err) {
      clearTimeout(pollRef.current);
      setError("Could not reach the AgentFlow server. Is api/app.py running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <Header />

      <form onSubmit={handleSubmit} style={styles.searchForm}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a research question…"
          style={styles.input}
          disabled={loading}
        />
        <button type="submit" style={styles.button} disabled={loading || !query.trim()}>
          {loading ? "Running…" : "Research"}
        </button>
      </form>

      {error && (
        <div style={styles.errorBox}>
          <strong>Pipeline error.</strong> {error}
        </div>
      )}

      {(loading || result) && (
        <div style={styles.splitView}>
          <div style={styles.answerColumn}>
            <AnswerPanel result={result} loading={loading} />
          </div>
          <div style={styles.traceColumn}>
            <PipelinePanel
              activeStage={activeStage}
              trace={result?.trace}
              loading={loading}
              expandedTrace={expandedTrace}
              setExpandedTrace={setExpandedTrace}
            />
          </div>
        </div>
      )}

      {!loading && !result && !error && <EmptyState />}
    </div>
  );
}

function Header() {
  return (
    <div style={styles.header}>
      <div style={styles.logoMark}>AF</div>
      <div>
        <div style={styles.title}>AgentFlow</div>
        <div style={styles.subtitle}>Multi-agent research assistant — grounded reasoning, visible pipeline</div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div style={styles.emptyState}>
      <div style={styles.emptyStateText}>
        Every answer here traces back to retrieved sources. Ask something specific —
        the pipeline decomposes it, searches, drafts, and fact-checks before responding.
      </div>
    </div>
  );
}

function AnswerPanel({ result, loading }) {
  if (loading && !result) {
    return (
      <div style={styles.panel}>
        <div style={styles.panelLabel}>ANSWER</div>
        <div style={styles.skeletonLine} />
        <div style={{ ...styles.skeletonLine, width: "85%" }} />
        <div style={{ ...styles.skeletonLine, width: "92%" }} />
        <div style={{ ...styles.skeletonLine, width: "70%" }} />
      </div>
    );
  }

  if (!result) return null;

  return (
    <div style={styles.panel}>
      <div style={styles.panelLabel}>ANSWER</div>
      <div style={styles.answerText}>{result.answer}</div>

      <div style={styles.confidenceRow}>
        <ConfidenceBadge confidence={result.confidence} status={result.status} />
      </div>

      {result.sources?.length > 0 && (
        <div style={styles.sourcesBlock}>
          <div style={styles.sourcesLabel}>SOURCES</div>
          {result.sources.map((url, i) => (
            <a key={i} href={url} target="_blank" rel="noreferrer" style={styles.sourceLink}>
              {new URL(url).hostname.replace("www.", "")}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

function ConfidenceBadge({ confidence, status }) {
  const pct = Math.round((confidence ?? 0) * 100);
  const color = pct >= 80 ? "#4ADE80" : pct >= 50 ? "#F0A830" : "#F87171";
  return (
    <div style={styles.confidenceBadge}>
      <div style={{ ...styles.confidenceDot, background: color }} />
      <span style={{ color }}>{pct}% grounded confidence</span>
      <span style={styles.statusTag}>
        {status === "validated" ? "validated" : "best effort"}
      </span>
    </div>
  );
}

function PipelinePanel({ activeStage, trace, loading, expandedTrace, setExpandedTrace }) {
  return (
    <div style={styles.panel}>
      <div style={styles.panelLabel}>AGENT PIPELINE</div>
      <div style={styles.pipelineList}>
        {PIPELINE_STAGES.map((stage, i) => {
          const isDone = trace
            ? trace.some((t) => t.agent === stage.key)
            : i < activeStage;
          const isActive = loading && i === activeStage;
          return (
            <div key={stage.key} style={styles.stageRow}>
              <div style={styles.stageIndicatorCol}>
                <div
                  style={{
                    ...styles.stageDot,
                    ...(isDone ? styles.stageDotDone : {}),
                    ...(isActive ? styles.stageDotActive : {}),
                  }}
                />
                {i < PIPELINE_STAGES.length - 1 && (
                  <div
                    style={{
                      ...styles.stageLine,
                      ...(isDone ? styles.stageLineDone : {}),
                    }}
                  />
                )}
              </div>
              <div style={styles.stageContent}>
                <div style={styles.stageLabel}>{stage.label}</div>
                <div style={styles.stageDesc}>
                  {isActive ? stage.desc + "…" : stage.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {trace && (
        <div style={styles.traceLog}>
          <div style={styles.sourcesLabel}>FULL TRACE ({trace.length} steps)</div>
          {trace.map((t, i) => (
            <div key={i} style={styles.traceItem}>
              <div
                style={styles.traceItemHeader}
                onClick={() => setExpandedTrace(expandedTrace === i ? null : i)}
              >
                <span style={styles.traceAgentName}>
                  {t.agent}
                  {t.iteration ? ` · iter ${t.iteration}` : ""}
                  {t.note ? ` · ${t.note}` : ""}
                </span>
                <span style={styles.traceTime}>{t.time_ms}ms</span>
              </div>
              {expandedTrace === i && (
                <pre style={styles.traceDetail}>
                  {JSON.stringify(t.output, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#0E0F11",
    color: "#E8E6E1",
    fontFamily: "'Inter', -apple-system, sans-serif",
    padding: "32px 24px 64px",
    maxWidth: 1100,
    margin: "0 auto",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 14,
    marginBottom: 36,
  },
  logoMark: {
    width: 40,
    height: 40,
    borderRadius: 10,
    background: "linear-gradient(135deg, #F0A830, #C9722A)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "'IBM Plex Mono', monospace",
    fontWeight: 700,
    fontSize: 14,
    color: "#0E0F11",
    flexShrink: 0,
  },
  title: {
    fontSize: 20,
    fontWeight: 600,
    letterSpacing: "-0.01em",
  },
  subtitle: {
    fontSize: 13,
    color: "#8A8780",
    marginTop: 2,
  },
  searchForm: {
    display: "flex",
    gap: 10,
    marginBottom: 28,
  },
  input: {
    flex: 1,
    background: "#16181B",
    border: "1px solid #2A2C30",
    borderRadius: 10,
    padding: "14px 16px",
    fontSize: 15,
    color: "#E8E6E1",
    outline: "none",
    fontFamily: "inherit",
  },
  button: {
    background: "#F0A830",
    color: "#0E0F11",
    border: "none",
    borderRadius: 10,
    padding: "14px 24px",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  errorBox: {
    background: "#2A1718",
    border: "1px solid #5C2A2A",
    color: "#F2A8A8",
    borderRadius: 10,
    padding: "14px 16px",
    fontSize: 13,
    marginBottom: 24,
  },
  splitView: {
    display: "grid",
    gridTemplateColumns: "1.4fr 1fr",
    gap: 20,
    alignItems: "start",
  },
  panel: {
    background: "#16181B",
    border: "1px solid #2A2C30",
    borderRadius: 14,
    padding: "20px 22px",
  },
  panelLabel: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: 11,
    letterSpacing: "0.08em",
    color: "#6F6C66",
    marginBottom: 16,
  },
  answerText: {
    fontSize: 15,
    lineHeight: 1.75,
    color: "#D9D6CF",
    whiteSpace: "pre-wrap",
  },
  skeletonLine: {
    height: 14,
    background: "#22242A",
    borderRadius: 6,
    marginBottom: 10,
    width: "100%",
    animation: "pulse 1.5s ease-in-out infinite",
  },
  confidenceRow: {
    marginTop: 20,
    paddingTop: 16,
    borderTop: "1px solid #2A2C30",
  },
  confidenceBadge: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 13,
    fontFamily: "'IBM Plex Mono', monospace",
  },
  confidenceDot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
  },
  statusTag: {
    marginLeft: "auto",
    fontSize: 11,
    color: "#6F6C66",
    border: "1px solid #2A2C30",
    borderRadius: 999,
    padding: "2px 10px",
  },
  sourcesBlock: {
    marginTop: 18,
  },
  sourcesLabel: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: 10,
    letterSpacing: "0.08em",
    color: "#6F6C66",
    marginBottom: 10,
  },
  sourceLink: {
    display: "block",
    fontSize: 13,
    color: "#8FB8E0",
    textDecoration: "none",
    marginBottom: 6,
  },
  pipelineList: {
    marginBottom: 8,
  },
  stageRow: {
    display: "flex",
    gap: 14,
  },
  stageIndicatorCol: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  stageDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    background: "#2A2C30",
    border: "2px solid #2A2C30",
    flexShrink: 0,
    marginTop: 3,
  },
  stageDotDone: {
    background: "#4ADE80",
    border: "2px solid #4ADE80",
  },
  stageDotActive: {
    background: "#F0A830",
    border: "2px solid #F0A830",
    boxShadow: "0 0 0 4px rgba(240,168,48,0.18)",
  },
  stageLine: {
    width: 2,
    flex: 1,
    minHeight: 24,
    background: "#2A2C30",
  },
  stageLineDone: {
    background: "#4ADE80",
  },
  stageContent: {
    paddingBottom: 20,
  },
  stageLabel: {
    fontSize: 14,
    fontWeight: 500,
    color: "#E8E6E1",
  },
  stageDesc: {
    fontSize: 12,
    color: "#6F6C66",
    marginTop: 2,
  },
  traceLog: {
    marginTop: 12,
    paddingTop: 16,
    borderTop: "1px solid #2A2C30",
  },
  traceItem: {
    marginBottom: 6,
  },
  traceItemHeader: {
    display: "flex",
    justifyContent: "space-between",
    padding: "8px 10px",
    background: "#1B1D21",
    borderRadius: 8,
    cursor: "pointer",
    fontSize: 12,
  },
  traceAgentName: {
    fontFamily: "'IBM Plex Mono', monospace",
    color: "#C9C6BF",
  },
  traceTime: {
    fontFamily: "'IBM Plex Mono', monospace",
    color: "#6F6C66",
  },
  traceDetail: {
    background: "#0E0F11",
    border: "1px solid #2A2C30",
    borderRadius: 8,
    padding: 12,
    fontSize: 11,
    color: "#8A8780",
    overflowX: "auto",
    marginTop: 4,
  },
  emptyState: {
    border: "1px dashed #2A2C30",
    borderRadius: 14,
    padding: "48px 32px",
    textAlign: "center",
  },
  emptyStateText: {
    fontSize: 14,
    color: "#6F6C66",
    maxWidth: 440,
    margin: "0 auto",
    lineHeight: 1.6,
  },
};