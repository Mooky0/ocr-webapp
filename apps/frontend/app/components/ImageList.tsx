"use client";

import {
  Box,
  Card,
  CardActionArea,
  CardMedia,
  CardContent,
  CircularProgress,
  Grid,
  Tooltip,
  Typography,
} from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import HourglassEmptyIcon from "@mui/icons-material/HourglassEmpty";
import { ImageSummary, imageFileUrl } from "../lib/api";

function OcrStatusIcon({ status }: { status: ImageSummary["ocr_status"] }) {
  if (status === "completed")
    return (
      <Tooltip title="OCR complete">
        <CheckCircleIcon fontSize="small" color="success" />
      </Tooltip>
    );
  if (status === "failed")
    return (
      <Tooltip title="OCR failed">
        <ErrorIcon fontSize="small" color="error" />
      </Tooltip>
    );
  return (
    <Tooltip title={status === "processing" ? "Processing…" : "Pending"}>
      <HourglassEmptyIcon fontSize="small" color="disabled" />
    </Tooltip>
  );
}

interface Props {
  images: ImageSummary[];
  loading: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function ImageList({ images, loading, selectedId, onSelect }: Props) {
  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (images.length === 0) {
    return (
      <Typography sx={{ color: "text.secondary", textAlign: "center", py: 4 }}>
        No images yet. Upload one to get started.
      </Typography>
    );
  }

  return (
    <Grid container spacing={2}>
      {images.map((img) => (
        <Grid key={img.id} size={{ xs: 6, sm: 4, md: 3 }}>
          <Card
            variant="outlined"
            sx={{
              outline: selectedId === img.id ? "2px solid" : "none",
              outlineColor: "primary.main",
            }}
          >
            <CardActionArea onClick={() => onSelect(img.id)}>
              <CardMedia
                component="img"
                height={120}
                image={imageFileUrl(img.id)}
                alt={img.filename}
                sx={{ objectFit: "cover" }}
              />
              <CardContent sx={{ py: 1, px: 1.5 }}>
                <Typography variant="caption" sx={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {img.description}
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mt: 1 }}>
                  <OcrStatusIcon status={img.ocr_status} />
                  <Typography variant="body2" sx={{ color: "text.secondary", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {img.filename}
                  </Typography>
                </Box>
              </CardContent>
            </CardActionArea>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}
