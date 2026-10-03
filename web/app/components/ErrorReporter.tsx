"use client";

import { useEffect } from "react";
import { reportError } from "@/lib/report-error";

/** Uncaught errors and rejected promises in the browser go to the admin panel. */
export function ErrorReporter() {
  useEffect(() => {
    const onError = (event: ErrorEvent) => reportError(event.message || String(event.error));
    const onRejection = (event: PromiseRejectionEvent) =>
      reportError(event.reason instanceof Error ? event.reason.message : String(event.reason));
    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onRejection);
    return () => {
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onRejection);
    };
  }, []);
  return null;
}
