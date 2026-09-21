"use client";

import { useState } from "react";

export function useCodeReview() {
  const [submittedCode, setSubmittedCode] = useState<string | null>(null);

  return { submittedCode, submit: setSubmittedCode };
}
