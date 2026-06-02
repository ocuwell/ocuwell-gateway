import { BrowserQRCodeReader } from "@zxing/browser";
import { BarcodeFormat, DecodeHintType } from "@zxing/library";
import jsQR from "jsqr";
import {
  Camera,
  CheckCircle2,
  Download,
  FileCheck2,
  FileInput,
  FileUp,
  Loader2,
  LockKeyhole,
  QrCode,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Usb,
  XCircle,
} from "lucide-react";
import QRCode from "qrcode";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent, ReactNode } from "react";

type FlowMode = "activation" | "deactivation";
type TransferMethod = "file" | "qr";

type RequestInput = {
  content: string;
  label: string;
  source: TransferMethod;
};

type ActivationResponse = {
  request_id: string;
  file_name: string;
  license_file_content: string;
  content_encoding: string;
};

type DeactivationResponse = {
  ok: boolean;
  request_id?: string | null;
};

type ResultState =
  | { mode: "activation"; data: ActivationResponse }
  | { mode: "deactivation"; data: DeactivationResponse };

const ACTIVATION_ENDPOINT = "/v1/client/licenses/activate-offline/license-file";
const DEACTIVATION_ENDPOINT = "/v1/client/licenses/deactivate-offline/request-file";
const QR_CHUNK_SIZE = 1420;
const QR_MAX_CHUNKS = 3;
const QR_MAX_CONTENT_LENGTH = QR_CHUNK_SIZE * QR_MAX_CHUNKS;
const QR_SCAN_INTERVAL_MS = 120;

const zxingHints = new Map<DecodeHintType, unknown>([
  [DecodeHintType.POSSIBLE_FORMATS, [BarcodeFormat.QR_CODE]],
  [DecodeHintType.TRY_HARDER, true],
]);
const zxingQrReader = new BrowserQRCodeReader(zxingHints);

