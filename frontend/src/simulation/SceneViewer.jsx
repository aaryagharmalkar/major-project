import React, { useState, useEffect, useRef } from "react";
import SceneCanvas from "./SceneCanvas";
import ArkhamHUD from "./ArkhamHUD";
import { SCENARIO_REGISTRY } from "./scenarios";

export default function SceneViewer() {
  const [selectedCaseId, setSelectedCaseId] = useState("case_001");
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [activeHypotheses, setActiveHypotheses] = useState({});
  const [selectedTargetId, setSelectedTargetId] = useState("vehicle_1");
  const [cameraPreset, setCameraPreset] = useState("tactical");

  const lastFrameTimeRef = useRef(performance.now());

  // Active Scene IR loaded dynamically from Scenario Registry
  const scene = SCENARIO_REGISTRY[selectedCaseId]?.data || SCENARIO_REGISTRY.case_001.data;

  // Reset target selection when switching cases
  const handleSelectCase = (caseId) => {
    setSelectedCaseId(caseId);
    setCurrentTime(0);
    const newScene = SCENARIO_REGISTRY[caseId]?.data;
    if (newScene) {
      if (newScene.vehicles && newScene.vehicles.length > 0) {
        setSelectedTargetId(newScene.vehicles[0].id);
      } else if (newScene.people && newScene.people.length > 0) {
        setSelectedTargetId(newScene.people[0].id);
      }
    }
  };

  // High-precision animation clock loop
  useEffect(() => {
    let animationFrameId;

    const tick = (now) => {
      const deltaSec = (now - lastFrameTimeRef.current) / 1000;
      lastFrameTimeRef.current = now;

      if (isPlaying) {
        setCurrentTime((prevTime) => {
          const nextTime = prevTime + deltaSec * playbackSpeed;
          if (nextTime >= 10.0) {
            return 0; // Loop seamlessly
          }
          return nextTime;
        });
      }

      animationFrameId = requestAnimationFrame(tick);
    };

    lastFrameTimeRef.current = performance.now();
    animationFrameId = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(animationFrameId);
  }, [isPlaying, playbackSpeed]);

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        background: "#05080f",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* 3D Scene Viewport */}
      <SceneCanvas
        scene={scene}
        currentTime={currentTime}
        selectedTargetId={selectedTargetId}
        setSelectedTargetId={setSelectedTargetId}
        cameraPreset={cameraPreset}
      />

      {/* Arkham Detective Mode HUD Overlay */}
      <ArkhamHUD
        currentTime={currentTime}
        setCurrentTime={setCurrentTime}
        isPlaying={isPlaying}
        setIsPlaying={setIsPlaying}
        playbackSpeed={playbackSpeed}
        setPlaybackSpeed={setPlaybackSpeed}
        activeHypotheses={activeHypotheses}
        setActiveHypotheses={setActiveHypotheses}
        selectedTargetId={selectedTargetId}
        setSelectedTargetId={setSelectedTargetId}
        cameraPreset={cameraPreset}
        setCameraPreset={setCameraPreset}
        selectedCaseId={selectedCaseId}
        onSelectCase={handleSelectCase}
        scene={scene}
      />
    </div>
  );
}