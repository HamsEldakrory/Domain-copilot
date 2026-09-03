import { createSlice } from "@reduxjs/toolkit";

const authSlice = createSlice({
  name: "auth",
  initialState: {
    access: localStorage.getItem("access") || null,
    refresh: localStorage.getItem("refresh") || null,
    user: null,
  },
  reducers: {
    setTokens: (state, action) => {
      state.access = action.payload.access;
      state.refresh = action.payload.refresh;

      localStorage.setItem("access", action.payload.access);
      localStorage.setItem("refresh", action.payload.refresh);
    },

    setUser: (state, action) => {
      state.user = action.payload;
    },

    logout: (state) => {
      state.access = null;
      state.refresh = null;
      state.user = null;

      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
    },
  },
});

export const { setTokens, setUser, logout } = authSlice.actions;

export default authSlice.reducer;
