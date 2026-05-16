"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Box,
  Container,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import DocumentScannerIcon from "@mui/icons-material/DocumentScanner";
import UploadForm from "./components/UploadForm";
import ImageList from "./components/ImageList";
import ImageDetail from "./components/ImageDetail";
import { listImages, ImageSummary } from "./lib/api";
import NotificationForm from "./components/NotificationForm";

export default function Home() {
  const [images, setImages] = useState<ImageSummary[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const fetchImages = useCallback(async () => {
    setLoadingList(true);
    try {
      const data = await listImages();
      setImages(data);
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => {
    fetchImages();
  }, [fetchImages]);

  function handleUploaded() {
    fetchImages();
  }

  function handleSelect(id: string) {
    setSelectedId((prev) => (prev === id ? null : id));
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={4}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <DocumentScannerIcon color="primary" fontSize="large" />
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            OCR Web App
          </Typography>
        </Box>

        <Box
          sx={{
            display: "flex",
            flexDirection: { xs: "column", md: "row" },
            gap: 3,
            alignItems: "flex-start",
          }}
        >
          <Box
            sx={{ display: "flex", flexDirection: "column", gap: 3, width: { xs: "100%", md: 320 } }}
          >
            <Paper variant="outlined" sx={{ p: 3, minWidth: 280, width: { xs: "100%", md: 320 } }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Upload image
              </Typography>
              <UploadForm onUploaded={handleUploaded} />
            </Paper>

            <Paper variant="outlined" sx={{ p: 3, minWidth: 280, width: { xs: "100%", md: 320 } }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Subscribe to notifications
              </Typography>
              <NotificationForm onUploaded={handleUploaded} />
            </Paper>

          </Box>

          <Box sx={{ flex: 1, width: "100%" }}>
            {selectedId ? (
              <Paper variant="outlined" sx={{ p: 3 }}>
                <ImageDetail
                  id={selectedId}
                  onClose={() => setSelectedId(null)}
                />
              </Paper>
            ) : (
              <Stack spacing={2}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Uploaded images
                </Typography>
                <ImageList
                  images={images}
                  loading={loadingList}
                  selectedId={selectedId}
                  onSelect={handleSelect}
                />
              </Stack>
            )}
          </Box>
        </Box>
      </Stack>
    </Container>
  );
}
