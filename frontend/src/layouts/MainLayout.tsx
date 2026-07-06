import { Box } from "@mui/material";
import { Outlet } from "react-router-dom";
import Header from "./Header";
import Sidebar, { DRAWER_WIDTH } from "./Sidebar";
import Footer from "./Footer";

export default function MainLayout() {
  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <Header />
      <Sidebar />
      <Box sx={{ flexGrow: 1, display: "flex", flexDirection: "column", ml: `${DRAWER_WIDTH}px` }}>
        <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
          <Outlet />
        </Box>
        <Footer />
      </Box>
    </Box>
  );
}
