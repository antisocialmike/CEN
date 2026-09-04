interface AxiosLikeError {
  response?: {
    status: number;
    data?: { detail?: string };
  };
}

function isAxiosLikeError(error: unknown): error is AxiosLikeError {
  return typeof error === "object" && error !== null && "response" in error;
}

export function getStatusCode(error: unknown): number | undefined {
  return isAxiosLikeError(error) ? error.response?.status : undefined;
}

export function getErrorDetail(error: unknown, fallback: string): string {
  if (isAxiosLikeError(error) && error.response?.data?.detail) {
    return error.response.data.detail;
  }
  return fallback;
}
