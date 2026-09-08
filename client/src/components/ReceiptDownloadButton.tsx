import { useState } from "react";
import { DownloadSimple } from "@phosphor-icons/react";
import { downloadReceipt } from "../services/payrollService";

interface ReceiptDownloadButtonProps {
  receiptId: number;
  label?: string;
}

export default function ReceiptDownloadButton({
  receiptId,
  label = "Descargar comprobante"
}: ReceiptDownloadButtonProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [hasFailed, setHasFailed] = useState(false);

  async function handleDownload() {
    setHasFailed(false);
    setIsDownloading(true);

    try {
      await downloadReceipt(receiptId);
    } catch {
      setHasFailed(true);
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <>
      <button
        className="btn btn-line receipt-card-download"
        onClick={handleDownload}
        disabled={isDownloading}
      >
        <DownloadSimple weight="bold" />
        {isDownloading ? "Preparando…" : label}
      </button>
      {hasFailed && (
        <span className="receipt-card-download-error" role="alert">
          No se pudo descargar. Inténtalo de nuevo.
        </span>
      )}
    </>
  );
}
