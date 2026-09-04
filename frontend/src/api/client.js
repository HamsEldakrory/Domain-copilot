import axios from "axios";
import { store } from "../store";
import { setTokens, logout } from "../store/authSlice";
import { getApiBaseUrl } from "./config";

const client = axios.create({
  baseURL: getApiBaseUrl(),
});

client.interceptors.request.use((config) => {
  const token = store.getState().auth.access;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const refresh = store.getState().auth.refresh;

    if (
      error.response?.status === 401 &&
      refresh &&
      !originalRequest._retried
    ) {
      originalRequest._retried = true;

      try {
        const response = await axios.post(
          `${getApiBaseUrl()}/auth/jwt/refresh/`,
          { refresh },
        );
        const newAccess = response.data.access;
        store.dispatch(
          setTokens({
            access: newAccess,
            refresh,
          }),
        );

        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return client(originalRequest);
      } catch (refreshError) {
        store.dispatch(logout());
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  },
);

export default client;