export function App() {
  const [mode, setMode] = useState<FlowMode>("activation");
  const [method, setMethod] = useState<TransferMethod>("file");
  const [requestInput, setRequestInput] = useState<RequestInput | null>(null);
  const [result, setResult] = useState<ResultState | null>(null);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const modeCopy = useMemo(
    () =>
      mode === "activation"
        ? {
            heading: "Activate an offline workstation",
            helper:
              "Upload or scan the activation request exported from OCUMAPS, then return the signed response by USB or QR.",
            submit: "Generate activation response",
            ready: "Activation request ready",
          }
        : {
            heading: "Deactivate an offline workstation",
            helper:
              "Upload or scan the deactivation request exported from OCUMAPS. The gateway completes the LicenseSpring release online.",
            submit: "Process deactivation",
            ready: "Deactivation request ready",
          },
    [mode],
  );

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(""), 3000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  function resetFlow(nextMode = mode, nextMethod = method) {
    setMode(nextMode);
    setMethod(nextMethod);
    setRequestInput(null);
    setResult(null);
    setError("");
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const content = (await file.text()).trim();
      if (!content) {
        setError("The selected request file is empty.");
        return;
      }

      setRequestInput({ content, label: file.name, source: "file" });
      setResult(null);
      setError("");
      setToast("Request file loaded.");
    } catch {
      setError("The request file could not be read.");
    } finally {
      event.target.value = "";
    }
  }

  function handleScannedRequest(value: string) {
    const content = value.trim();
    if (!content) {
      setError("The scanned QR did not contain a request.");
      return;
    }

    setRequestInput({ content, label: "Scanned request QR", source: "qr" });
    setResult(null);
    setError("");
    setToast("Request QR captured.");
  }

  async function submitRequest() {
    if (!requestInput) {
      setError("Load a request file or scan a request QR first.");
      return;
    }

    setIsSubmitting(true);
    setError("");
    setResult(null);

    try {
      const endpoint = mode === "activation" ? ACTIVATION_ENDPOINT : DEACTIVATION_ENDPOINT;
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildRequestBody(requestInput.content, mode)),
      });
      const responseBody = await readResponseBody(response);

      if (!response.ok) {
        throw new Error(readErrorMessage(responseBody, "The gateway could not process this request."));
      }

      if (mode === "activation") {
        setResult({ mode, data: responseBody as ActivationResponse });
        setToast("Activation response is ready.");
      } else {
        setResult({ mode, data: responseBody as DeactivationResponse });
        setToast("Deactivation processed.");
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "The gateway request failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function clearRequest() {
    setRequestInput(null);
    setResult(null);
    setError("");
  }

  function downloadActivationFile(data: ActivationResponse) {
    const blob = new Blob([data.license_file_content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = data.file_name || "licensespring-offline.lic";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setToast("License response file downloaded.");
  }

  return (
    <main className="gateway-shell">
      <header className="topbar">
        <div className="brand">
          <div>
            <p>OCUWELL Gateway</p>
            <span className="brand-subtitle">Offline license transfer</span>
          </div>
        </div>
      </header>

      <section className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">OCUMAPS licensing</p>
          <h1>Activate and deactivate licenses from an online gateway.</h1>
          <p>
            Use this page when the OCUMAPS workstation is offline. Bring the request here by USB
            file or camera QR, then return the gateway response to the same workstation.
          </p>
        </div>
        <div className="hero-steps" aria-label="Transfer options">
          <TransferStep icon={<Usb size={21} aria-hidden="true" />} label="USB file transfer" />
          <TransferStep icon={<Camera size={21} aria-hidden="true" />} label="Camera QR transfer" />
          <TransferStep icon={<ShieldCheck size={21} aria-hidden="true" />} label="LicenseSpring secured" />
        </div>
      </section>

      <section className="mode-toggle" aria-label="License operation">
        <ModeButton
          active={mode === "activation"}
          helper="Create the response file or response QRs"
          icon={<FileInput size={20} aria-hidden="true" />}
          label="Activation"
          onClick={() => resetFlow("activation", method)}
        />
        <ModeButton
          active={mode === "deactivation"}
          helper="Release an offline workstation license"
          icon={<RotateCcw size={20} aria-hidden="true" />}
          label="Deactivation"
          onClick={() => resetFlow("deactivation", method)}
        />
      </section>

      <section className="workspace-grid">
        <section className="panel request-panel">
          <div className="panel-heading">
            <p className="eyebrow">Request</p>
            <h2>{modeCopy.heading}</h2>
            <p>{modeCopy.helper}</p>
          </div>

          <div className="method-grid" aria-label="Request transfer method">
            <MethodButton
              active={method === "file"}
              icon={<FileUp size={18} aria-hidden="true" />}
              label="File"
              onClick={() => resetFlow(mode, "file")}
              variant="primary"
            />
            <MethodButton
              active={method === "qr"}
              icon={<QrCode size={18} aria-hidden="true" />}
              label="QR"
              onClick={() => resetFlow(mode, "qr")}
              variant="secondary"
            />
          </div>

          {method === "file" ? (
            <div className="transfer-section">
              <label className="upload-zone">
                <FileUp size={30} aria-hidden="true" />
                <strong>{requestInput?.source === "file" ? requestInput.label : "Choose request file"}</strong>
                <span>.req, .json, or .txt exported from OCUMAPS</span>
                <input
                  accept=".req,.json,.txt,application/json,text/plain"
                  type="file"
                  onChange={handleFileChange}
                />
              </label>
            </div>
          ) : (
            <div className="transfer-section">
              <QrScanner disabled={isSubmitting} onScanned={handleScannedRequest} />
            </div>
          )}

          {requestInput ? (
            <div className="ready-banner">
              <FileCheck2 size={18} aria-hidden="true" />
              <div>
                <strong>{modeCopy.ready}</strong>
                <span>{requestInput.label}</span>
              </div>
            </div>
          ) : null}

          {error ? <div className="error-banner">{error}</div> : null}

          <div className="button-row">
            <button className="secondary-button" type="button" onClick={clearRequest} disabled={isSubmitting}>
              <RefreshCw size={17} aria-hidden="true" />
              Clear
            </button>
            <button
              className="primary-button"
              disabled={isSubmitting || !requestInput}
              type="button"
              onClick={submitRequest}
            >
              {isSubmitting ? <Loader2 className="spin" size={17} aria-hidden="true" /> : null}
              {modeCopy.submit}
            </button>
          </div>
        </section>

        <ResultPanel
          downloadActivationFile={downloadActivationFile}
          result={result}
        />
      </section>

      {toast ? <div className="toast">{toast}</div> : null}
    </main>
  );
}

function TransferStep({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <div>
      {icon}
      <span>{label}</span>
    </div>
  );
}

function ModeButton({
  active,
  helper,
  icon,
  label,
  onClick,
}: {
  active: boolean;
  helper: string;
  icon: ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button className={`mode-button ${active ? "active" : ""}`} type="button" onClick={onClick}>
      <span className="mode-icon">{icon}</span>
      <span>
        <strong>{label}</strong>
        <small>{helper}</small>
      </span>
    </button>
  );
}

function MethodButton({
  active,
  icon,
  label,
  onClick,
  variant,
}: {
  active: boolean;
  icon: ReactNode;
  label: string;
  onClick: () => void;
  variant: "primary" | "secondary";
}) {
  return (
    <button
      aria-pressed={active}
      className={`method-button method-button-${variant} ${active ? "active" : ""}`}
      type="button"
      onClick={onClick}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function ResultPanel({
  downloadActivationFile,
  result,
}: {
  downloadActivationFile: (data: ActivationResponse) => void;
  result: ResultState | null;
}) {
  if (!result) {
    return (
      <aside className="panel result-panel empty-result">
        <LockKeyhole size={42} aria-hidden="true" />
        <h2>Gateway response</h2>
        <p>
          Activation responses appear here as a USB file download and ordered QR handoff. Offline
          deactivation shows a success confirmation.
        </p>
      </aside>
    );
  }

  if (result.mode === "deactivation") {
    return (
      <aside className="panel result-panel">
        <div className="result-status success">
          <CheckCircle2 size={34} aria-hidden="true" />
          <div>
            <p className="eyebrow">Complete</p>
            <h2>Deactivation processed</h2>
            <p>Request ID: {result.data.request_id || "Not supplied"}</p>
          </div>
        </div>
      </aside>
    );
  }

  return (
    <ActivationResult
      data={result.data}
      downloadActivationFile={downloadActivationFile}
    />
  );
}

function ActivationResult({
  data,
  downloadActivationFile,
}: {
  data: ActivationResponse;
  downloadActivationFile: (data: ActivationResponse) => void;
}) {
  const chunks = useMemo(() => splitQrChunks(data.license_file_content), [data.license_file_content]);
  const canShowQr =
    data.license_file_content.length <= QR_MAX_CONTENT_LENGTH && chunks.length <= QR_MAX_CHUNKS;
  const [qrImages, setQrImages] = useState<string[]>([]);
  const [qrError, setQrError] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [completedCount, setCompletedCount] = useState(0);

  useEffect(() => {
    setActiveIndex(0);
    setCompletedCount(0);
  }, [data.request_id, data.license_file_content]);

  useEffect(() => {
    let cancelled = false;
    setQrImages([]);
    setQrError("");

    if (!canShowQr) return undefined;

    Promise.all(
      chunks.map((chunk) =>
        QRCode.toDataURL(chunk, {
          errorCorrectionLevel: "M",
          margin: 1,
          width: 420,
        }),
      ),
    )
      .then((images) => {
        if (!cancelled) setQrImages(images);
      })
      .catch(() => {
        if (!cancelled) setQrError("The response QR images could not be generated.");
      });

    return () => {
      cancelled = true;
    };
  }, [canShowQr, chunks]);

  const handoffComplete = completedCount >= chunks.length && chunks.length > 0;
  const currentQrImage = qrImages[activeIndex];

  function markCurrentQrScanned() {
    const nextCompleted = Math.max(completedCount, activeIndex + 1);
    setCompletedCount(nextCompleted);

    if (activeIndex < chunks.length - 1) {
      setActiveIndex(activeIndex + 1);
    }
  }

  function resetQrHandoff() {
    setActiveIndex(0);
    setCompletedCount(0);
  }

  return (
    <aside className="panel result-panel">
      <div className="result-status success">
        <CheckCircle2 size={34} aria-hidden="true" />
        <div>
          <p className="eyebrow">Ready</p>
          <h2>Activation response generated</h2>
          <p>Request ID: {data.request_id}</p>
        </div>
      </div>

      <div className="handoff-block">
        <div className="handoff-heading">
          <Usb size={20} aria-hidden="true" />
          <div>
            <h3>Option 1: USB file transfer</h3>
            <p>Download the response file and bring it back to the OCUMAPS workstation.</p>
          </div>
        </div>
        <button className="primary-button full-width" type="button" onClick={() => downloadActivationFile(data)}>
          <Download size={17} aria-hidden="true" />
          Download {data.file_name}
        </button>
      </div>

      <div className="handoff-block">
        <div className="handoff-heading">
          <QrCode size={20} aria-hidden="true" />
          <div>
            <h3>Option 2: Camera QR transfer</h3>
            <p>Show one response QR at a time. Mark each QR as scanned before revealing the next.</p>
          </div>
        </div>

        {!canShowQr ? (
          <div className="warning-banner">
            This response is {data.license_file_content.length} characters. QR transfer supports up
            to {QR_MAX_CONTENT_LENGTH} characters, so use the response file.
          </div>
        ) : qrError ? (
          <div className="error-banner">{qrError}</div>
        ) : qrImages.length !== chunks.length ? (
          <div className="loading-row">
            <Loader2 className="spin" size={17} aria-hidden="true" />
            Generating response QRs
          </div>
        ) : (
          <div className="qr-handoff">
            <div className="qr-steps" aria-label="Response QR order">
              {chunks.map((_, index) => {
                const isComplete = index < completedCount;
                const isCurrent = index === activeIndex && !handoffComplete;
                const className = isComplete ? "complete" : isCurrent ? "active" : "locked";

                return (
                  <div className={`qr-step ${className}`} key={index}>
                    {isComplete ? <CheckCircle2 size={15} aria-hidden="true" /> : null}
                    {className === "locked" ? <LockKeyhole size={14} aria-hidden="true" /> : null}
                    <span>QR {index + 1}</span>
                  </div>
                );
              })}
            </div>

            <div className="qr-display">
              {currentQrImage ? (
                <img src={currentQrImage} alt={`Activation response QR ${activeIndex + 1}`} />
              ) : null}
              <p>
                {handoffComplete
                  ? "All response QRs are marked as scanned."
                  : `Scan QR ${activeIndex + 1} of ${chunks.length} on the OCUMAPS workstation.`}
              </p>
            </div>

            <div className="button-row qr-actions">
              <button className="secondary-button" type="button" onClick={resetQrHandoff}>
                <RefreshCw size={17} aria-hidden="true" />
                Restart QR 1
              </button>
              <button
                className="primary-button"
                disabled={handoffComplete}
                type="button"
                onClick={markCurrentQrScanned}
              >
                <CheckCircle2 size={17} aria-hidden="true" />
                Mark QR {Math.min(activeIndex + 1, chunks.length)} scanned
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

function QrScanner({
  disabled,
  onScanned,
}: {
  disabled?: boolean;
  onScanned: (value: string) => void;
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isOpening, setIsOpening] = useState(false);
  const [cameraError, setCameraError] = useState("");

  const stopCamera = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }

    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsCameraOpen(false);
  }, []);

  useEffect(() => stopCamera, [stopCamera]);

  async function startCamera() {
    setCameraError("");

    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError("Camera access is not available in this browser.");
      return;
    }

    stopCamera();
    setIsOpening(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment",
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
      });

      streamRef.current = stream;
      setIsCameraOpen(true);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      timerRef.current = window.setInterval(() => {
        const video = videoRef.current;
        const canvas = canvasRef.current;

        if (
          !video ||
          !canvas ||
          video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA ||
          video.videoWidth === 0 ||
          video.videoHeight === 0
        ) {
          return;
        }

        const context = canvas.getContext("2d", { willReadFrequently: true });
        if (!context) {
          setCameraError("Unable to read the camera preview.");
          stopCamera();
          return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        const scannedValue = decodeQrFromCanvas(context, canvas);
        if (scannedValue?.trim()) {
          stopCamera();
          onScanned(scannedValue.trim());
        }
      }, QR_SCAN_INTERVAL_MS);
    } catch (error) {
      stopCamera();
      setCameraError(getCameraErrorMessage(error));
    } finally {
      setIsOpening(false);
    }
  }

  return (
    <div className="scanner">
      <div className={`scanner-preview ${isCameraOpen ? "camera-open" : ""}`}>
        <video
          ref={videoRef}
          className={isCameraOpen ? "scanner-video" : "hidden"}
          autoPlay
          muted
          playsInline
        />
        {!isCameraOpen ? (
          <div className="scanner-placeholder">
            <Camera size={36} aria-hidden="true" />
            <strong>Scan request QR</strong>
            <span>Hold the OCUMAPS request QR inside the camera frame.</span>
          </div>
        ) : (
          <div className="scan-frame" aria-hidden="true" />
        )}
      </div>
      <canvas ref={canvasRef} className="hidden" aria-hidden="true" />

      <div className="button-row scanner-actions">
        <button className="primary-button" type="button" onClick={startCamera} disabled={disabled || isOpening || isCameraOpen}>
          {isOpening ? <Loader2 className="spin" size={17} aria-hidden="true" /> : <Camera size={17} aria-hidden="true" />}
          {isOpening ? "Opening camera" : isCameraOpen ? "Camera active" : "Allow camera"}
        </button>
        <button className="secondary-button" type="button" onClick={stopCamera} disabled={!isCameraOpen}>
          <XCircle size={17} aria-hidden="true" />
          Stop camera
        </button>
      </div>

      {cameraError ? <div className="warning-banner">{cameraError}</div> : null}
    </div>
  );
}

function buildRequestBody(rawRequest: string, mode: FlowMode): Record<string, unknown> {
  const parsed = parseJson(rawRequest);

  if (isRecord(parsed)) {
    if ("encoded_request" in parsed || "activation_request" in parsed || "deactivation_request" in parsed) {
      return parsed;
    }

    return mode === "activation" ? { activation_request: parsed } : { deactivation_request: parsed };
  }

  if (typeof parsed === "string" && parsed.trim()) {
    return { encoded_request: parsed.trim() };
  }

  return { encoded_request: rawRequest };
}

function parseJson(value: string): unknown {
  try {
    return JSON.parse(value);
  } catch {
    return undefined;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

async function readResponseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return {};

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function readErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload === "string" && payload.trim()) return payload;

  if (isRecord(payload)) {
    const detail = payload.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      return "The request format is not valid for this offline license operation.";
    }
  }

  return fallback;
}

function splitQrChunks(content: string): string[] {
  return content.match(new RegExp(`[\\s\\S]{1,${QR_CHUNK_SIZE}}`, "g")) ?? [];
}

function decodeQrFromCanvas(
  context: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
): string | null {
  const zxingResult = decodeQrWithZxing(canvas);
  if (zxingResult) return zxingResult;

  const fullFrameResult = decodeQrImageData(context.getImageData(0, 0, canvas.width, canvas.height));
  if (fullFrameResult) return fullFrameResult;

  const cropSize = Math.floor(Math.min(canvas.width, canvas.height) * 0.82);
  if (cropSize <= 0) return null;

  const cropX = Math.floor((canvas.width - cropSize) / 2);
  const cropY = Math.floor((canvas.height - cropSize) / 2);
  return decodeQrImageData(context.getImageData(cropX, cropY, cropSize, cropSize));
}

function decodeQrWithZxing(canvas: HTMLCanvasElement): string | null {
  try {
    const result = zxingQrReader.decodeFromCanvas(canvas);
    return result.getText() || null;
  } catch {
    return null;
  }
}

function decodeQrImageData(imageData: ImageData): string | null {
  try {
    return (
      jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: "attemptBoth",
      })?.data ?? null
    );
  } catch {
    return null;
  }
}

function getCameraErrorMessage(error: unknown): string {
  if (
    typeof DOMException !== "undefined" &&
    error instanceof DOMException &&
    (error.name === "NotAllowedError" || error.name === "PermissionDeniedError")
  ) {
    return "Camera permission was blocked. Allow camera access, then try again.";
  }

  return error instanceof Error ? `Unable to open camera. ${error.message}` : "Unable to open camera.";
}
