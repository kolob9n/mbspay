import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    primary: { main: "#1565c0", light: "#5e92f3", dark: "#003c8f" },
    secondary: { main: "#ff6f00", light: "#ffa040", dark: "#c43e00" },
    background: { default: "#f5f5f5", paper: "#ffffff" },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: { fontWeight: 600 }, h5: { fontWeight: 600 }, h6: { fontWeight: 600 },
  },
  shape: { borderRadius: 8 },
  components: {
    MuiButton: { styleOverrides: { root: { textTransform: "none", fontWeight: 500 } } },
    MuiTableCell: { styleOverrides: { head: { fontWeight: 600 } } },
  },
});

export default theme;
