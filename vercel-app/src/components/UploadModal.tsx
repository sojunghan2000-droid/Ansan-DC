"use client";

import { useEffect, useRef, useState } from "react";
import type { Member } from "@/lib/types";

interface Props {
  open: boolean;
  onClose: () => void;
  onApply: (members: Member[], warnings: string[]) => void;
}

export function UploadModal({ open, onClose, onApply }: Props) {
  const [chkFile, setChkFile] = useState<File | null>(null);
  const [gridFile, setGridFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) {
      setChkFile(null);
      setGridFile(null);
      setBusy(false);
      setErrorMsg(null);
    }
  }, [open]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && open && !busy) onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, busy, onClose]);

  if (!open) return null;

  async function handleApply() {
    if (!chkFile) {
      setErrorMsg("CHK LIST 엑셀(필수)을 선택해 주세요.");
      return;
    }
    setBusy(true);
    setErrorMsg(null);
    try {
      const { parseExcels } = await import("@/lib/xlsxParser");
      const { members, warnings } = await parseExcels(chkFile, gridFile);
      if (members.length === 0) {
        setErrorMsg(
          "CHK LIST 시트에서 부재를 찾지 못했습니다. 표준 양식(시트명 'CHK LIST', R8부터 데이터)인지 확인해주세요.",
        );
        setBusy(false);
        return;
      }
      onApply(members, warnings);
      onClose();
    } catch (err) {
      console.error(err);
      setErrorMsg(
        err instanceof Error
          ? `파싱 실패: ${err.message}`
          : "엑셀 파일 파싱 중 오류가 발생했습니다.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="엑셀 데이터 업로드"
        className="modal-card"
      >
        <div className="modal-header">
          <h2>📁 엑셀 데이터 업로드</h2>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            disabled={busy}
            aria-label="닫기"
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <p className="modal-desc">
            입결 데이터 표준 양식(시트명 <code>CHK LIST</code>, R8부터 데이터)을 따르는 두 엑셀을
            업로드하면 즉시 대시보드가 갱신됩니다. 파일은 브라우저에서만 처리되며 서버로 전송되지
            않습니다.
          </p>

          <div className="upload-row">
            <label className="upload-label">
              <span>① CHK LIST 엑셀 <em className="req">(필수)</em></span>
              <input
                type="file"
                accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                disabled={busy}
                onChange={(e) => {
                  setChkFile(e.target.files?.[0] ?? null);
                  setErrorMsg(null);
                }}
              />
              {chkFile && (
                <span className="upload-meta">
                  ✓ {chkFile.name} ({(chkFile.size / 1024).toFixed(0)} KB)
                </span>
              )}
            </label>
          </div>

          <div className="upload-row">
            <label className="upload-label">
              <span>② 그리드 마스터 엑셀 <em className="opt">(선택)</em></span>
              <input
                type="file"
                accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                disabled={busy}
                onChange={(e) => {
                  setGridFile(e.target.files?.[0] ?? null);
                  setErrorMsg(null);
                }}
              />
              {gridFile && (
                <span className="upload-meta">
                  ✓ {gridFile.name} ({(gridFile.size / 1024).toFixed(0)} KB)
                </span>
              )}
              {!gridFile && (
                <span className="upload-hint">
                  비워두면 모든 GRID가 &lsquo;(미지정)&rsquo;으로 처리됩니다.
                </span>
              )}
            </label>
          </div>

          {errorMsg && <div className="upload-error">⚠ {errorMsg}</div>}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onClose} disabled={busy}>
            취소
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={handleApply}
            disabled={busy || !chkFile}
          >
            {busy ? "파싱 중…" : "적용"}
          </button>
        </div>
      </div>
    </div>
  );
}
