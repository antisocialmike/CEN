interface AxiosLikeError {
  response?: {
    status: number;
    data?: { detail?: unknown };
  };
}

function isAxiosLikeError(error: unknown): error is AxiosLikeError {
  return typeof error === "object" && error !== null && "response" in error;
}

export function getStatusCode(error: unknown): number | undefined {
  return isAxiosLikeError(error) ? error.response?.status : undefined;
}

export function getErrorDetail(error: unknown): string | undefined {
  const detail = isAxiosLikeError(error) ? error.response?.data?.detail : undefined;
  return typeof detail === "string" ? detail : undefined;
}

export function getValidationMessage(error: unknown): string | undefined {
  const detail = isAxiosLikeError(error) ? error.response?.data?.detail : undefined;
  if (!Array.isArray(detail) || detail.length === 0) return undefined;
  const message: unknown = (detail[0] as { msg?: unknown }).msg;
  return typeof message === "string" ? message.replace(/^Value error, /, "") : undefined;
}
