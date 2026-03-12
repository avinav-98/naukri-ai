const defaultHeaders = {
  Accept: "application/json",
};

function toFormData(data) {
  if (data instanceof FormData) {
    return data;
  }
  const formData = new FormData();
  Object.entries(data || {}).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return;
    }
    if (Array.isArray(value)) {
      value.forEach((item) => formData.append(key, item));
      return;
    }
    formData.append(key, value);
  });
  return formData;
}

export async function apiRequest(path, options = {}) {
  const requestOptions = {
    method: "GET",
    credentials: "include",
    headers: { ...defaultHeaders, ...(options.headers || {}) },
    ...options,
  };

  if (options.form) {
    requestOptions.body = toFormData(options.form);
    delete requestOptions.headers["Content-Type"];
  } else if (options.json) {
    requestOptions.body = JSON.stringify(options.json);
    requestOptions.headers["Content-Type"] = "application/json";
  }

  const response = await fetch(path, requestOptions);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message = typeof payload === "string" ? payload : payload?.error || payload?.message || "Request failed";
    const error = new Error(message);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

export const sessionApi = {
  getSession: () => apiRequest("/api/session"),
  login: (form) => apiRequest("/api/session/login", { method: "POST", form }),
  signup: (form) => apiRequest("/api/session/signup", { method: "POST", form }),
  logout: () => apiRequest("/api/session/logout", { method: "POST" }),
  forgotPassword: (form) => apiRequest("/api/session/forgot-password", { method: "POST", form }),
  resetPassword: (token, form) => apiRequest(`/api/session/reset-password/${token}`, { method: "POST", form }),
};
