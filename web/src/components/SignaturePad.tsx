"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  onChange: (dataUrl: string | null) => void;
  disabled?: boolean;
};

/**
 * Canvas acknowledgement stub — not a certified e-signature capture.
 */
export function SignaturePad({ onChange, disabled }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const drawing = useRef(false);
  const [hasInk, setHasInk] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    canvas.width = Math.floor(width * ratio);
    canvas.height = Math.floor(height * ratio);
    ctx.scale(ratio, ratio);
    ctx.strokeStyle = "#0f1c24";
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.fillStyle = "#f7fafb";
    ctx.fillRect(0, 0, width, height);
  }, []);

  function pos(e: React.PointerEvent<HTMLCanvasElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  function pointerDown(e: React.PointerEvent<HTMLCanvasElement>) {
    if (disabled) return;
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!ctx) return;
    drawing.current = true;
    e.currentTarget.setPointerCapture(e.pointerId);
    const { x, y } = pos(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
  }

  function pointerMove(e: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawing.current || disabled) return;
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;
    const { x, y } = pos(e);
    ctx.lineTo(x, y);
    ctx.stroke();
    setHasInk(true);
  }

  function pointerUp() {
    if (!drawing.current) return;
    drawing.current = false;
    const canvas = canvasRef.current;
    if (!canvas) return;
    // Emit after stroke; parent stores data URL stub for acknowledgement API
    onChange(canvas.toDataURL("image/png"));
    setHasInk(true);
  }

  function clear() {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    ctx.fillStyle = "#f7fafb";
    ctx.fillRect(0, 0, canvas.clientWidth, canvas.clientHeight);
    setHasInk(false);
    onChange(null);
  }

  return (
    <div className="stack">
      <p className="muted" style={{ margin: 0 }}>
        Draw acknowledgement mark below.{" "}
        <strong>Not a certified e-signature</strong> — demo stub only.
      </p>
      <canvas
        ref={canvasRef}
        className="signature-canvas"
        style={{
          width: "100%",
          height: "140px",
          borderRadius: "8px",
          border: "1px solid var(--border)",
          touchAction: "none",
          cursor: disabled ? "not-allowed" : "crosshair",
          background: "#f7fafb",
        }}
        onPointerDown={pointerDown}
        onPointerMove={pointerMove}
        onPointerUp={pointerUp}
        onPointerLeave={pointerUp}
      />
      <button
        type="button"
        className="btn secondary small"
        onClick={clear}
        disabled={disabled || !hasInk}
      >
        Clear mark
      </button>
    </div>
  );
}
