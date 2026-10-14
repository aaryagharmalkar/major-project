import React, { useMemo } from "react";
import { resolveEntityWaypoints, sampleEntityState } from "./kinematics";
import { SCENARIO_REGISTRY } from "./scenarios";

export default function ArkhamHUD({
  currentTime,
  setCurrentTime,
  isPlaying,
  setIsPlaying,
  playbackSpeed,
  setPlaybackSpeed,
  activeHypotheses = {},
  setActiveHypotheses,
  selectedTargetId,
  setSelectedTargetId,
  cameraPreset,
  setCameraPreset,
  selectedCaseId,
  onSelectCase,
  scene = {},
}) {
  const formatTime = (seconds) => {
    const s = Math.floor(seconds);
    const ms = Math.floor((seconds - s) * 1000);
    return `T+00:${s.toString().padStart(2, "0")}.${ms.toString().padStart(3, "0")}`;
  };

  const metadata = scene.metadata || {};
  const vehicles = scene.vehicles || [];
  const people = scene.people || [];
  const timeline = scene.timeline || [];
  const conflicts = scene.conflicts || [];

  // Combine targets for selection
  const allTargets = useMemo(() => {
    const list = [];
    vehicles.forEach((v) => list.push({ id: v.id, label: v.id.toUpperCase(), type: "vehicle", data: v }));
    people.forEach((p) => list.push({ id: p.id, label: (p.name || p.id).toUpperCase(), type: "person", data: p }));
    return list;
  }, [vehicles, people]);

  const activeTarget =
    allTargets.find((t) => t.id === selectedTargetId) || allTargets[0] || {};

  // Compute live velocity and kinematics dynamically for the active target
  const targetKinematics = useMemo(() => {
    if (!activeTarget.data) return { speedKmph: 0, position: { x: 0, y: 0, z: 0 } };
    const waypoints = resolveEntityWaypoints(activeTarget.data, timeline);
    return sampleEntityState(waypoints, currentTime);
  }, [activeTarget, timeline, currentTime]);

  // Active Keyframe Event Detection from dynamic timeline
  const currentEvent = useMemo(() => {
    if (!timeline || timeline.length === 0) return null;
    const idx = Math.min(timeline.length - 1, Math.floor((currentTime / 10.0) * timeline.length));
    return timeline[idx] || timeline[0];
  }, [timeline, currentTime]);

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        fontFamily: "'Courier New', Courier, monospace",
        color: "#00f0ff",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "16px",
        boxSizing: "border-box",
        userSelect: "none",
      }}
    >
      {/* ============================================================ */}
      {/* TOP BAR: CASE HEADER, SCENARIO SELECTOR, & HYPOTHESES        */}
      {/* ============================================================ */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          width: "100%",
          pointerEvents: "none",
        }}
      >
        {/* Left: Project Header & Case Switcher Dropdown */}
        <div
          style={{
            pointerEvents: "auto",
            background: "rgba(6, 11, 20, 0.88)",
            border: "1px solid rgba(0, 240, 255, 0.35)",
            boxShadow: "0 0 15px rgba(0, 240, 255, 0.15)",
            padding: "12px 18px",
            borderRadius: 6,
            backdropFilter: "blur(6px)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: "#00f0ff",
                boxShadow: "0 0 8px #00f0ff",
              }}
            />
            <span style={{ fontSize: 16, fontWeight: "bold", letterSpacing: 2 }}>
              SENTINEL // RECONSTRUCTION
            </span>
          </div>

          {/* Scenario / Case Selector */}
          <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 10, color: "#ffb700", letterSpacing: 1 }}>CASE:</span>
            <select
              value={selectedCaseId}
              onChange={(e) => onSelectCase && onSelectCase(e.target.value)}
              style={{
                background: "rgba(0, 240, 255, 0.1)",
                border: "1px solid #00f0ff",
                color: "#fff",
                padding: "3px 8px",
                fontSize: 11,
                fontFamily: "inherit",
                borderRadius: 4,
                outline: "none",
                cursor: "pointer",
              }}
            >
              {Object.values(SCENARIO_REGISTRY).map((sc) => (
                <option key={sc.id} value={sc.id} style={{ background: "#0c1322", color: "#fff" }}>
                  {sc.name}
                </option>
              ))}
            </select>
          </div>

          <div style={{ fontSize: 11, color: "#8bd0db", marginTop: 6 }}>
            LOCATION: <span style={{ color: "#fff" }}>{metadata.location_name}</span>
          </div>
        </div>

        {/* Center: Dynamic Conflict & Hypothesis Selector */}
        {conflicts.length > 0 ? (
          <div
            style={{
              pointerEvents: "auto",
              background: "rgba(6, 11, 20, 0.88)",
              border: "1px solid rgba(255, 183, 0, 0.4)",
              padding: "8px 14px",
              borderRadius: 6,
              backdropFilter: "blur(6px)",
              textAlign: "center",
              maxWidth: "420px",
            }}
          >
            <div style={{ fontSize: 10, color: "#ffb700", letterSpacing: 1, marginBottom: 6 }}>
              // CONFLICTING HYPOTHESIS ENGINE
            </div>
            {conflicts.map((conflict) => {
              const fieldName = conflict.field || conflict.key || "Parameter";
              const hyps = conflict.hypotheses || [];
              const activeHypId = activeHypotheses[conflict.id] || hyps[0]?.id;

              return (
                <div key={conflict.id} style={{ marginBottom: 4 }}>
                  <div style={{ fontSize: 10, color: "#7a9b9e", marginBottom: 3 }}>
                    {fieldName.toUpperCase().replace("_", " ")}:
                  </div>
                  <div style={{ display: "flex", gap: 6, justifyContent: "center", flexWrap: "wrap" }}>
                    {hyps.map((h, i) => {
                      const isSelected = activeHypId === h.id;
                      const label = typeof h.value === "number" ? `${h.value} km/h` : `${h.value}`;
                      const source = h.source ? ` (${h.source})` : "";

                      return (
                        <button
                          key={h.id || i}
                          onClick={() =>
                            setActiveHypotheses &&
                            setActiveHypotheses((prev) => ({
                              ...prev,
                              [conflict.id]: h.id,
                            }))
                          }
                          style={{
                            background: isSelected
                              ? "rgba(0, 240, 255, 0.25)"
                              : "rgba(255, 255, 255, 0.05)",
                            border: isSelected
                              ? "1px solid #00f0ff"
                              : "1px solid rgba(255, 255, 255, 0.2)",
                            color: isSelected ? "#00f0ff" : "#888",
                            padding: "3px 8px",
                            fontSize: 10,
                            cursor: "pointer",
                            borderRadius: 3,
                            fontFamily: "inherit",
                          }}
                        >
                          HYP {i + 1}: {label}
                          <span style={{ opacity: 0.6, fontSize: 9 }}>{source}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div
            style={{
              pointerEvents: "auto",
              background: "rgba(6, 11, 20, 0.88)",
              border: "1px solid rgba(0, 240, 255, 0.3)",
              padding: "8px 14px",
              borderRadius: 6,
              backdropFilter: "blur(6px)",
              fontSize: 11,
              color: "#00f0ff",
              letterSpacing: 1,
            }}
          >
            ✓ EVIDENCE CONSENSUS // NO CONFLICTS DETECTED
          </div>
        )}

        {/* Right: Camera Viewport Presets */}
        <div
          style={{
            pointerEvents: "auto",
            background: "rgba(6, 11, 20, 0.88)",
            border: "1px solid rgba(0, 240, 255, 0.35)",
            padding: "8px 12px",
            borderRadius: 6,
            backdropFilter: "blur(6px)",
          }}
        >
          <div style={{ fontSize: 10, color: "#8bd0db", marginBottom: 6, letterSpacing: 1 }}>
            CAMERA VIEWPORT
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            {[
              { id: "tactical", label: "TACTICAL 45°" },
              { id: "overhead", label: "OVERHEAD" },
              { id: "impact", label: "FOCUS POINT" },
            ].map((cam) => (
              <button
                key={cam.id}
                onClick={() => setCameraPreset(cam.id)}
                style={{
                  background:
                    cameraPreset === cam.id
                      ? "rgba(0, 240, 255, 0.2)"
                      : "rgba(255, 255, 255, 0.05)",
                  border:
                    cameraPreset === cam.id
                      ? "1px solid #00f0ff"
                      : "1px solid rgba(255, 255, 255, 0.2)",
                  color: cameraPreset === cam.id ? "#00f0ff" : "#888",
                  padding: "4px 8px",
                  fontSize: 10,
                  cursor: "pointer",
                  borderRadius: 3,
                  fontFamily: "inherit",
                }}
              >
                {cam.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* MIDDLE SECTION: DYNAMIC TELEMETRY & FORENSIC EVIDENCE CARD    */}
      {/* ============================================================ */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          width: "100%",
          pointerEvents: "none",
        }}
      >
        {/* Left: Target Telemetry */}
        <div
          style={{
            pointerEvents: "auto",
            background: "rgba(6, 11, 20, 0.88)",
            border: "1px solid rgba(0, 240, 255, 0.35)",
            padding: "14px",
            borderRadius: 6,
            backdropFilter: "blur(6px)",
            width: "270px",
          }}
        >
          <div style={{ fontSize: 11, color: "#ffb700", letterSpacing: 1.5, marginBottom: 8 }}>
            // TARGET TELEMETRY
          </div>

          <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
            {allTargets.map((t) => (
              <button
                key={t.id}
                onClick={() => setSelectedTargetId(t.id)}
                style={{
                  background:
                    selectedTargetId === t.id
                      ? "rgba(0, 240, 255, 0.2)"
                      : "rgba(255, 255, 255, 0.05)",
                  border:
                    selectedTargetId === t.id
                      ? "1px solid #00f0ff"
                      : "1px solid rgba(255, 255, 255, 0.15)",
                  color: selectedTargetId === t.id ? "#00f0ff" : "#777",
                  padding: "4px 6px",
                  fontSize: 10,
                  cursor: "pointer",
                  borderRadius: 3,
                  fontFamily: "inherit",
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {activeTarget.data && (
            <>
              <div style={{ fontSize: 12, marginBottom: 4 }}>
                <span style={{ color: "#7a9b9e" }}>ENTITY: </span>
                <span style={{ color: "#fff" }}>
                  {activeTarget.data.make || activeTarget.data.name || activeTarget.data.role || activeTarget.id}
                </span>
              </div>

              {activeTarget.data.registration && (
                <div style={{ fontSize: 12, marginBottom: 4 }}>
                  <span style={{ color: "#7a9b9e" }}>REG: </span>
                  <span style={{ color: "#fff" }}>{activeTarget.data.registration}</span>
                </div>
              )}

              <div
                style={{
                  marginTop: 10,
                  padding: "8px",
                  background: "rgba(0, 240, 255, 0.06)",
                  border: "1px solid rgba(0, 240, 255, 0.2)",
                  borderRadius: 4,
                }}
              >
                <div style={{ fontSize: 10, color: "#7a9b9e" }}>CALCULATED VELOCITY</div>
                <div style={{ fontSize: 22, fontWeight: "bold", color: "#00f0ff", marginTop: 2 }}>
                  {targetKinematics.speedKmph.toFixed(1)}{" "}
                  <span style={{ fontSize: 12, color: "#8bd0db" }}>km/h</span>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Right: Active Detective Forensic Node */}
        {currentEvent && (
          <div
            style={{
              pointerEvents: "auto",
              background: "rgba(6, 11, 20, 0.88)",
              border: "1px solid rgba(255, 0, 85, 0.4)",
              boxShadow: "0 0 15px rgba(255, 0, 85, 0.15)",
              padding: "14px",
              borderRadius: 6,
              backdropFilter: "blur(6px)",
              width: "280px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
              <div
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: "#ff0055",
                  boxShadow: "0 0 6px #ff0055",
                }}
              />
              <span style={{ fontSize: 11, color: "#ff0055", fontWeight: "bold", letterSpacing: 1 }}>
                // FORENSIC EVIDENCE NODE
              </span>
            </div>

            <div style={{ fontSize: 13, color: "#fff", fontWeight: "bold", marginBottom: 6 }}>
              {(currentEvent.event_type || "Incident Event").toUpperCase().replace("_", " ")}
            </div>

            <div style={{ fontSize: 11, color: "#a5b9bc", marginBottom: 8, lineHeight: 1.4 }}>
              {currentEvent.description || "Forensic event observed at documented timestamp."}
            </div>

            <div style={{ fontSize: 10, color: "#ffb700" }}>
              TIMESTAMP: <span style={{ color: "#fff" }}>{currentEvent.timestamp || "Documented"}</span>
            </div>
            <div style={{ fontSize: 10, color: "#00f0ff", marginTop: 2 }}>
              CONFIDENCE:{" "}
              <span style={{ color: "#fff" }}>
                {Math.round((currentEvent.confidence || 0.9) * 100)}%
              </span>
            </div>
          </div>
        )}
      </div>

      {/* ============================================================ */}
      {/* BOTTOM BAR: DYNAMIC TIMELINE SCRUBBER & KEYFRAME BADGES      */}
      {/* ============================================================ */}
      <div
        style={{
          pointerEvents: "auto",
          background: "rgba(6, 11, 20, 0.92)",
          border: "1px solid rgba(0, 240, 255, 0.35)",
          boxShadow: "0 0 20px rgba(0, 240, 255, 0.12)",
          padding: "14px 20px",
          borderRadius: 8,
          backdropFilter: "blur(8px)",
        }}
      >
        {/* Dynamic Timeline Keyframe Badges */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: 10,
            color: "#6b8e94",
            marginBottom: 6,
            letterSpacing: 1,
          }}
        >
          {timeline.length > 0 ? (
            timeline.map((ev, i) => {
              const timeFraction = i / Math.max(1, timeline.length - 1);
              const eventSec = timeFraction * 10.0;
              const isNear = Math.abs(currentTime - eventSec) < 1.2;

              return (
                <span
                  key={ev.id || i}
                  onClick={() => setCurrentTime(eventSec)}
                  style={{
                    cursor: "pointer",
                    color: isNear ? "#00f0ff" : "inherit",
                    fontWeight: isNear ? "bold" : "normal",
                  }}
                >
                  ◆ T+{eventSec.toFixed(1)}s ({ev.event_type?.toUpperCase().replace("_", " ")})
                </span>
              );
            })
          ) : (
            <>
              <span onClick={() => setCurrentTime(0)} style={{ cursor: "pointer" }}>◆ T+0.0s (START)</span>
              <span onClick={() => setCurrentTime(5)} style={{ cursor: "pointer" }}>● T+5.0s (EVENT)</span>
              <span onClick={() => setCurrentTime(10)} style={{ cursor: "pointer" }}>◆ T+10.0s (FINAL)</span>
            </>
          )}
        </div>

        {/* Detective Scrubbing Slider */}
        <div style={{ position: "relative", width: "100%", marginBottom: 12 }}>
          <input
            type="range"
            min="0"
            max="10"
            step="0.05"
            value={currentTime}
            onChange={(e) => {
              setCurrentTime(parseFloat(e.target.value));
              setIsPlaying(false);
            }}
            style={{
              width: "100%",
              height: "6px",
              background: `linear-gradient(to right, #00f0ff 0%, #00f0ff ${(currentTime / 10) * 100}%, rgba(255,255,255,0.15) ${(currentTime / 10) * 100}%, rgba(255,255,255,0.15) 100%)`,
              outline: "none",
              borderRadius: "3px",
              cursor: "pointer",
              appearance: "none",
            }}
          />
        </div>

        {/* Playback Controls & Speed */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button
              onClick={() => setCurrentTime(0)}
              style={{
                background: "rgba(255, 255, 255, 0.06)",
                border: "1px solid rgba(0, 240, 255, 0.3)",
                color: "#00f0ff",
                padding: "6px 12px",
                fontSize: 11,
                cursor: "pointer",
                borderRadius: 4,
                fontFamily: "inherit",
              }}
            >
              ⏮ REWIND
            </button>

            <button
              onClick={() => setCurrentTime((t) => Math.max(0, t - 0.2))}
              style={{
                background: "rgba(255, 255, 255, 0.06)",
                border: "1px solid rgba(0, 240, 255, 0.3)",
                color: "#00f0ff",
                padding: "6px 10px",
                fontSize: 11,
                cursor: "pointer",
                borderRadius: 4,
                fontFamily: "inherit",
              }}
            >
              -0.2s
            </button>

            <button
              onClick={() => setIsPlaying(!isPlaying)}
              style={{
                background: isPlaying ? "rgba(255, 0, 85, 0.2)" : "rgba(0, 240, 255, 0.2)",
                border: isPlaying ? "1px solid #ff0055" : "1px solid #00f0ff",
                color: isPlaying ? "#ff0055" : "#00f0ff",
                padding: "6px 18px",
                fontSize: 12,
                fontWeight: "bold",
                cursor: "pointer",
                borderRadius: 4,
                fontFamily: "inherit",
                letterSpacing: 1,
              }}
            >
              {isPlaying ? "⏸ PAUSE" : "▶ PLAY"}
            </button>

            <button
              onClick={() => setCurrentTime((t) => Math.min(10, t + 0.2))}
              style={{
                background: "rgba(255, 255, 255, 0.06)",
                border: "1px solid rgba(0, 240, 255, 0.3)",
                color: "#00f0ff",
                padding: "6px 10px",
                fontSize: 11,
                cursor: "pointer",
                borderRadius: 4,
                fontFamily: "inherit",
              }}
            >
              +0.2s
            </button>
          </div>

          <div style={{ fontSize: 16, fontWeight: "bold", color: "#fff", letterSpacing: 2 }}>
            {formatTime(currentTime)}
          </div>

          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <span style={{ fontSize: 10, color: "#6b8e94", marginRight: 4 }}>SPEED:</span>
            {[0.25, 0.5, 1.0, 2.0].map((spd) => (
              <button
                key={spd}
                onClick={() => setPlaybackSpeed(spd)}
                style={{
                  background:
                    playbackSpeed === spd
                      ? "rgba(0, 240, 255, 0.2)"
                      : "rgba(255, 255, 255, 0.05)",
                  border:
                    playbackSpeed === spd
                      ? "1px solid #00f0ff"
                      : "1px solid rgba(255, 255, 255, 0.15)",
                  color: playbackSpeed === spd ? "#00f0ff" : "#777",
                  padding: "4px 8px",
                  fontSize: 10,
                  cursor: "pointer",
                  borderRadius: 3,
                  fontFamily: "inherit",
                }}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
